#!/usr/bin/env python3
"""
Agent de préparation des payloads BadUSB — semi-interactif, assisté par Ollama.

Rôle: préparer les scripts classés (voir classify_badusb.py) avant que
l'utilisateur les copie lui-même sur la carte SD du Flipper Zero (dans
badusb/). Ce script ne touche jamais la carte SD directement.

Pour chaque script :
  1. Détection déterministe (regex) des champs à personnaliser — webhook
     Discord, bot/chat Telegram, IP/port d'attaquant, email, placeholders
     entre crochets ([person], [text]...), clé API. Voir FIELD_SPECS.
  2. Si rien n'est détecté par regex, fallback optionnel: on demande à un
     modèle Ollama (tool-calling, jamais de texte libre parsé à l'aveugle —
     même philosophie que Bad_USB_Classifier/ollama_agent.py) s'il repère un
     champ à configurer. Toute valeur renvoyée par le modèle est revérifiée
     verbatim dans le fichier avant d'être utilisée: pas de remplacement à
     l'aveugle.
  3. Les scripts sans aucun champ détecté sont copiés tels quels (aucune
     action requise — "plug and play").
  4. Pour les scripts avec champs détectés, l'utilisateur est interrogé une
     fois par type de champ (valeur globale réutilisée) ou fichier par
     fichier selon son choix — voir collect_field_values().

Voir SETUP_METHODS.md (généré par --write-methods-doc) pour le détail de la
méthode retenue par thème de classification.
"""
from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Bad_USB_Classifier.ollama_agent import (
    DEFAULT_MODEL,
    OllamaUnavailable,
    chat_with_tools,
)

logger = logging.getLogger(__name__)

DUCKY_EXTENSIONS = {".txt", ".duck", ".ds"}
SKIP_FILENAMES = {"readme.md", "license", "license.md", "classification.log"}


# ─── Méthode par thème (documentation + biais de détection) ─────────────────
# "needs" liste les clés de FIELD_SPECS attendues le plus souvent pour ce
# thème — sert uniquement à documenter/prioriser, la détection regex tourne
# de toute façon sur TOUS les fichiers quel que soit le thème.

THEME_METHODS: dict[str, dict] = {
    "exfiltration": {
        "needs": ["discord_webhook", "telegram_bot_token", "telegram_chat_id"],
        "note": "Envoie des données collectées vers un service externe : il faut presque toujours fournir une destination (webhook Discord ou bot Telegram).",
    },
    "credentials": {
        "needs": ["discord_webhook"],
        "note": "Vole/exfiltre des identifiants — nécessite une destination pour recevoir les résultats.",
    },
    "PassVault": {
        "needs": ["discord_webhook"],
        "note": "Variante exfiltration ciblant les gestionnaires de mots de passe/navigateurs.",
    },
    "Mimikatz": {
        "needs": [],
        "note": "Exécution locale (dump credentials en local) — souvent plug & play, vérifier quand même une destination d'exfiltration.",
    },
    "Telegram": {
        "needs": ["telegram_bot_token", "telegram_chat_id"],
        "note": "Utilise l'API Telegram — nécessite un bot token + chat id.",
    },
    "web2Discord": {
        "needs": ["discord_webhook"],
        "note": "Exfiltration web -> Discord.",
    },
    "ReverseShell": {
        "needs": ["attacker_ip", "attacker_port"],
        "note": "Ouvre un shell vers l'attaquant — nécessite IP + port d'écoute.",
    },
    "remote_access": {
        "needs": ["attacker_ip", "attacker_port"],
        "note": "Accès distant — souvent plug & play (ex: reboot), parfois IP/port si reverse shell.",
    },
    "execution": {
        "needs": ["attacker_ip", "attacker_port"],
        "note": "Exécution générique — variable, dépend du payload (certains téléchargent un script tiers sans configuration).",
    },
    "phishing": {
        "needs": ["discord_webhook", "generic_url"],
        "note": "Pages/liens de phishing ou exfiltration de saisies — vérifier URL/webhook.",
    },
    "iMessageExfil": {
        "needs": ["bracket_placeholder"],
        "note": "Cible un contact/texte précis — remplacer [person]/[text] par les vraies valeurs avant usage.",
    },
    "CartmanSong": {"needs": [], "note": "Prank audio/visuel — plug & play."},
    "prank": {
        "needs": [],
        "note": "Farces sans exfiltration — plug & play dans l'immense majorité des cas.",
    },
    "quackberry": {
        "needs": [],
        "note": "Explicitement documenté par les auteurs comme plug & play.",
    },
    "destructive": {
        "needs": [],
        "note": "Actions destructrices locales — pas de destination réseau en général.",
    },
    "ransom": {
        "needs": [],
        "note": "Simulations de ransomware — locales, pas de C2 réel dans ces échantillons.",
    },
    "recon": {
        "needs": ["generic_url"],
        "note": "Collecte d'infos — certains scripts de scraping ont une URL cible à adapter.",
    },
    "incident_response": {
        "needs": [],
        "note": "Scripts défensifs (triage/forensic) — plug & play, aucune exfiltration attendue.",
    },
    "mobile": {"needs": [], "note": "Cible Android/iOS — généralement plug & play."},
    "general": {
        "needs": ["discord_webhook", "attacker_ip", "generic_url"],
        "note": "Fourre-tout — comportement variable, laisser la détection générique trancher.",
    },
    "unassigned": {
        "needs": [],
        "note": "Non catégorisé par le classifieur — à relire manuellement, la détection auto peut être incomplète.",
    },
}


