#!/usr/bin/env python3
"""
Auto-Flipper-Tools GUI — interface web locale à 3 colonnes.

Colonne 1 (source)   : glisser un dossier, ou cloner un dépôt via URL.
Colonne 2 (organized) : résultat de la classification (thème par thème).
Colonne 3 (ready)     : résultat de l'enrichissement (webhooks/IP/tokens
                        injectés), prêt à copier sur la carte SD du Flipper.

Application locale mono-utilisateur (pas d'auth, pas de multi-session) —
tourne sur 127.0.0.1 uniquement, pensée pour un usage desktop via navigateur.
Aucune donnée ne sort de la machine sauf ce que l'utilisateur déclenche
explicitement (clone git, découverte GitHub/Reddit, Ollama).
"""
from __future__ import annotations

import shutil
import sys
import webbrowser
from pathlib import Path
from threading import Timer
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Bad_USB_Classifier import payload_setup_agent as psa
from Bad_USB_Classifier.classify_badusb import run_classifier

APP_DIR = Path(__file__).resolve().parent
WORKSPACE = Path.home() / ".auto-flipper-tools" / "gui-workspace"
SOURCE_DIR = WORKSPACE / "source"
ORGANIZED_DIR = WORKSPACE / "organized"
READY_DIR = WORKSPACE / "ready"

for d in (SOURCE_DIR, ORGANIZED_DIR, READY_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    static_folder=str(APP_DIR / "static"),
    template_folder=str(APP_DIR / "templates"),
)

# État en mémoire du dernier scan d'enrichissement — un process mono-utilisateur
# local n'a pas besoin de session store; le plan est réutilisé entre le scan
# (GET /api/enrich/scan) et l'application des valeurs (POST /api/enrich/apply).
_last_plan: psa.SetupPlan | None = None
_last_matches_by_id: dict[str, tuple[Path, psa.FieldMatch]] = {}


def _safe_join(base: Path, relative: str) -> Path:
    """Empêche toute traversée de chemin (../) lors de l'upload de fichiers."""
    candidate = (base / relative).resolve()
    base_resolved = base.resolve()
    if base_resolved not in candidate.parents and candidate != base_resolved:
        raise ValueError(f"Chemin invalide (hors workspace): {relative}")
    return candidate


def _tree(root: Path) -> dict[str, Any]:
    """Construit un arbre JSON du dossier pour affichage colonne."""

    def walk(d: Path) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        try:
            children = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except FileNotFoundError:
            return []
        for child in children:
            if child.name.startswith("."):
                continue
            if child.is_dir():
                entries.append(
                    {"name": child.name, "type": "dir", "children": walk(child)}
                )
            else:
                entries.append(
                    {"name": child.name, "type": "file", "size": child.stat().st_size}
                )
        return entries

    return {
        "root": str(root),
        "exists": root.is_dir(),
        "children": walk(root) if root.is_dir() else [],
    }


@app.route("/")
def index():
    return send_from_directory(str(APP_DIR / "templates"), "index.html")


@app.route("/api/tree/<stage>")
def api_tree(stage: str):
    stage_dir = {
        "source": SOURCE_DIR,
        "organized": ORGANIZED_DIR,
        "ready": READY_DIR,
    }.get(stage)
    if stage_dir is None:
        return jsonify({"error": "unknown stage"}), 400
    return jsonify(_tree(stage_dir))


