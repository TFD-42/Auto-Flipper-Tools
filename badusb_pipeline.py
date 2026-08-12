#!/usr/bin/env python3
"""
Unified BadUSB pipeline — the project's single entry point.

Point this at any folder containing BadUSB scripts (.txt/.duck/.ds, loose
or already organized into subfolders, doesn't matter) and it will:

  1. Classify (Bad_USB_Classifier/classify_badusb.py) — Ducky Script
     detection, deduplication, classification by theme (keyword + Ollama).
  2. Enrich   (Bad_USB_Classifier/payload_setup_agent.py) — detects scripts
     that need a value (Discord webhook, IP, token...), guides you through
     creating one if needed (e.g. a Discord webhook from a brand-new
     account), and customizes the scripts that need it.

A single, clean output folder ready to copy onto the Flipper Zero's SD
card — no extra intermediate folder: the enrichment step modifies in place
the copies already produced by classification (never the original files).

Usage:
  python3 badusb_pipeline.py <source_folder> [--output DIR] [--no-ollama]
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
        description="Classifies and enriches a folder of BadUSB scripts in a single pass."
    )
    parser.add_argument(
        "directory",
        help="Source folder containing BadUSB scripts (any structure)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output folder (default: <source_folder>_organized next to it)",
    )
    parser.add_argument(
        "--model",
        default="qwen2.5-1.5b-heretic:latest",
        help="Ollama model for the classification/detection fallback",
    )
    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Disable all Ollama calls (regex/keyword matching only)",
    )
    args = parser.parse_args()

    source = Path(args.directory).expanduser().resolve()
    if not source.is_dir():
        print(f"Error: {source} is not a valid directory.")
        return 1

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source.parent / f"{source.name}_organized"
    )

    print(f"=== Step 1/2 — Classification: {source} -> {output} ===")
    output = run_classifier(
        source, output_root=output, use_ollama=not args.no_ollama, model=args.model
    )

    print(f"\n=== Step 2/2 — Enrichment (in place in {output}) ===")
    plan = analyze_tree(output, use_ollama=not args.no_ollama, model=args.model)
    print_summary(plan)

    values: dict = {}
    if plan.to_configure:
        proceed = input("\nConfigure these files now? [Y/n] ").strip().lower()
        if proceed != "n":
            values = collect_field_values(plan)
    else:
        print("\nNo file needs configuration.")

    report_lines = apply_and_copy(output, output, plan, values)
    report_path = output / "setup_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"\nDone. Folder ready: {output}")
    print(f"Report: {report_path}")
    print(
        "All that's left is to copy this folder into badusb/ on the Flipper Zero's SD card."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
