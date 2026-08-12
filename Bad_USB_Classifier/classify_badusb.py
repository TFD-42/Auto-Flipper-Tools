#!/usr/bin/env python3
"""
BadUSB Classifier — deep recursive, bundle-aware, dedup, two-pass AI refinement.

Pass 1: fast scan — keyword match + short Ollama query, dedup by hash + header.
Pass 2: deep Ollama — re-reads EVERY file (150 lines min) one by one through
         Ollama to get precise per-file classification, then majority-votes
         each bundle/script into the correct topic.  Slow but accurate.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# === CONFIGURATION ===
OLLAMA_MODEL = "qwen2.5:3b"
OLLAMA_TIMEOUT_FAST = 30
OLLAMA_TIMEOUT_DEEP = 120
DEEP_MIN_LINES = 150

# Controlled by run_classifier()/CLI (--no-ollama, --model). If False,
# classification stays 100% keyword-matching (fast, no network) and pass 2
# (deep refinement, one Ollama call per file) is skipped.
OLLAMA_ENABLED = True

VALID_KEYWORDS = {
    "STRING",
    "DELAY",
    "ENTER",
    "REM",
    "HOLD",
    "RELEASE",
    "GUI",
    "ALT",
    "CTRL",
    "SHIFT",
    "TAB",
    "BACKSPACE",
    "ESC",
    "SPACE",
    "CAPSLOCK",
    "NUMLOCK",
    "SCROLLLOCK",
    "UP",
    "DOWN",
    "LEFT",
    "RIGHT",
    "HOME",
    "END",
    "INSERT",
    "DELETE",
    "PAGEUP",
    "PAGEDOWN",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "PRINTSCREEN",
    "PAUSE",
    "MEDIA_PLAY_PAUSE",
    "MEDIA_NEXT_TRACK",
    "MEDIA_PREV_TRACK",
    "VOLUME_UP",
    "VOLUME_DOWN",
    "MUTE",
    "REMOTE",
    "LANGUAGE",
    "UNICODE",
}

TOPICS = [
    "exfiltration",
    "PassVault",
    "remote_access",
    "CartmanSong",
    "general",
    "phishing",
    "ReverseShell",
    "Chrome2Discord",
    "iMessageExfil",
    "prank",
    "Telegram",
    "credentials",
    "incident_response",
    "quackberry",
    "Text2Speech",
    "destructive",
    "Mimikatz",
    "ransom",
    "web2Discord",
    "EmailAndTextMessage",
    "MOAB",
    "execution",
    "mobile",
    "recon",
]
TOPICS_LOWER = {t.lower(): t for t in TOPICS}

UNASSIGNED_DIR = "unassigned"

DUCKY_EXTENSIONS = {".txt", ".duck", ".ds"}
HELPER_EXTENSIONS = {".ps1", ".sh", ".bat", ".cmd", ".py", ".vbs", ".rb", ".pl"}
PAYLOAD_EXTENSIONS = {".bin", ".exe", ".dll", ".msi", ".jar", ".apk"}
DATA_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".svg",
    ".json",
    ".xml",
    ".csv",
    ".dat",
    ".cfg",
    ".ini",
    ".yaml",
    ".yml",
    ".html",
    ".htm",
    ".css",
    ".js",
}
READABLE_EXTENSIONS = (
    DUCKY_EXTENSIONS
    | HELPER_EXTENSIONS
    | {".html", ".htm", ".js", ".css", ".json", ".xml", ".yaml", ".yml"}
)
SKIP_EXTENSIONS = {".zip", ".gz", ".tar", ".7z", ".rar"}
SKIP_FILENAMES = {
    "readme.md",
    "license",
    "license.md",
    "licence",
    "licence.md",
    ".ds_store",
    ".gitignore",
    ".gitmodules",
    "contributing.md",
    "changelog.md",
    "code_of_conduct.md",
}

HEADER_LINES = 5

logger = logging.getLogger(__name__)


# ─── Deduplication ───────────────────────────────────────────────────────────


class DedupIndex:
    def __init__(self):
        self.full_hashes: set[str] = set()
        self.header_fps: set[str] = set()
        self.dupes_hash = 0
        self.dupes_header = 0

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()

    def _header_fingerprint(self, content: str) -> str:
        code_lines: list[str] = []
        for raw in content.splitlines():
            stripped = raw.strip()
            if not stripped:
                continue
            upper = stripped.upper()
            if upper.startswith("REM") and any(
                k in upper for k in ("AUTHOR", "CREDIT", "BY ", "NAME")
            ):
                continue
            code_lines.append(stripped)
            if len(code_lines) >= HEADER_LINES:
                break
        blob = "\n".join(code_lines)
        return hashlib.sha256(blob.encode("utf-8", errors="replace")).hexdigest()

    def is_duplicate(self, content: str) -> bool:
        fh = self._content_hash(content)
        if fh in self.full_hashes:
            self.dupes_hash += 1
            return True
        hp = self._header_fingerprint(content)
        if hp in self.header_fps:
            self.dupes_header += 1
            return True
        self.full_hashes.add(fh)
        self.header_fps.add(hp)
        return False


# ─── Ducky Script detection ─────────────────────────────────────────────────


def is_ducky_script(content: str) -> bool:
    for line in content.upper().splitlines():
        stripped = line.lstrip()
        if stripped and any(stripped.startswith(kw) for kw in VALID_KEYWORDS):
            return True
    return False


def read_text_safe(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


# ─── Topic classification — FAST (pass 1) ───────────────────────────────────


def classify_content(content: str) -> str:
    return (
        extract_topic_from_content(content)
        or ask_ollama_fast(content)
        or UNASSIGNED_DIR
    )


def extract_topic_from_content(content: str) -> Optional[str]:
    lower = content.lower()
    for topic in TOPICS:
        if topic.lower() in lower:
            return topic
    return None


def ask_ollama_fast(content: str) -> Optional[str]:
    prompt = (
        "You are a BadUSB script expert. Classify this Ducky Script:\n\n"
        f"{content[:2000]}\n\n"
        f"Categories: {', '.join(TOPICS)}\n\n"
        'Respond with ONLY the exact category name or "unknown".'
    )
    return _ollama_query(prompt, OLLAMA_TIMEOUT_FAST)


# ─── Topic classification — DEEP (pass 2) ───────────────────────────────────


def ask_ollama_deep(content: str, filename: str) -> Optional[str]:
    """Send at least 150 lines of actual content to Ollama for precise classification."""
    lines = content.splitlines()
    chunk = "\n".join(lines[: max(DEEP_MIN_LINES, len(lines))])

    prompt = f"""You are a security expert specializing in BadUSB, Ducky Script, and HID attacks.