# ─── Détection déterministe des champs à personnaliser ──────────────────────


@dataclass
class FieldSpec:
    key: str
    label: str
    example: str
    pattern: re.Pattern
    # group(1) du pattern = la sous-chaîne exacte à remplacer dans le fichier


FIELD_SPECS: list[FieldSpec] = [
    FieldSpec(
        key="discord_webhook",
        label="URL du webhook Discord",
        example="DISCORD_HOOK_URL",
        pattern=re.compile(r'(?i)\$?\bwebhook(?:_?url)?\b\s*=\s*["\']([^"\']*)["\']'),
    ),
    FieldSpec(
        key="telegram_bot_token",
        label="Bot token Telegram",
        example="123456789:AAExampleTokenExampleTokenExample",
        pattern=re.compile(r'(?i)\$?\bbot_?token\b\s*=\s*["\']([^"\']*)["\']'),
    ),
    FieldSpec(
        key="telegram_chat_id",
        label="Chat ID Telegram",
        example="123456789",
        pattern=re.compile(r'(?i)\$?\bchat_?id\b\s*=\s*["\']([^"\']*)["\']'),
    ),
    FieldSpec(
        key="attacker_ip",
        label="IP de l'attaquant (LHOST)",
        example="192.168.1.42",
        pattern=re.compile(
            r"\b(LHOST|ATTACKER[_-]?IP|YOUR[_-]?IP|IP[_-]?ADDRESS)\b"
            r'(?:\s*=\s*["\']?([^"\'\s\n]*)["\']?)?'
        ),
    ),
    FieldSpec(
        key="attacker_port",
        label="Port d'écoute de l'attaquant (LPORT)",
        example="4444",
        pattern=re.compile(r'\b(LPORT|ATTACKER[_-]?PORT)\b\s*=?\s*["\']?(\d*)["\']?'),
    ),
    FieldSpec(
        key="email",
        label="Adresse email",
        example="toi@example.com",
        pattern=re.compile(
            r'(?i)\$?\b(?:your_?email|email)\b\s*=\s*["\']([^"\']*)["\']'
        ),
    ),
    FieldSpec(
        key="generic_url",
        label="URL cible",
        example="https://ton-site-ou-cible.example",
        pattern=re.compile(r'(https?://(?:www\.)?example\.com[^\s"\']*)'),
    ),
    FieldSpec(
        key="bracket_placeholder",
        label="Valeur à remplacer (placeholder entre crochets)",
        example="(dépend du script — nom, message, etc.)",
        pattern=re.compile(r"(\[[a-zA-Z_][a-zA-Z0-9_ ]{1,30}\])"),
    ),
    FieldSpec(
        key="api_key",
        label="Clé API",
        example="sk-...",
        pattern=re.compile(r'(?i)\$?\bapi_?key\b\s*=\s*["\']([^"\']*)["\']'),
    ),
]

