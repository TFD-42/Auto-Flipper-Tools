#!/usr/bin/env python3
"""
Découverte de nouvelles sources BadUSB — recherche GitHub + Reddit.

Cherche des dépôts/posts pas encore listés dans url.txt à partir d'une liste
de requêtes ciblées (badusb, ducky script, flipper zero payloads...). N'écrit
rien par défaut (dry-run) — affiche les nouveaux candidats trouvés. Avec
--write, les ajoute à la fin de url.txt (dédoublonnés contre l'existant) pour
relecture avant de lancer classify_badusb.py --urls url.txt (qui clone/pull
via git — voir download_repos_from_urls()).

Ne clone jamais rien lui-même: la découverte et le clonage restent deux
étapes séparées, pour qu'un humain valide la liste avant d'exécuter quoi
que ce soit venant d'internet.

Sources:
  - GitHub Search API (api.github.com/search/repositories) — non authentifié,
    donc soumis à un rate-limit bas (10 req/min). Suffisant pour un usage
    occasionnel; ajoute un token via GITHUB_TOKEN pour un quota plus large.
  - Reddit (www.reddit.com/search.json) — endpoint public en lecture seule,
    on en extrait les liens github.com mentionnés dans les posts.
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
USER_AGENT = "Auto-Flipper-Tools-discover/1.0"


def _get_json(url: str, headers: dict) -> Optional[dict]:
    if urllib.parse.urlparse(url).scheme != "https":
        logger.warning("URL rejetée (schéma non-https): %s", url)
        return None
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    try:
        with urllib.request.urlopen(
            req, timeout=20
        ) as resp:  # nosec B310 - schéma vérifié ci-dessus
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.warning("HTTP %s pour %s", e.code, url)
    except (
        Exception
    ) as e:  # noqa: BLE001 - une source qui échoue ne doit pas bloquer les autres
        logger.warning("Échec requête %s: %s", url, e)
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
        time.sleep(6)  # reste sous la limite non-authentifiée (10 req/min)
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
        description="Cherche de nouveaux dépôts BadUSB sur GitHub/Reddit, absents de url.txt."
    )
    parser.add_argument(
        "--url-file",
        default=str(Path(__file__).parent / "url.txt"),
        help="Fichier de sources à compléter (défaut: Bad_USB_Classifier/url.txt)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Ajoute les nouveaux candidats à la fin du fichier (sinon: affichage seul)",
    )
    parser.add_argument(
        "--skip-reddit", action="store_true", help="Ne cherche que sur GitHub"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    url_file = Path(args.url_file).resolve()
    known = load_known(url_file)
    logger.info("%d source(s) déjà connue(s) dans %s", len(known), url_file)

    logger.info("Recherche GitHub...")
    candidates = search_github(GITHUB_QUERIES)

    if not args.skip_reddit:
        logger.info("Recherche Reddit...")
        candidates |= search_reddit(REDDIT_QUERIES)

    new = sorted(candidates - known)
    if not new:
        print("\nAucune nouvelle source trouvée.")
        return 0

    print(
        f"\n{len(new)} nouvelle(s) source(s) trouvée(s) (absentes de {url_file.name}):"
    )
    for u in new:
        print(f"  {u}")

    if args.write:
        with url_file.open("a", encoding="utf-8") as f:
            f.write(f"\n# === Découvertes automatiques ({len(new)}) ===\n")
            for u in new:
                f.write(f"{u}\n")
        print(f"\nAjoutées à {url_file}. Relis la liste avant de lancer:")
        print(f"  python3 Bad_USB_Classifier/classify_badusb.py --urls {url_file}")
    else:
        print("\n(dry-run — relance avec --write pour les ajouter à url.txt)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
