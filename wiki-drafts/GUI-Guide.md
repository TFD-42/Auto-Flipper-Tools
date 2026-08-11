# Usage — Desktop GUI

A local, 3-column web interface for the whole pipeline — no terminal needed once installed.

## Launch it

```bash
pip install -e ".[gui]"
badusb-gui
```

Opens automatically at `http://127.0.0.1:5115`. It's a local Flask server bound to `127.0.0.1` only — nothing leaves your machine except what you explicitly trigger (a git clone, the repo-discovery step, or Ollama).

## The three columns

### 1. Source

Get scripts into the workspace three ways:
- **Drag & drop** a folder directly from Finder/Explorer onto the drop zone (reads the folder recursively, including subfolders).
- **Choose a folder** via the "Choisir un dossier…" button (native OS folder picker).
- **Clone a single repo** by pasting a GitHub URL and clicking "Cloner".
- **Clone a whole list** — pick a `.txt` file of URLs (one per line, `#` for comments) and click "Cloner la liste". If you don't pick a file, it defaults to the bundled `Bad_USB_Classifier/url.txt` (shown live as "Par défaut : url.txt (79 sources)").

### 2. Classé (Classified)

One click ("Classer →") runs the same classifier as the CLI — pattern-based, with an optional "Ollama en secours" checkbox for the AI fallback. Results appear as a live folder tree, organized by theme.

### 3. Prêt à flasher (Ready to flash)

Click "Analyser →" to scan the classified output for placeholders. For each field type found (Discord webhook, attacker IP, etc.) you get:
- a text input to fill in the value (used for every file that needs that field),
- for Discord webhooks specifically, an expandable step-by-step guide for creating one from scratch, and server-side URL format validation (an invalid URL is rejected with a clear error, nothing gets silently written),
- an expandable list of exactly which files that field affects.

Click "Appliquer et finaliser →" to write the enriched scripts into the final `ready/` folder — that's what you copy onto the Flipper Zero's SD card, in `badusb/`.

Each column has a "Vider" button to reset just that stage.

## Where files live

The GUI keeps its own workspace at `~/.auto-flipper-tools/gui-workspace/{source,organized,ready}/` — separate from wherever you keep your actual project files, and never committed to any git repo.

## Verified behavior

This flow — clone a real repo with known Discord webhook placeholders → classify → scan → reject an invalid webhook URL → accept a valid one → confirm the real file content changed on disk — has been tested end-to-end in a real browser session, not just via unit tests. See `tests/test_gui_app.py` for the automated coverage (path-traversal rejection on uploads, full classify → scan → apply flow, URL-list default fallback).
