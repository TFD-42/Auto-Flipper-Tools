# Auto-Flipper-Tools Wiki

Classify and enrich BadUSB/Ducky Script payloads for Flipper Zero — one command or one click, any source folder, local-first with optional AI.

## Start here

| Page | What's in it |
|---|---|
| [Installation](Installation) | One-line installers (macOS/Linux/Windows), standalone executables, manual install from source |
| [Usage — CLI](Usage-CLI) | `badusb_pipeline.py` and the individual tools, real command examples |
| [Usage — GUI](GUI-Guide) | The 3-column desktop interface: drag & drop / clone → classify → enrich |
| [Architecture](Architecture) | How classification and enrichment actually work internally |
| [Source Repositories & Credits](Source-Repositories) | The ~79 community repos this project can classify, credited by author |
| [FAQ](FAQ) | Common questions |
| [Troubleshooting](Troubleshooting) | Fixes for the errors you're most likely to hit |
| [Contributing](Contributing) | How to contribute, including the BadUSB-specific ethics checklist |

## What this project actually does

Three tools, usable standalone or chained together:

1. **Classifier** (`Bad_USB_Classifier/classify_badusb.py`) — recursive, dedup-aware, two-pass classification of Ducky Script payloads into 24 topic categories, using keyword matching with an optional Ollama fallback.
2. **Enrichment agent** (`Bad_USB_Classifier/payload_setup_agent.py`) — detects placeholders a payload needs before it'll actually work (Discord webhook, attacker IP, Telegram token...) and walks you through filling them in, including a from-scratch Discord webhook setup guide.
3. **Repo discovery** (`Bad_USB_Classifier/discover_repos.py`) — searches GitHub/Reddit for new BadUSB source repos not yet tracked in `url.txt`.

`badusb_pipeline.py` chains classification + enrichment into one command. The [GUI](GUI-Guide) does the same thing visually, in three columns.

## Project links

- [Main README](https://github.com/TFD-42/Auto-Flipper-Tools#readme)
- [Issues](https://github.com/TFD-42/Auto-Flipper-Tools/issues)
- [Releases](https://github.com/TFD-42/Auto-Flipper-Tools/releases)
- [CI status](https://github.com/TFD-42/Auto-Flipper-Tools/actions)

## Scope note

This project is for **authorized security testing and research only**. It classifies and organizes third-party community payloads — it does not claim authorship of any payload it processes. See [Source Repositories & Credits](Source-Repositories) and [ETHICS.md](https://github.com/TFD-42/Auto-Flipper-Tools/blob/main/ETHICS.md).