# bracket_placeholder est le pattern le plus susceptible de faux positifs
# (types PowerShell comme [Math]/[int]/[ref], sections ini [Unit]/[Service],
# prompts factices [sudo]...). On ne retient que les crochets qui suivent la
# convention de placeholder communautaire: TOUT_EN_MAJUSCULES_AVEC_UNDERSCORE
# (EVIL_SERVER_IP, LISTENER_IP_ADDRESS...) ou un mot-clé usuel de la liste
# ci-dessous (basé sur l'inventaire réel des payloads classifiés).
BRACKET_KNOWN_WORDS = {
    "person",
    "text",
    "name",
    "target",
    "message",
    "url",
    "ip",
    "contact",
    "email",
    "phone",
    "victim",
    "username",
    "password",
    "recipient",
    "subject",
    "body",
    "filename",
    "address",
    "port",
}
_ALL_CAPS_UNDERSCORE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")


def _is_probable_placeholder(bracket_content: str) -> bool:
    word = bracket_content.strip()
    if _ALL_CAPS_UNDERSCORE.match(word):
        return True
    return word.lower() in BRACKET_KNOWN_WORDS


@dataclass
class FieldMatch:
    spec: FieldSpec
    line_no: int
    raw_line: str
    placeholder: str  # sous-chaîne exacte à remplacer, peut être vide


def scan_file(content: str) -> list[FieldMatch]:
    matches: list[FieldMatch] = []
    seen_placeholders: set[tuple[str, str]] = set()
    lines = content.splitlines()

    for spec in FIELD_SPECS:
        for m in spec.pattern.finditer(content):
            placeholder = (
                next((g for g in reversed(m.groups()) if g is not None), "")
                if m.groups()
                else ""
            )
            if spec.key == "bracket_placeholder" and not _is_probable_placeholder(
                placeholder.strip("[]")
            ):
                continue
            key = (spec.key, placeholder)
            if key in seen_placeholders:
                continue
            seen_placeholders.add(key)
            line_no = content.count("\n", 0, m.start()) + 1
            raw_line = (
                lines[line_no - 1] if 0 <= line_no - 1 < len(lines) else m.group(0)
            )
            matches.append(
                FieldMatch(
                    spec=spec,
                    line_no=line_no,
                    raw_line=raw_line.strip(),
                    placeholder=placeholder,
                )
            )

    return matches


def is_valid_ducky(content: str) -> bool:
    keywords = ("STRING", "DELAY", "ENTER", "REM", "GUI", "ALT", "CTRL", "SHIFT")
    return any(
        line.lstrip().upper().startswith(keywords) for line in content.splitlines()
    )


# ─── Fallback Ollama pour les fichiers sans match regex ─────────────────────

REPORT_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "report_fields_needed",
            "description": "Signale les champs que l'utilisateur doit personnaliser dans ce script avant usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "description": "Ce que représente la valeur (ex: 'adresse IP cible')",
                                },
                                "exact_substring": {
                                    "type": "string",
                                    "description": "La sous-chaîne EXACTE présente dans le script à remplacer (copier-coller verbatim).",
                                },
                            },
                            "required": ["label", "exact_substring"],
                        },
                    },
                    "plug_and_play": {
                        "type": "boolean",
                        "description": "true si le script ne nécessite aucune configuration.",
                    },
                },
                "required": ["plug_and_play"],
            },
        },
    }
]


