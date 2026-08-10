#!/usr/bin/env python3
"""
Pipeline BadUSB unifié — point d'entrée unique du projet.

Colle n'importe quel dossier contenant des scripts BadUSB (.txt/.duck/.ds,
en vrac ou déjà organisés par sous-dossiers, peu importe) et ce script:

  1. Classe   (Bad_USB_Classifier/classify_badusb.py) — détection Ducky
     Script, dédoublonnage, classification par thème (keyword + Ollama).
  2. Enrichit (Bad_USB_Classifier/payload_setup_agent.py) — détecte les scripts qui
     ont besoin d'une valeur (webhook Discord, IP, token...), guide la
     création si besoin (ex: webhook Discord depuis un compte tout neuf),
     et personnalise les scripts qui en ont besoin.

Un seul dossier de sortie, propre et prêt à copier sur la carte SD du
Flipper Zero — pas de dossier intermédiaire supplémentaire: l'étape
d'enrichissement modifie en place les copies déjà produites par la
classification (jamais les fichiers d'origine).

Usage:
  python3 badusb_pipeline.py <dossier_source> [--output DIR] [--no-ollama]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from Bad_USB_Classifier.classify_badusb import run_classifier
from Bad_USB_Classifier.payload_setup_agent import (
    analyze_tree,
    apply_and_copy,
    collect_field_values,
    print_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classe et enrichit un dossier de scripts BadUSB en un seul passage."
    )
    parser.add_argument(
        "directory",
        help="Dossier source contenant des scripts BadUSB (n'importe quelle structure)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Dossier de sortie (défaut: <dossier_source>_organized à côté)",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-1.5b-heretic:latest",
        help="Modèle Ollama pour le fallback de classification/détection",
    )
    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Désactive tout appel Ollama (regex/mots-clés uniquement)",
    )
    args = parser.parse_args()

    source = Path(args.directory).expanduser().resolve()
    if not source.is_dir():
        print(f"Erreur: {source} n'est pas un dossier valide.")
        return 1

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source.parent / f"{source.name}_organized"
    )

    print(f"=== Étape 1/2 — Classification: {source} -> {output} ===")
    output = run_classifier(
        source, output_root=output, use_ollama=not args.no_ollama, model=args.model
    )

    print(f"\n=== Étape 2/2 — Enrichissement (en place dans {output}) ===")
    plan = analyze_tree(output, use_ollama=not args.no_ollama, model=args.model)
    print_summary(plan)

    values: dict = {}
    if plan.to_configure:
        proceed = input("\nConfigurer ces fichiers maintenant ? [O/n] ").strip().lower()
        if proceed != "n":
            values = collect_field_values(plan)
    else:
        print("\nAucun fichier ne nécessite de configuration.")

    report_lines = apply_and_copy(output, output, plan, values)
    report_path = output / "setup_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"\nTerminé. Dossier prêt: {output}")
    print(f"Rapport: {report_path}")
    print(
        "Il ne reste plus qu'à copier ce dossier dans badusb/ sur la carte SD du Flipper Zero."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
