#!/usr/bin/env python3
"""
BadUSB Classifier — deep recursive scanner with multi-file payload bundle detection.

Handles both standalone Ducky Scripts and full attack bundles where a directory
contains the main script alongside helper modules (.ps1, .sh, .bat, .py),
binary payloads (.bin, .exe), and data assets (.wav, .png, .json, .xml, .csv).
When a bundle is detected the entire directory is copied as a unit.
"""
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

# === CONFIGURATION ===
OLLAMA_MODEL = "qwen2.5:3b"

VALID_KEYWORDS = {
    "STRING", "DELAY", "ENTER", "REM", "HOLD", "RELEASE", "GUI", "ALT", "CTRL",
    "SHIFT", "TAB", "BACKSPACE", "ESC", "SPACE", "CAPSLOCK", "NUMLOCK", "SCROLLLOCK",
    "UP", "DOWN", "LEFT", "RIGHT", "HOME", "END", "INSERT", "DELETE", "PAGEUP",
    "PAGEDOWN", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10",
    "F11", "F12", "PRINTSCREEN", "PAUSE", "MEDIA_PLAY_PAUSE", "MEDIA_NEXT_TRACK",
    "MEDIA_PREV_TRACK", "VOLUME_UP", "VOLUME_DOWN", "MUTE", "REMOTE", "LANGUAGE", "UNICODE"
}

TOPICS = [
    "exfiltration", "PassVault", "remote_access", "CartmanSong", "general",
    "phishing", "ReverseShell", "Chrome2Discord", "iMessageExfil", "prank",
    "Telegram", "credentials", "incident_response", "quackberry", "Text2Speech",
    "destructive", "Mimikatz", "ransom", "web2Discord", "EmailAndTextMessage",
    "MOAB", "execution", "mobile", "recon"
]

UNASSIGNED_DIR = "unassigned"

DUCKY_EXTENSIONS = {".txt", ".duck", ".ds"}
HELPER_EXTENSIONS = {".ps1", ".sh", ".bat", ".cmd", ".py", ".vbs", ".rb", ".pl"}
PAYLOAD_EXTENSIONS = {".bin", ".exe", ".dll", ".msi", ".jar", ".apk"}
DATA_EXTENSIONS = {
    ".wav", ".mp3", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg",
    ".json", ".xml", ".csv", ".dat", ".cfg", ".ini", ".yaml", ".yml",
    ".html", ".htm", ".css", ".js",
}
SKIP_EXTENSIONS = {".zip", ".gz", ".tar", ".7z", ".rar"}
SKIP_FILENAMES = {"readme.md", "license", "license.md", "licence", ".ds_store", ".gitignore", ".gitmodules"}

logger = logging.getLogger(__name__)


# ─── Ducky Script detection ───────────────────────────────────────────────────

def is_ducky_script(content: str) -> bool:
    lines = content.upper().splitlines()
    for line in lines:
        stripped = line.lstrip()
        if stripped and any(stripped.startswith(kw) for kw in VALID_KEYWORDS):
            return True
    return False


def read_text_safe(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


# ─── Topic classification ─────────────────────────────────────────────────────

def classify_content(content: str) -> str:
    """Return a topic for the given script content (always returns something)."""
    return (
        extract_topic_from_content(content)
        or ask_ollama_for_topic(content)
        or UNASSIGNED_DIR
    )


def extract_topic_from_content(content: str) -> Optional[str]:
    lower = content.lower()
    for topic in TOPICS:
        if topic.lower() in lower:
            return topic
    return None


def ask_ollama_for_topic(content: str) -> Optional[str]:
    prompt = (
        "You are a BadUSB script expert. Classify this Ducky Script:\n\n"
        f"{content[:2000]}\n\n"
        f"Categories: {', '.join(TOPICS)}\n\n"
        'Respond with ONLY the exact category name or "unknown".'
    )
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt, capture_output=True, text=True, timeout=30,
        )
        answer = result.stdout.strip().lower()
        for topic in TOPICS:
            if topic.lower() == answer:
                logger.info(f"Ollama classified as '{topic}'")
                return topic
        logger.warning(f"Ollama returned unrecognised answer: {answer!r}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Ollama timed out")
    except FileNotFoundError:
        logger.error("Ollama not found — install it or remove from PATH")
    except Exception as e:
        logger.error(f"Ollama error: {e}")
    return None