def ollama_fallback_scan(content: str, filename: str, model: str) -> list[FieldMatch]:
    """Dernier recours pour les fichiers où la regex n'a rien trouvé. Toute
    sous-chaîne suggérée par le modèle est revérifiée verbatim dans le
    fichier avant d'être acceptée — le modèle ne modifie jamais rien
    directement, il ne fait que suggérer (tool call structuré)."""
    found: list[FieldMatch] = []

    def on_tool_call(name: str, args: dict) -> str:
        if name != "report_fields_needed":
            return "Tool inconnu."
        for f in args.get("fields", []):
            substring = (f.get("exact_substring") or "").strip()
            label = f.get("label") or "Valeur à personnaliser"
            if substring and substring in content:
                line_no = content.count("\n", 0, content.index(substring)) + 1
                spec = FieldSpec(
                    key="ollama_suggested",
                    label=label,
                    example="",
                    pattern=re.compile(re.escape(substring)),
                )
                found.append(
                    FieldMatch(
                        spec=spec,
                        line_no=line_no,
                        raw_line=substring,
                        placeholder=substring,
                    )
                )
            else:
                logger.debug(
                    "Suggestion Ollama ignorée (introuvable verbatim): %r", substring
                )
        return f"{len(found)} champ(s) retenu(s)."

    system_prompt = (
        "Tu analyses un Ducky Script (payload BadUSB) pour repérer si l'utilisateur "
        "doit y personnaliser une valeur avant de l'utiliser (IP, email, URL, nom, "
        "token, etc.). Réponds UNIQUEMENT via l'appel de l'outil report_fields_needed. "
        "N'invente rien : exact_substring doit être copié tel quel depuis le script."
    )
    try:
        chat_with_tools(
            model,
            system_prompt,
            f"Fichier: {filename}\n\n{content[:4000]}",
            tools=REPORT_TOOL_SCHEMA,
            on_tool_call=on_tool_call,
        )
    except OllamaUnavailable as e:
        logger.warning("Ollama indisponible pour %s: %s", filename, e)
    except Exception as e:  # noqa: BLE001 - un échec IA ne doit jamais bloquer le run
        logger.warning("Analyse Ollama échouée pour %s: %s", filename, e)
    return found


# ─── Collecte interactive des valeurs ────────────────────────────────────────


@dataclass
class SetupPlan:
    ready: list[Path] = field(default_factory=list)  # aucune config nécessaire
    to_configure: dict[Path, list[FieldMatch]] = field(default_factory=dict)
    skipped: list[Path] = field(default_factory=list)


def analyze_tree(root: Path, use_ollama: bool, model: str) -> SetupPlan:
    plan = SetupPlan()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.lower() in SKIP_FILENAMES:
            continue
        if path.suffix.lower() not in DUCKY_EXTENSIONS:
            plan.skipped.append(path)
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if not content.strip() or not is_valid_ducky(content):
            plan.skipped.append(path)
            continue

        matches = scan_file(content)
        if not matches and use_ollama:
            matches = ollama_fallback_scan(content, path.name, model)

        if not matches:
            plan.ready.append(path)
        else:
            plan.to_configure[path] = matches
    return plan


def print_summary(plan: SetupPlan) -> None:
    print("\n=== Résumé de l'analyse ===")
    print(f"  Prêts à l'emploi (aucune config)   : {len(plan.ready)}")
    print(f"  À configurer                        : {len(plan.to_configure)}")
    print(f"  Ignorés (pas des scripts BadUSB)    : {len(plan.skipped)}")

    per_field: dict[str, int] = {}
    for matches in plan.to_configure.values():
        for m in matches:
            per_field[m.spec.key] = per_field.get(m.spec.key, 0) + 1
    if per_field:
        print("\n  Détail par type de champ :")
        for key, count in sorted(per_field.items(), key=lambda kv: -kv[1]):
            print(f"    - {key:<22} {count} fichier(s)")


# ─── Setup Discord depuis zéro (compte tout juste créé) ─────────────────────
# Couvre toute la chaîne: compte -> serveur -> salon -> webhook. Déclenché
# quand l'utilisateur indique ne pas encore avoir de webhook prêt.

