#!/usr/bin/env python3
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
SUPPORTED_EXTENSIONS = {".txt", ".duck", ".ds"}
IGNORED_FILENAMES = {"readme.md"}

logger = logging.getLogger(__name__)


def is_ducky_script(content: str) -> bool:
    """Verify presence of valid Ducky Script keywords."""
    lines = content.upper().splitlines()
    for line in lines:
        stripped = line.lstrip()
        if stripped and any(stripped.startswith(kw) for kw in VALID_KEYWORDS):
            return True
    return False


def extract_topic_from_content(content: str) -> Optional[str]:
    """Extract topic from content by keyword matching."""
    lower_content = content.lower()
    for topic in TOPICS:
        if topic.lower() in lower_content:
            logger.debug(f"Found topic '{topic}' via keyword match")
            return topic
    return None


def ask_ollama_for_topic(content: str) -> Optional[str]:
    """Query Ollama for topic classification."""
    prompt = f"""You are a BadUSB script expert. Classify this Ducky Script:

{content[:2000]}

Categories: {', '.join(TOPICS)}

Respond with ONLY the exact category name or "unknown"."""
    
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30
        )
        answer = result.stdout.strip().lower()
        
        for topic in TOPICS:
            if topic.lower() == answer:
                logger.info(f"Ollama classified as '{topic}'")
                return topic
        
        logger.warning(f"Ollama returned unknown category: {answer}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Ollama request timed out")
        return None
    except FileNotFoundError:
        logger.error("Ollama not found - ensure it's installed and in PATH")
        return None
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None


def get_unique_path(dest_path: Path) -> Path:
    """Generate unique filename if destination exists."""
    if not dest_path.exists():
        return dest_path
    
    base, ext = dest_path.stem, dest_path.suffix
    counter = 1
    while True:
        new_path = dest_path.parent / f"{base}_{counter}{ext}"
        if not new_path.exists():
            return new_path
        counter += 1


def process_file(file_path: Path, root_output_dir: Path) -> bool:
    """Process file: validate, classify, move. Returns True if successful."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError as e:
        logger.error(f"Cannot read {file_path}: {e}")
        return False

    if not is_ducky_script(content):
        logger.debug(f"Skipped (not Ducky Script): {file_path}")
        return False

    topic = extract_topic_from_content(content) or ask_ollama_for_topic(content) or UNASSIGNED_DIR

    dest_dir = root_output_dir / topic
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = get_unique_path(dest_dir / file_path.name)
    
    try:
        shutil.move(str(file_path), str(dest_path))
        logger.info(f"Moved {file_path.name} -> {topic}/")
        return True
    except OSError as e:
        logger.error(f"Failed to move {file_path}: {e}")
        return False


def setup_logging(log_path: Path) -> None:
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
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
    logger.info(f"Starting classification from {root_dir}")

    stats = {"processed": 0, "skipped": 0, "removed": 0}

    for current_dir, subdirs, files in os.walk(root_dir):
        current_path = Path(current_dir)
        if output_root in current_path.parents or current_path == output_root:
            subdirs.clear()
            continue
        
        for filename in files:
            file_path = current_path / filename
            
            if filename.lower() in IGNORED_FILENAMES:
                try:
                    file_path.unlink()
                    logger.info(f"Removed {filename}")
                    stats["removed"] += 1
                except OSError as e:
                    logger.error(f"Cannot remove {file_path}: {e}")
                continue
            
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                logger.debug(f"Skipped (unsupported extension): {file_path.name}")
                stats["skipped"] += 1
                continue
            
            if process_file(file_path, output_root):
                stats["processed"] += 1
            else:
                stats["skipped"] += 1

    logger.info(f"Complete. Processed: {stats['processed']}, Skipped: {stats['skipped']}, Removed: {stats['removed']}")
    print(f"\nLog: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