# ─── Bundle detection ─────────────────────────────────────────────────────────

def find_ducky_scripts_in(directory: Path) -> list[Path]:
    """Return every file in *directory* (non-recursive) that is a Ducky Script."""
    scripts = []
    for f in directory.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() not in DUCKY_EXTENSIONS:
            continue
        content = read_text_safe(f)
        if content and is_ducky_script(content):
            scripts.append(f)
    return scripts


def has_companion_files(directory: Path) -> bool:
    """True when the directory holds helper scripts, binaries, or data assets
    alongside one or more Ducky Scripts — i.e. it is a multi-file payload bundle."""
    dominated = HELPER_EXTENSIONS | PAYLOAD_EXTENSIONS | DATA_EXTENSIONS
    for f in directory.iterdir():
        if f.is_file() and f.suffix.lower() in dominated:
            return True
    for child in directory.iterdir():
        if child.is_dir():
            return True
    return False


def collect_combined_content(directory: Path, ducky_files: list[Path]) -> str:
    """Merge all Ducky Scripts + readable helpers into one blob for topic detection."""
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


# ─── Unique-path helper ──────────────────────────────────────────────────────

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


# ─── Core processing ─────────────────────────────────────────────────────────

class Stats:
    def __init__(self):
        self.bundles = 0
        self.singles = 0
        self.skipped = 0
        self.cleaned = 0


def process_bundle(directory: Path, ducky_files: list[Path], output_root: Path, stats: Stats):
    """Copy the entire payload directory as a bundle into the right topic folder."""
    combined = collect_combined_content(directory, ducky_files)
    topic = classify_content(combined)
    dest_dir = output_root / topic
    dest_dir.mkdir(parents=True, exist_ok=True)
    bundle_dest = unique_dir(dest_dir / directory.name)
    shutil.copytree(str(directory), str(bundle_dest))
    scripts = ", ".join(f.name for f in ducky_files)
    logger.info(f"[BUNDLE] {directory.name}/ ({scripts}) -> {topic}/{bundle_dest.name}/")
    stats.bundles += 1


def process_single(file_path: Path, output_root: Path, stats: Stats):
    """Copy a standalone Ducky Script into the right topic folder."""
    content = read_text_safe(file_path)
    if not content:
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
    return low.startswith(".") or low in {"__pycache__", "node_modules", "assets"}


def walk_and_classify(root_dir: Path, output_root: Path, stats: Stats):
    """Deep recursive walk.  At each directory decide: bundle, individual files, or recurse."""
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
            process_bundle(current, ducky_files, output_root, stats)
            # mark all descendants as handled so walk skips them
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
                process_single(fp, output_root, stats)
            else:
                stats.skipped += 1


# ─── Entry point ──────────────────────────────────────────────────────────────

def setup_logging(log_path: Path):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python classify_badusb.py <directory>")
        return 1

    root_dir = Path(sys.argv[1]).resolve()
    if not root_dir.is_dir():
        print(f"Error: {root_dir} is not a valid directory")
        return 1

    output_root = root_dir / "classified_badusb"
    output_root.mkdir(exist_ok=True)
    log_path = output_root / "classification.log"

    setup_logging(log_path)
    logger.info(f"Scanning {root_dir} (deep recursive, bundle-aware)")

    stats = Stats()
    walk_and_classify(root_dir, output_root, stats)

    logger.info(
        f"Done — bundles: {stats.bundles}, singles: {stats.singles}, "
        f"skipped: {stats.skipped}, cleaned: {stats.cleaned}"
    )
    print(f"\nLog: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
