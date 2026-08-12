#!/usr/bin/env python3
"""
Discovery of new BadUSB sources — GitHub + Reddit search.

Looks for repos/posts not yet listed in url.txt from a list of targeted
queries (badusb, ducky script, flipper zero payloads...). Writes nothing by
default (dry-run) — just prints the new candidates found. With --write,
appends them to the end of url.txt (deduplicated against the existing list)
for review before running classify_badusb.py --urls url.txt (which
clones/pulls via git — see download_repos_from_urls()).

Never clones anything itself: discovery and cloning stay two separate
steps, so a human reviews the list before anything from the internet gets
executed.

Sources:
  - GitHub Search API (api.github.com/search/repositories) — unauthenticated,
    so subject to a low rate limit (10 req/min). Enough for occasional use;
    add a token via GITHUB_TOKEN for a larger quota.
  - Reddit (www.reddit.com/search.json) — public read-only endpoint, we
    extract the github.com links mentioned in posts.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

GITHUB_QUERIES = [
    "badusb ducky script flipper",
    "flipper zero badusb payloads",
    "rubber ducky payloads flipper zero",
    "ducky script payload collection",
]
REDDIT_QUERIES = ["flipper zero badusb payload", "badusb ducky script github"]

GITHUB_REPO_RE = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+")
USER_AGENT = "BK_Flipper_Full_Pipline-discover/1.0"


def _get_json(url: str, headers: dict) -> Optional[dict]:
    if urllib.parse.urlparse(url).scheme != "https":
        logger.warning("URL rejected (non-https scheme): %s", url)
        return None
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    try:
        with urllib.request.urlopen(
            req, timeout=20
        ) as resp:  # nosec B310 - scheme checked above
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.warning("HTTP %s for %s", e.code, url)
    except (
        Exception
    ) as e:  # noqa: BLE001 - one failing source shouldn't block the others
        logger.warning("Request failed %s: %s", url, e)
    return None


def search_github(queries: list[str]) -> set[str]:
    found: set[str] = set()
    for q in queries:
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&sort=stars&per_page=20"
        data = _get_json(url, {"Accept": "application/vnd.github+json"})
        if not data:
            continue
        for item in data.get("items", []):
            html_url = item.get("html_url")
            if html_url:
                found.add(html_url.rstrip("/"))
        time.sleep(6)  # stay under the unauthenticated limit (10 req/min)
    return found


def search_reddit(queries: list[str]) -> set[str]:
    found: set[str] = set()
    for q in queries:
        url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(q)}&limit=25&sort=relevance"
        data = _get_json(url, {})
        if not data:
            continue
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            text = " ".join(str(post.get(k, "")) for k in ("url", "selftext", "title"))
            found.update(m.rstrip("/") for m in GITHUB_REPO_RE.findall(text))
        time.sleep(2)
    return found


def load_known(url_file: Path) -> set[str]:
    if not url_file.is_file():
        return set()
    return {
        line.strip().rstrip("/")
        for line in url_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Searches GitHub/Reddit for new BadUSB repos not already in url.txt."
    )
    parser.add_argument(
        "--url-file",
        default=str(Path(__file__).parent / "url.txt"),
        help="Source file to append to (default: Bad_USB_Classifier/url.txt)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Append the new candidates to the end of the file (otherwise: print only)",
    )
    parser.add_argument("--skip-reddit", action="store_true", help="Only search GitHub")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    url_file = Path(args.url_file).resolve()
    known = load_known(url_file)
    logger.info("%d known source(s) in %s", len(known), url_file)

    logger.info("Searching GitHub...")
    candidates = search_github(GITHUB_QUERIES)

    if not args.skip_reddit:
        logger.info("Searching Reddit...")
        candidates |= search_reddit(REDDIT_QUERIES)

    new = sorted(candidates - known)
    if not new:
        print("\nNo new source found.")
        return 0

    print(f"\n{len(new)} new source(s) found (not in {url_file.name}):")
    for u in new:
        print(f"  {u}")

    if args.write:
        with url_file.open("a", encoding="utf-8") as f:
            f.write(f"\n# === Automatic discoveries ({len(new)}) ===\n")
            for u in new:
                f.write(f"{u}\n")
        print(f"\nAppended to {url_file}. Review the list before running:")
        print(f"  python3 Bad_USB_Classifier/classify_badusb.py --urls {url_file}")
    else:
        print("\n(dry-run — re-run with --write to add them to url.txt)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