DISCORD_WEBHOOK_GUIDE = """
    Pas encore de webhook Discord ? Voici la marche à suivre en partant d'un
    compte tout juste créé :

      1. Compte      : va sur https://discord.com et crée un compte (ou
                        connecte-toi si c'est déjà fait).
      2. Serveur      : clique sur le "+" en bas de la barre de serveurs à
                        gauche -> "Créer un serveur" -> "Pour moi et mes amis"
                        (nom au choix, ex: "BadUSB-Tests"). Un serveur privé
                        suffit, inutile de le rendre public.
      3. Salon        : un salon texte par défaut existe (#général) — tu
                        peux l'utiliser tel quel, ou en créer un dédié
                        (clic droit sur la catégorie -> Créer un salon).
      4. Webhook      : clique sur la roue crantée à côté du salon
                        (Paramètres du salon) -> Intégrations -> Webhooks
                        -> "Nouveau webhook".
      5. Récupération : donne-lui un nom, vérifie le salon de destination,
                        puis clique sur "Copier l'URL du webhook".

    L'URL copiée ressemble à :
      DISCORD_HOOK_URL
"""

DISCORD_WEBHOOK_RE = re.compile(
    r"^https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/\d+/[\w-]+/?$"
)


def _ask_discord_webhook_value(prompt_text: str) -> str:
    """Demande une URL de webhook Discord, propose le guide de création si
    l'utilisateur n'en a pas encore, et valide le format avant de l'accepter.
    """
    ready = input("    As-tu déjà un webhook Discord prêt ? [O/n] ").strip().lower()
    if ready == "n":
        print(DISCORD_WEBHOOK_GUIDE)
        input("    Appuie sur Entrée une fois le webhook créé et son URL copiée...")

    while True:
        val = input(prompt_text).strip()
        if not val:
            return ""
        if DISCORD_WEBHOOK_RE.match(val):
            return val
        print(
            "    ! Ça ne ressemble pas à une URL de webhook Discord valide "
            "(attendu: https://discord.com/api/webhooks/<id>/<token>)."
        )
        if input("    Réessayer ? [O/n] ").strip().lower() == "n":
            return ""


def collect_field_values(plan: SetupPlan) -> dict[str, dict[Path, str]]:
    """Pour chaque type de champ rencontré, demande à l'utilisateur une
    valeur globale (réutilisée partout) ou du cas par cas. Retourne
    {field_key: {file_path: value}}.
    """
    values: dict[str, dict[Path, str]] = {}

    fields_by_key: dict[str, list[tuple[Path, FieldMatch]]] = {}
    for path, matches in plan.to_configure.items():
        for m in matches:
            fields_by_key.setdefault(m.spec.key, []).append((path, m))

    for key, occurrences in fields_by_key.items():
        spec = occurrences[0][1].spec
        print(f"\n--- {spec.label} ({len(occurrences)} fichier(s)) ---")
        if spec.example:
            print(f"    Exemple: {spec.example}")
        mode = (
            input(
                "    [g] valeur unique pour tous ces fichiers / [f] au cas par cas / [s] ignorer ce champ : "
            )
            .strip()
            .lower()
        )

        values[key] = {}
        if mode == "s":
            continue
        if mode == "g":
            if key == "discord_webhook":
                val = _ask_discord_webhook_value(f"    Valeur pour '{spec.label}' : ")
            else:
                val = input(f"    Valeur pour '{spec.label}' : ").strip()
            for path, _m in occurrences:
                values[key][path] = val
        else:
            for path, m in occurrences:
                print(f"      {path.name} — ligne {m.line_no}: {m.raw_line[:100]}")
                prompt = f"      Valeur pour '{spec.label}' (Entrée pour ignorer) : "
                val = (
                    _ask_discord_webhook_value(prompt)
                    if key == "discord_webhook"
                    else input(prompt).strip()
                )
                if val:
                    values[key][path] = val

    return values


# ─── Application des valeurs + copie vers ready_to_flash/ ───────────────────
#
# root == output_root est un mode valide ("enrichissement en place"): utilisé
# par badusb_pipeline.py pour finaliser le dossier déjà produit par le
# classifieur, sans créer une 3e copie (raw -> classified -> ready_to_flash).
# root != output_root reproduit le comportement historique de ce module
# (copie depuis un dossier déjà classé vers un dossier ready_to_flash séparé).