@app.route("/api/clone", methods=["POST"])
def api_clone():
    import subprocess

    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    if not url.startswith(("https://", "http://")):
        return (
            jsonify({"error": "URL invalide — attendu https://github.com/owner/repo"}),
            400,
        )
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
    if not repo_name or "/" in repo_name or repo_name in (".", ".."):
        return jsonify({"error": "Nom de dépôt invalide"}), 400
    dest = SOURCE_DIR / repo_name
    if dest.exists():
        return jsonify({"error": f"{repo_name} existe déjà dans la source"}), 400
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        return jsonify({"error": result.stderr.strip()[:500]}), 500
    return jsonify({"ok": True, "tree": _tree(SOURCE_DIR)})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Reçoit un lot de fichiers (drag&drop de dossier ou <input webkitdirectory>),
    chaque fichier porte son chemin relatif dans le champ `relpath`."""
    files = request.files.getlist("files")
    relpaths = request.form.getlist("relpaths")
    if len(files) != len(relpaths):
        return jsonify({"error": "Désynchronisation fichiers/chemins"}), 400

    written = 0
    for f, relpath in zip(files, relpaths):
        try:
            dest = _safe_join(SOURCE_DIR, relpath)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        dest.parent.mkdir(parents=True, exist_ok=True)
        f.save(str(dest))
        written += 1

    return jsonify({"ok": True, "written": written, "tree": _tree(SOURCE_DIR)})


@app.route("/api/classify", methods=["POST"])
def api_classify():
    data = request.get_json(force=True) or {}
    use_ollama = bool(data.get("use_ollama", False))
    model = data.get("model") or "qwen2.5-1.5b-heretic:latest"

    if not any(SOURCE_DIR.iterdir()):
        return (
            jsonify(
                {
                    "error": "Dossier source vide — dépose des fichiers ou clone un dépôt d'abord"
                }
            ),
            400,
        )

    if ORGANIZED_DIR.exists():
        shutil.rmtree(ORGANIZED_DIR)
    run_classifier(
        SOURCE_DIR, output_root=ORGANIZED_DIR, use_ollama=use_ollama, model=model
    )

    if READY_DIR.exists():
        shutil.rmtree(READY_DIR)
        READY_DIR.mkdir(parents=True, exist_ok=True)

    return jsonify({"ok": True, "tree": _tree(ORGANIZED_DIR)})


@app.route("/api/enrich/scan", methods=["POST"])
def api_enrich_scan():
    global _last_plan, _last_matches_by_id

    data = request.get_json(force=True) or {}
    use_ollama = bool(data.get("use_ollama", False))
    model = data.get("model") or "qwen2.5-1.5b-heretic:latest"

    if not ORGANIZED_DIR.is_dir() or not any(ORGANIZED_DIR.iterdir()):
        return (
            jsonify({"error": "Rien à enrichir — lance d'abord la classification"}),
            400,
        )

    plan = psa.analyze_tree(ORGANIZED_DIR, use_ollama=use_ollama, model=model)
    _last_plan = plan
    _last_matches_by_id = {}

    fields_by_key: dict[str, dict] = {}
    for path, matches in plan.to_configure.items():
        for m in matches:
            match_id = f"{path}::{m.spec.key}::{m.line_no}::{len(_last_matches_by_id)}"
            _last_matches_by_id[match_id] = (path, m)
            entry = fields_by_key.setdefault(
                m.spec.key,
                {
                    "key": m.spec.key,
                    "label": m.spec.label,
                    "example": m.spec.example,
                    "files": [],
                },
            )
            entry["files"].append(
                {
                    "match_id": match_id,
                    "file": str(path.relative_to(ORGANIZED_DIR)),
                    "line_no": m.line_no,
                    "raw_line": m.raw_line[:160],
                }
            )

    return jsonify(
        {
            "ready_count": len(plan.ready),
            "to_configure_count": len(plan.to_configure),
            "skipped_count": len(plan.skipped),
            "fields": list(fields_by_key.values()),
            "discord_webhook_guide": psa.DISCORD_WEBHOOK_GUIDE,
        }
    )


@app.route("/api/enrich/apply", methods=["POST"])
def api_enrich_apply():
    if _last_plan is None:
        return jsonify({"error": "Lance d'abord un scan (/api/enrich/scan)"}), 400

    data = request.get_json(force=True) or {}
    values_by_key: dict[str, str] = data.get("values") or {}  # {field_key: value}
    per_file_values: dict[str, str] = (
        data.get("per_file_values") or {}
    )  # {match_id: value}

    for key, val in values_by_key.items():
        if key == "discord_webhook" and val and not psa.DISCORD_WEBHOOK_RE.match(val):
            return jsonify({"error": f"URL de webhook Discord invalide: {val}"}), 400

    values: dict[str, dict[Path, str]] = {}
    for match_id, (path, m) in _last_matches_by_id.items():
        val = per_file_values.get(match_id) or values_by_key.get(m.spec.key)
        if val:
            values.setdefault(m.spec.key, {})[path] = val

    if READY_DIR.exists():
        shutil.rmtree(READY_DIR)
    READY_DIR.mkdir(parents=True)

    report_lines = psa.apply_and_copy(ORGANIZED_DIR, READY_DIR, _last_plan, values)
    (READY_DIR / "setup_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    return jsonify({"ok": True, "tree": _tree(READY_DIR)})


@app.route("/api/reset", methods=["POST"])
def api_reset():
    global _last_plan, _last_matches_by_id
    stage = (request.get_json(force=True) or {}).get("stage", "all")
    targets = {
        "source": [SOURCE_DIR],
        "organized": [ORGANIZED_DIR],
        "ready": [READY_DIR],
        "all": [SOURCE_DIR, ORGANIZED_DIR, READY_DIR],
    }.get(stage)
    if targets is None:
        return jsonify({"error": "unknown stage"}), 400
    for d in targets:
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True, exist_ok=True)
    _last_plan = None
    _last_matches_by_id = {}
    return jsonify({"ok": True})


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Auto-Flipper-Tools — interface graphique locale"
    )
    parser.add_argument("--port", type=int, default=5115)
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Ne pas ouvrir le navigateur automatiquement",
    )
    args = parser.parse_args()

    if not args.no_browser:
        Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}")).start()

    app.run(host="127.0.0.1", port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
