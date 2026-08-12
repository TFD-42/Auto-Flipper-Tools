#!/usr/bin/env python3
"""
Generates the "Source Repositories & Credits" Markdown section from
Bad_USB_Classifier/url.txt — one shields.io badge (GitHub stars, dynamic,
never hardcoded) per source repo, doubling as both credit and a real
backlink to each author.

url.txt is the single source of truth: every time a repo is added there,
re-run this script so the README stays in sync (see promotion-report.md —
this is exactly the desync problem this script solves).

Usage:
  python3 scripts/generate_credits_badges.py > credits_section.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

URL_FILE = Path(__file__).resolve().parent.parent / "Bad_USB_Classifier" / "url.txt"
REPO_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+?)/?$")
SECTION_RE = re.compile(r"^#\s*===\s*(.+?)\s*===\s*$")


def parse_sections(text: str) -> dict[str, list[tuple[str, str]]]:
    sections: dict[str, list[tuple[str, str]]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        m = SECTION_RE.match(line)
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
            continue
        if line.startswith("http") and current:
            m2 = REPO_RE.match(line)
            if m2:
                sections[current].append((m2.group(1), m2.group(2)))
    return sections


def badge_line(owner: str, repo: str) -> str:
    url = f"https://github.com/{owner}/{repo}"
    badge = (
        f"https://img.shields.io/github/stars/{owner}/{repo}"
        "?style=flat-square&label=%E2%98%85&color=blue"
    )
    return f"[![{owner}/{repo} stars]({badge})]({url}) [{owner}/{repo}]({url})"


def main() -> int:
    if not URL_FILE.is_file():
        print(f"Not found: {URL_FILE}", file=sys.stderr)
        return 1

    sections = parse_sections(URL_FILE.read_text())
    total = sum(len(repos) for repos in sections.values())

    print("## Source Repositories & Credits\n")
    print(
        "This project classifies and organizes BadUSB payloads sourced from the "
        f"community repositories below (**{total} repos**, kept in sync with "
        "[`Bad_USB_Classifier/url.txt`](Bad_USB_Classifier/url.txt) — the "
        "authoritative list, regenerate this section with "
        "`python3 scripts/generate_credits_badges.py`). **This project does "
        "not claim authorship of any third-party payload it classifies; full "
        "credit and copyright remain with each original author.** Star counts "
        "are live (shields.io dynamic badges), not hardcoded.\n"
    )

    for section, repos in sections.items():
        if not repos:
            continue
        print(f"### {section}\n")
        for owner, repo in repos:
            print(f"- {badge_line(owner, repo)}")
        print()

    print(
        "> **Want to add your repo?** Fork this project, add your URL to "
        "[`Bad_USB_Classifier/url.txt`](Bad_USB_Classifier/url.txt), and open "
        "a Pull Request!\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