def apply_and_copy(
    root: Path, output_root: Path, plan: SetupPlan, values: dict[str, dict[Path, str]]
) -> list[str]:
    report_lines: list[str] = ["# Rapport de préparation des payloads\n"]
    in_place = output_root.resolve() == root.resolve()

    for path in plan.ready:
        if not in_place:
            dest = output_root / path.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        report_lines.append(f"- OK  (plug & play)     {path.relative_to(root)}")

    for path, matches in plan.to_configure.items():
        content = path.read_text(encoding="utf-8", errors="ignore")
        applied: list[str] = []
        pending: list[str] = []

        for m in matches:
            new_val = values.get(m.spec.key, {}).get(path)
            if not new_val:
                pending.append(m.spec.label)
                continue
            if m.placeholder:
                content = content.replace(m.placeholder, new_val)
            else:
                content = content.replace(m.raw_line, f"{m.raw_line}{new_val}")
            applied.append(f"{m.spec.label} -> {new_val}")

        dest = output_root / path.relative_to(root)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

        rel = path.relative_to(root)
        if pending:
            report_lines.append(
                f"- REVOIR  {rel}  (non renseigné: {', '.join(pending)})"
            )
        else:
            report_lines.append(f"- CONFIG  {rel}  ({'; '.join(applied)})")

    return report_lines


def write_methods_doc(dest: Path) -> None:
    lines = [
        "# Méthode de configuration par thème\n",
        "Généré par payload_setup_agent.py — détail de ce qu'attend chaque",
        "catégorie de payload avant copie sur le Flipper Zero.\n",
    ]
    for theme, info in THEME_METHODS.items():
        needs = ", ".join(info["needs"]) if info["needs"] else "aucune (plug & play)"
        lines.append(f"## {theme}\n\n- Champs attendus : {needs}\n- {info['note']}\n")
    dest.write_text("\n".join(lines), encoding="utf-8")
    print(f"Méthodes écrites dans {dest}")


# ─── CLI ──────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prépare les payloads BadUSB avant copie sur le Flipper Zero."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        help="Dossier classifié à analyser (ex: ~/Desktop/classified_badusb)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Dossier de sortie (défaut: <directory>_ready_to_flash à côté)",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-1.5b-heretic:latest",
        help="Modèle Ollama pour le fallback (tool-calling requis)",
    )
    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Désactive le fallback IA, regex uniquement",
    )
    parser.add_argument(
        "--write-methods-doc", metavar="FILE", help="Écrit SETUP_METHODS.md et quitte"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.write_methods_doc:
        write_methods_doc(Path(args.write_methods_doc))
        return 0

    if not args.directory:
        parser.print_help()
        return 1

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"Erreur: {root} n'est pas un dossier valide.")
        return 1

    output_root = (
        Path(args.output).expanduser().resolve()
        if args.output
        else root.parent / f"{root.name}_ready_to_flash"
    )

    print(f"Analyse de {root} ...")
    plan = analyze_tree(root, use_ollama=not args.no_ollama, model=args.model)
    print_summary(plan)

    if not plan.to_configure:
        print("\nAucun fichier à configurer — copie directe.")
    else:
        proceed = (
            input("\nContinuer et configurer ces fichiers ? [O/n] ").strip().lower()
        )
        if proceed == "n":
            print("Annulé.")
            return 0

    values = collect_field_values(plan) if plan.to_configure else {}

    if output_root.exists():
        confirm = (
            input(f"{output_root} existe déjà, l'écraser ? [o/N] ").strip().lower()
        )
        if confirm != "o":
            print("Annulé.")
            return 0
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    report_lines = apply_and_copy(root, output_root, plan, values)
    report_path = output_root / "setup_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"\nTerminé. Fichiers prêts dans: {output_root}")
    print(f"Rapport détaillé: {report_path}")
    print(
        "\nIl ne reste plus qu'à copier manuellement ce dossier dans badusb/ sur la carte SD du Flipper Zero."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