Analyze the following file carefully. Read every line of code.

FILENAME: {filename}

--- FILE CONTENT START ---
{chunk}
--- FILE CONTENT END ---

Based on the FULL content above, what is the primary purpose / attack category of this script?

Choose EXACTLY ONE category from this list:
{', '.join(TOPICS)}

Rules:
- If the script steals passwords, WiFi keys, browser data, cookies → credentials or exfiltration
- If the script opens a reverse shell or remote connection → ReverseShell or remote_access
- If the script sends data to Discord → Chrome2Discord or web2Discord
- If the script sends data to Telegram → Telegram
- If the script is a joke, wallpaper change, sound prank → prank
- If the script deletes files or causes damage → destructive
- If the script does reconnaissance or system info gathering → recon
- If the script runs Mimikatz or credential dumping → Mimikatz
- If the script demands payment or encrypts files → ransom
- If the script targets mobile devices (Android/iOS) → mobile
- If the script sends phishing pages or fake login → phishing
- If the script targets macOS specifically, still classify by PURPOSE not OS
- If none match clearly → general

Respond with ONLY the exact category name, nothing else."""

    return _ollama_query(prompt, OLLAMA_TIMEOUT_DEEP)


def _ollama_query(prompt: str, timeout: int) -> Optional[str]:
    if not OLLAMA_ENABLED:
        return None
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        raw = result.stdout.strip()
        # try exact match first
        if raw.lower() in TOPICS_LOWER:
            topic = TOPICS_LOWER[raw.lower()]
            return topic
        # try to find a topic name anywhere in the response
        for topic in TOPICS:
            if topic.lower() in raw.lower():
                return topic
        logger.warning(f"Ollama unrecognised: {raw!r}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Ollama timed out")
    except FileNotFoundError:
        logger.error("Ollama not found")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
    return None


# ─── Bundle detection ────────────────────────────────────────────────────────


def find_ducky_scripts_in(directory: Path) -> list[Path]:
    scripts = []
    for f in directory.iterdir():
        if not f.is_file() or f.suffix.lower() not in DUCKY_EXTENSIONS:
            continue
        content = read_text_safe(f)
        if content and is_ducky_script(content):
            scripts.append(f)
    return scripts


def has_companion_files(directory: Path) -> bool:
    dominated = HELPER_EXTENSIONS | PAYLOAD_EXTENSIONS | DATA_EXTENSIONS
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in dominated:
            return True
    for child in directory.iterdir():
        if child.is_dir() and child.name.lower() not in {
            "assets",
            "__pycache__",
            ".git",
        }:
            return True
    return False


def collect_combined_content(directory: Path, ducky_files: list[Path]) -> str:
    parts: list[str] = []
    for f in ducky_files:
        c = read_text_safe(f)
        if c:
            parts.append(c)
    for f in sorted(directory.rglob("*")):
        if f in ducky_files or not f.is_file():
            continue
        if f.suffix.lower() in HELPER_EXTENSIONS | {".txt"}:
            c = read_text_safe(f)
            if c:
                parts.append(c)
    return "\n".join(parts)


# ─── Path helpers ────────────────────────────────────────────────────────────


def unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    i = 1
    while True:
        candidate = dest.parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def unique_dir(dest: Path) -> Path:
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.parent / f"{dest.name}_{i}"
        if not candidate.exists():
            return candidate
        i += 1


# ─── Pass 1: fast classification ────────────────────────────────────────────


class Stats:
    def __init__(self):
        self.bundles = 0
        self.singles = 0
        self.skipped = 0
        self.cleaned = 0
        self.dupes = 0
        self.refined = 0


def process_bundle(directory, ducky_files, output_root, dedup, stats):
    combined = collect_combined_content(directory, ducky_files)
    if dedup.is_duplicate(combined):
        logger.info(f"[DUPE-BUNDLE] {directory.name}/")
        stats.dupes += 1
        return
    topic = classify_content(combined)
    dest_dir = output_root / topic
    dest_dir.mkdir(parents=True, exist_ok=True)
    bundle_dest = unique_dir(dest_dir / directory.name)
    shutil.copytree(str(directory), str(bundle_dest))
    logger.info(f"[BUNDLE] {directory.name}/ -> {topic}/")
    stats.bundles += 1


def process_single(file_path, output_root, dedup, stats):
    content = read_text_safe(file_path)
    if not content:
        return
    if dedup.is_duplicate(content):
        logger.info(f"[DUPE] {file_path.name}")
        stats.dupes += 1
        return
    topic = classify_content(content)
    dest_dir = output_root / topic
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = unique_dest(dest_dir / file_path.name)
    shutil.copy2(str(file_path), str(dest))
    logger.info(f"[SINGLE] {file_path.name} -> {topic}/")
    stats.singles += 1


def should_skip_dir(name: str) -> bool:
    low = name.lower()
    return low.startswith(".") or low in {
        "__pycache__",
        "node_modules",
        "assets",
        "classified_badusb",
    }


def pass1_classify(root_dir: Path, output_root: Path, stats: Stats):
    logger.info("═══ PASS 1: fast classification (keyword + short Ollama) ═══")
    dedup = DedupIndex()
    handled_dirs: set[Path] = set()

    for current_dir, subdirs, files in os.walk(root_dir, topdown=True):
        current = Path(current_dir)
        if current == output_root or output_root in current.parents:
            subdirs.clear()
            continue
        if current in handled_dirs:
            subdirs.clear()
            continue
        if should_skip_dir(current.name) and current != root_dir:
            subdirs.clear()
            continue

        ducky_files = find_ducky_scripts_in(current)
        if ducky_files and has_companion_files(current):
            process_bundle(current, ducky_files, output_root, dedup, stats)
            for child in current.rglob("*"):
                if child.is_dir():
                    handled_dirs.add(child)
            subdirs.clear()
            continue

        for f in files:
            fp = current / f
            if fp.name.lower() in SKIP_FILENAMES:
                stats.cleaned += 1
                continue
            if fp.suffix.lower() in SKIP_EXTENSIONS:
                stats.skipped += 1
                continue
            if fp.suffix.lower() not in DUCKY_EXTENSIONS:
                stats.skipped += 1
                continue
            content = read_text_safe(fp)
            if content and is_ducky_script(content):
                process_single(fp, output_root, dedup, stats)
            else:
                stats.skipped += 1

    stats.dupes = dedup.dupes_hash + dedup.dupes_header
    logger.info(
        f"Pass 1 done — bundles: {stats.bundles}, singles: {stats.singles}, "
        f"dupes: {stats.dupes}, skipped: {stats.skipped}"
    )


# ─── Pass 2: deep Ollama refinement — file by file ──────────────────────────


def deep_classify_file(file_path: Path) -> Optional[str]:
    """Read a file and send it through deep Ollama analysis."""
    content = read_text_safe(file_path)
    if not content or len(content.strip()) < 10:
        return None
    return ask_ollama_deep(content, file_path.name)


def deep_classify_bundle(bundle_dir: Path) -> Optional[str]:
    """Read every readable file in the bundle through Ollama individually,
    then majority-vote the topic."""
    votes: dict[str, int] = {}

    readable_files = []
    for f in sorted(bundle_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.name.lower() in SKIP_FILENAMES:
            continue
        if f.suffix.lower() in READABLE_EXTENSIONS:
            readable_files.append(f)

    if not readable_files:
        return None

    for f in readable_files:
        content = read_text_safe(f)
        if not content or len(content.strip()) < 10:
            continue
        topic = ask_ollama_deep(content, f.name)
        if topic:
            votes[topic] = votes.get(topic, 0) + 1
            logger.info(f"  [DEEP] {f.name} -> {topic}")

    if not votes:
        return None

    winner = max(votes, key=lambda topic: votes[topic])
    logger.info(f"  [VOTE] {bundle_dir.name}/ -> {winner} (votes: {votes})")
    return winner


def pass2_refine(output_root: Path, stats: Stats):
    """Re-classify every item in the output using deep Ollama analysis.
    Each readable file is sent individually with 150+ lines."""
    if not OLLAMA_ENABLED:
        logger.info("═══ PASS 2 skipped (Ollama disabled) ═══")
        return
    logger.info("═══ PASS 2: deep Ollama refinement (file by file, 150 lines min) ═══")

    topic_dirs = sorted([d for d in output_root.iterdir() if d.is_dir()])

    for topic_dir in topic_dirs:
        current_topic = topic_dir.name
        logger.info(f"Refining topic: {current_topic}/ ...")

        # ── bundles first ──
        bundles = sorted([d for d in topic_dir.iterdir() if d.is_dir()])
        for bundle in bundles:
            logger.info(f"  Analyzing bundle: {bundle.name}/")
            new_topic = deep_classify_bundle(bundle)

            if new_topic and new_topic != current_topic:
                dest_dir = output_root / new_topic
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = unique_dir(dest_dir / bundle.name)
                shutil.move(str(bundle), str(dest))
                logger.info(f"  [MOVED] {bundle.name}/: {current_topic} -> {new_topic}")
                stats.refined += 1
            elif new_topic:
                logger.info(f"  [OK] {bundle.name}/ stays in {current_topic}")

        # ── standalone scripts ──
        scripts = sorted(
            [
                f
                for f in topic_dir.iterdir()
                if f.is_file() and f.suffix.lower() in DUCKY_EXTENSIONS
            ]
        )
        for script in scripts:
            content = read_text_safe(script)
            if not content or not is_ducky_script(content):
                continue

            new_topic = ask_ollama_deep(content, script.name)
            if not new_topic:
                continue

            if new_topic != current_topic:
                dest_dir = output_root / new_topic
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = unique_dest(dest_dir / script.name)
                shutil.move(str(script), str(dest))
                logger.info(f"  [MOVED] {script.name}: {current_topic} -> {new_topic}")
                stats.refined += 1
            else:
                logger.info(f"  [OK] {script.name} stays in {current_topic}")

    # clean empty dirs
    for topic_dir in list(output_root.iterdir()):
        if topic_dir.is_dir() and not any(topic_dir.iterdir()):
            topic_dir.rmdir()
            logger.info(f"  [CLEAN] removed empty: {topic_dir.name}/")

    logger.info(f"Pass 2 done — {stats.refined} items reclassified")


# ─── GitHub repo downloading ────────────────────────────────────────────────


def download_repos_from_urls(url_file: Path, download_dir: Path) -> Path:
    """Clones (or updates) every GitHub repo listed in url_file into
    download_dir via `git clone --depth 1` — first run: clones everything;
    subsequent runs: `git pull` on repos already present. See
    discover_repos.py to find new sources to add to url_file before
    re-running.
    """
    urls = [
        line.strip()
        for line in url_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    logger.info(f"Found {len(urls)} URLs in {url_file}")
    download_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for i, url in enumerate(urls, 1):
        url = url.rstrip("/")
        parts = url.split("/")
        if len(parts) < 5:
            logger.warning(f"[{i}/{len(urls)}] Skipping invalid URL: {url}")
            continue

        repo = parts[-1].replace(".git", "")
        repo_dest = download_dir / repo

        if repo_dest.exists():
            logger.info(f"[{i}/{len(urls)}] Update: {repo}")
            result = subprocess.run(
                ["git", "-C", str(repo_dest), "pull", "--ff-only"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.warning(
                    f"  git pull failed for {repo}: {result.stderr.strip()[:200]}"
                )
            success += 1
            continue

        logger.info(f"[{i}/{len(urls)}] Clone: {url} ...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(repo_dest)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode == 0:
            logger.info(f"  -> {repo_dest.name}/")
            success += 1
        else:
            logger.error(f"  Failed: {result.stderr.strip()[:200]}")

    logger.info(f"Clone/update complete: {success}/{len(urls)} repos")
    return download_dir


# ─── Entry point ─────────────────────────────────────────────────────────────


def setup_logging(log_path: Path):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )


def run_classifier(
    root_dir: Path,
    output_root: Optional[Path] = None,
    use_ollama: bool = True,
    model: Optional[str] = None,
) -> Path:
    """Classifies every BadUSB script found under root_dir into output_root
    (defaults to root_dir/classified_badusb). Returns the output folder —
    used directly by badusb_pipeline.py to chain into the enrichment agent
    without an extra intermediate folder.

    use_ollama=False disables all network calls (100% keyword-matching
    classification, pass 2 skipped) — useful when the configured model
    isn't installed locally, or for a fast/deterministic run.
    """
    global OLLAMA_ENABLED, OLLAMA_MODEL
    OLLAMA_ENABLED = use_ollama
    if model:
        OLLAMA_MODEL = model

    if output_root is None:
        output_root = root_dir / "classified_badusb"
    if output_root.exists():
        shutil.rmtree(output_root)
        print(f"Cleaned previous output: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    log_path = output_root / "classification.log"

    setup_logging(log_path)

    stats = Stats()
    pass1_classify(root_dir, output_root, stats)
    pass2_refine(output_root, stats)

    logger.info(
        f"═══ FINAL: bundles={stats.bundles}, singles={stats.singles}, "
        f"dupes={stats.dupes}, refined={stats.refined}, "
        f"skipped={stats.skipped}, cleaned={stats.cleaned} ═══"
    )
    print(f"\nLog: {log_path}")
    return output_root


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BadUSB Classifier — deep recursive, bundle-aware, dedup, two-pass AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify an existing directory of scripts
  python classify_badusb.py /path/to/scripts

  # Download repos from url list, then classify
  python classify_badusb.py --urls url.txt

  # Download to a specific directory, then classify
  python classify_badusb.py --urls url.txt --output /tmp/badusb_repos
        """,
    )
    parser.add_argument("directory", nargs="?", help="Directory to classify")
    parser.add_argument(
        "--urls",
        metavar="FILE",
        help="Download repos from URL list (one URL per line), then classify",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="DIR",
        help="Download directory (default: ./badusb_repos)",
    )
    parser.add_argument(
        "--model",
        default=OLLAMA_MODEL,
        help=f"Ollama model to use (default: {OLLAMA_MODEL})",
    )
    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Disable all Ollama calls (keyword-matching only, no pass 2)",
    )

    args = parser.parse_args()

    if args.urls:
        url_file = Path(args.urls).resolve()
        if not url_file.is_file():
            print(f"Error: URL file not found: {url_file}")
            return 1
        download_dir = (
            Path(args.output).resolve()
            if args.output
            else Path("badusb_repos").resolve()
        )
        log_path = download_dir / "download.log"
        download_dir.mkdir(parents=True, exist_ok=True)
        setup_logging(log_path)
        download_repos_from_urls(url_file, download_dir)
        run_classifier(download_dir, use_ollama=not args.no_ollama, model=args.model)
        return 0

    if args.directory:
        root_dir = Path(args.directory).resolve()
        if not root_dir.is_dir():
            print(f"Error: {root_dir} is not a valid directory")
            return 1
        run_classifier(root_dir, use_ollama=not args.no_ollama, model=args.model)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
