# Auto-Flipper-Tools

> Classify and enrich BadUSB/Ducky Script payloads for Flipper Zero — one command, any source folder, local-first with optional AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/TFD-42/Auto-Flipper-Tools/actions/workflows/tests.yml/badge.svg)](https://github.com/TFD-42/Auto-Flipper-Tools/actions/workflows/tests.yml)
[![Security Scan](https://github.com/TFD-42/Auto-Flipper-Tools/actions/workflows/security-scan.yml/badge.svg)](https://github.com/TFD-42/Auto-Flipper-Tools/actions/workflows/security-scan.yml)
[![Cross-Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](#quick-start)
[![Local-first](https://img.shields.io/badge/AI-optional%20%26%20local%20(Ollama)-informational.svg)](#dependencies)

## Overview

<img width="1680" height="720" alt="github_banner_42" src="https://github.com/user-attachments/assets/682f0c0e-cedb-451e-bc45-1c0158a8fccf" />

Auto-Flipper-Tools is an automation toolkit for security professionals, researchers, and enthusiasts working with Flipper Zero devices. Its core job: take a messy folder of BadUSB/Ducky Script payloads — your own, or pulled from any of the ~90 community source repos it already knows about — and turn it into a clean, categorized, ready-to-flash folder, filling in the placeholders (Discord webhook, attacker IP, Telegram token...) that individual scripts need before they'll actually work.

![Capture d’écran 2026-08-11 à 19 19 12](https://github.com/user-attachments/assets/8ee29e95-57dd-4322-b0f2-985b65caf7b9)

### Key Use Cases

- 🔍 **BadUSB Payload Classification** — automatically categorize and organize BadUSB scripts into 24 topic-based folders
- 🤖 **AI-Powered Analysis** — optional Ollama integration for classification and placeholder detection; the tool works fully offline without it
- 🧩 **Semi-Interactive Enrichment** — detects scripts that need a webhook/IP/token and walks you through filling them in (including a from-scratch Discord webhook setup guide)
- 📊 **Batch Processing** — classify and enrich hundreds of payloads in one pass
- 🔄 **Cross-Platform** — one-line automated install for macOS, Linux, and Windows, plus standalone executables that need no Python at all

## Quick Start

### Automated Install (macOS / Linux / Unix)

```bash
curl -fsSL https://raw.githubusercontent.com/TFD-42/Auto-Flipper-Tools/main/scripts/install.sh | bash
```

### Automated Install (Windows, PowerShell)

```powershell
irm https://raw.githubusercontent.com/TFD-42/Auto-Flipper-Tools/main/scripts/install.ps1 | iex
```

Both scripts detect your OS, verify Python 3.8+, create an isolated venv
under `~/.auto-flipper-tools` (`%USERPROFILE%\.auto-flipper-tools` on
Windows), install the package, and add `badusb-pipeline` (+ the other CLIs)
to your PATH. Nothing is installed with `sudo`/admin rights.

### Standalone Executables (no Python required)

Download the executable for your OS from the
[latest release](https://github.com/TFD-42/Auto-Flipper-Tools/releases/latest):
`badusb-pipeline-linux`, `badusb-pipeline-macos`, or `badusb-pipeline-windows.exe`.

### Manual Install (from source)

```bash
git clone https://github.com/TFD-42/Auto-Flipper-Tools.git
cd Auto-Flipper-Tools
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Dependencies

- Python 3.8+
- Ollama (**optional** — only used as a fallback for classification/placeholder-detection when keyword matching doesn't find an answer; `--no-ollama` runs the whole pipeline with zero network calls)

### Basic Usage

```bash
# One-shot: classify + enrich any folder of BadUSB scripts
python3 badusb_pipeline.py ./payloads

# Or step by step:
python Bad_USB_Classifier/classify_badusb.py ./payloads --no-ollama
python Bad_USB_Classifier/payload_setup_agent.py ./payloads_organized

# Refresh the bundled source corpus (git clone/pull from url.txt)
python Bad_USB_Classifier/classify_badusb.py --urls Bad_USB_Classifier/url.txt

# Find new sources not yet in url.txt (dry-run by default)
python Bad_USB_Classifier/discover_repos.py
```

## Core Components

### `badusb_pipeline.py` — Unified Entry Point

Point any folder of BadUSB scripts (`.txt`/`.duck`/`.ds`, loose or nested, any
structure) at this script and it will classify them by theme and enrich the
ones that need a value before you copy the result onto your Flipper Zero's
SD card. Chains the two tools below into one clean output folder — no manual
two-step process required.

### `Bad_USB_Classifier/`

- **`classify_badusb.py`** — recursive, dedup-aware, two-pass classifier. Pattern-based Ducky Script validation, keyword topic matching, optional Ollama fallback (24 categories), automatic collision handling, comprehensive logging.
- **`payload_setup_agent.py`** — semi-interactive enrichment agent: regex-detects placeholders (Discord webhook, Telegram bot/chat id, attacker IP/port, email, `[bracket]` placeholders), guides you through creating a Discord webhook from scratch if you don't have one, validates the URL format, and writes the configured scripts back.
- **`discover_repos.py`** — searches GitHub's search API and Reddit's public JSON search for new BadUSB payload source repos not yet in `url.txt`; never clones anything itself, only proposes candidates for you to review.
- **`ollama_agent.py`** — shared tool-calling wrapper for the two agents above; every AI suggestion is verified against the actual file content before being trusted, never blindly applied.

[📖 Full Documentation](./Bad_USB_Classifier/README.md)

### `gui/` — 3-Column Desktop GUI

A local web-based interface for the whole pipeline — no terminal needed once
installed. Three columns: **Source** (drag & drop a folder, browse for one,
or clone a repo by URL) → **Classé** (one click to classify) → **Prêt à
flasher** (detects placeholders, shows a form per field — with the Discord
webhook guide inline — and writes the enriched, ready-to-copy scripts).

```bash
pip install -e ".[gui]"
badusb-gui
```

Opens automatically at `http://127.0.0.1:5115`. Runs entirely on localhost —
nothing leaves your machine except what you explicitly trigger (a git clone,
the discover step, or Ollama).

## Architecture & Roadmap

### Current Tools
- ✅ BadUSB Classifier — Ducky Script analysis and categorization
- ✅ Payload Setup Agent — semi-interactive enrichment before flashing
- ✅ Repo Discovery — GitHub/Reddit search for new payload sources
- ✅ Unified pipeline (`badusb_pipeline.py`) + automated cross-platform installers + standalone executables
- ✅ 3-column desktop GUI (`gui/`) — drag & drop / clone → classify → enrich, no terminal required

### Planned Tools
- 🔜 Auto-Build System — pre-build and validation for scripts before classification
- 🔜 App Fuzzer Automation — automated app fuzzing payload generation
- 🔜 Script Validator — enhanced validation across multiple script types
- 🔜 API Integrations — Flipper Zero device API automation

## Directory Structure

```
Auto-Flipper-Tools/
├── badusb_pipeline.py          # unified entry point: classify + enrich
├── pyproject.toml              # pip-installable package (console_scripts)
├── Bad_USB_Classifier/
│   ├── classify_badusb.py      # classification (keyword + optional Ollama)
│   ├── payload_setup_agent.py  # enrichment (webhooks, IPs, tokens...)
│   ├── discover_repos.py       # find new source repos (GitHub/Reddit)
│   ├── ollama_agent.py         # shared Ollama tool-calling wrapper
│   ├── requirements.txt
│   ├── url.txt                 # ~90 known community source repos
│   └── README.md
├── scripts/
│   ├── install.sh               # automated installer: macOS/Linux/Unix
│   └── install.ps1              # automated installer: Windows
├── gui/
│   ├── app.py                   # Flask backend (badusb-gui entry point)
│   ├── templates/index.html     # 3-column UI
│   └── static/                  # app.js + style.css
├── tests/                       # pytest unit tests
├── docs/
│   ├── INSTALLATION.md
│   ├── USAGE.md
│   └── ARCHITECTURE.md
├── .github/
│   └── workflows/
│       ├── tests.yml            # pytest + lint + type-check, 3-OS matrix
│       ├── security-scan.yml    # secret scan, bandit, CodeQL, dependency check
│       └── release.yml          # sdist/wheel + per-OS executables → GitHub Release
├── .gitignore
├── README.md
├── LICENSE
└── requirements.txt
```

## Security & Privacy

### Security Features

- ✅ **Secret Scanning** — GitHub advanced security scanning + TruffleHog in CI
- ✅ **Static Analysis** — bandit + CodeQL run on every push
- ✅ **Input Validation** — placeholder detection never blindly trusts AI suggestions; every value is re-verified against the actual file content before use
- ✅ **No Telemetry** — nothing phones home; the only outbound calls are the ones you explicitly trigger (`--urls`, `discover_repos.py`, or Ollama)
- ✅ **Error Handling** — errors are caught per-file so one malformed script doesn't abort a batch run

### Security Scanning

This repository uses GitHub's built-in security features plus a dedicated CI workflow:
- Secret scanning (GitHub + TruffleHog) to prevent credential leaks
- CodeQL analysis for code quality
- Bandit static analysis and `safety`/dependency vulnerability checks
- Dependabot for dependency vulnerability scanning

### Responsible Disclosure

If you discover a security vulnerability, please email security concerns privately rather than opening a public issue — see [SECURITY.md](SECURITY.md).

## Contributing

Contributions are welcome and encouraged! Whether you're fixing bugs, adding features, improving documentation, or enhancing security — all help is appreciated. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide, including the ethical obligations specific to BadUSB payload contributions.

### Development Setup

```bash
git clone https://github.com/TFD-42/Auto-Flipper-Tools.git
cd Auto-Flipper-Tools
python -m venv venv
source venv/bin/activate

# Installs the package + all dev tools (pytest, black, isort, flake8, mypy, bandit)
pip install -e ".[dev]"

pytest                                  # run tests
black . && isort .                      # format
flake8 Bad_USB_Classifier/ --select=E9,F63,F7,F82   # critical lint
mypy Bad_USB_Classifier/ --ignore-missing-imports    # type-check
```

## Performance

Measured on this repo's own test run (Apple Silicon Mac, `--no-ollama`
keyword-only mode, a real 959-file corpus cloned from 4 community source
repos in `url.txt`):

| Metric | Result |
|--------|--------|
| Files processed (classify + enrich) | 959 files in 1.83s (~524 files/sec) |
| Ducky scripts identified | 369 (340 ready-to-use, 29 needing a value filled in) |

With Ollama enabled as a fallback for files keyword-matching can't classify,
throughput drops to roughly one Ollama call's latency per unmatched file
(model- and hardware-dependent) — `--no-ollama` is the fast path when you
just need bulk keyword-based sorting.

## References & Attribution

### Origins & Inspiration

This toolkit builds upon and references:

- **[Flipper Zero](https://flipperzero.one/)** — multi-tool platform for security professionals
- **[BadUSB Research](https://adamcaudill.com/2014/10/17/badusb/)** — original BadUSB concept and research
- **[Ducky Script](https://docs.hak5.org/hak5-usb-rubber-ducky/)** — official USB Rubber Ducky documentation
- **[Hak5 USB Rubber Ducky](https://hak5.org/products/usb-rubber-ducky)** — original Ducky Script implementation
- **Flipper Zero Community** — BadUSB payload research and development

No evidence of this codebase being forked from or reusing another project's
source code was found (checked git remotes, commit history, and license
headers) — the classifier/enrichment/discovery tools here are original
implementations.

### Related Projects

- [Flipper Zero Firmware](https://github.com/flipperdevices/flipperzero-firmware)
- [USB Rubber Ducky Payload Repository](https://github.com/hak5/usb-rubber-ducky)
- [Flipper Zero Bad USB Database](https://github.com/UberGimbal/Flipper-Bad-USB)

## FAQ

**Q: Do I need Ollama for this tool?**
A: No. `--no-ollama` runs the full classify + enrich pipeline with pattern/keyword matching alone and zero network calls. Ollama is an optional fallback for files keyword matching can't confidently classify.

**Q: Is this tool legal to use?**
A: Yes, but only for authorized security testing and research. Always obtain proper authorization before using any payload against a system you don't own or don't have explicit permission to test.

**Q: What script formats are supported?**
A: Ducky Script (`.txt`, `.duck`, `.ds`).

**Q: Can I use this commercially?**
A: Yes, under the MIT license. Please include license attribution.

## Troubleshooting

### Ollama Not Found
```
Error: Ollama not found - ensure it's installed and in PATH
```
**Solution**: Install Ollama from https://ollama.ai, or just add `--no-ollama` to skip AI entirely.

### Timeout During Classification
```
Error: Ollama request timed out
```
**Solution**: This only affects the optional Ollama fallback path — re-run with `--no-ollama` for the deterministic keyword-only path, or increase `OLLAMA_TIMEOUT_FAST`/`OLLAMA_TIMEOUT_DEEP` in `classify_badusb.py`.

### Permission Denied
```
Error: Cannot read file or Cannot move file
```
**Solution**: Check file permissions; ensure write access to the output directory.

## Roadmap

- [ ] Additional classification models
- [ ] Web interface for classification
- [ ] Support for additional script formats
- [ ] Community payload database
- [ ] Custom rule engine

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

## Source Repositories & Credits

This project classifies and organizes BadUSB payloads sourced from the community repositories below (**79 repos**, kept in sync with [`Bad_USB_Classifier/url.txt`](Bad_USB_Classifier/url.txt) — the authoritative list, regenerate this section with `python3 scripts/generate_credits_badges.py`). **This project does not claim authorship of any third-party payload it classifies; full credit and copyright remain with each original author.** Star counts are live (shields.io dynamic badges), not hardcoded.

### BadUSB Payload Collections

- [![I-Am-Jakoby/Flipper-Zero-BadUSB stars](https://img.shields.io/github/stars/I-Am-Jakoby/Flipper-Zero-BadUSB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/I-Am-Jakoby/Flipper-Zero-BadUSB) [I-Am-Jakoby/Flipper-Zero-BadUSB](https://github.com/I-Am-Jakoby/Flipper-Zero-BadUSB)
- [![aleff-github/my-flipper-shits stars](https://img.shields.io/github/stars/aleff-github/my-flipper-shits?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/aleff-github/my-flipper-shits) [aleff-github/my-flipper-shits](https://github.com/aleff-github/my-flipper-shits)
- [![FalsePhilosopher/badusb stars](https://img.shields.io/github/stars/FalsePhilosopher/badusb?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/FalsePhilosopher/badusb) [FalsePhilosopher/badusb](https://github.com/FalsePhilosopher/badusb)
- [![Kavitate/FlipperZeroBadUSB stars](https://img.shields.io/github/stars/Kavitate/FlipperZeroBadUSB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Kavitate/FlipperZeroBadUSB) [Kavitate/FlipperZeroBadUSB](https://github.com/Kavitate/FlipperZeroBadUSB)
- [![SeenKid/flipper-zero-bad-usb stars](https://img.shields.io/github/stars/SeenKid/flipper-zero-bad-usb?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/SeenKid/flipper-zero-bad-usb) [SeenKid/flipper-zero-bad-usb](https://github.com/SeenKid/flipper-zero-bad-usb)
- [![RamtinHaf/Flipper-Zero-Bad-USB stars](https://img.shields.io/github/stars/RamtinHaf/Flipper-Zero-Bad-USB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/RamtinHaf/Flipper-Zero-Bad-USB) [RamtinHaf/Flipper-Zero-Bad-USB](https://github.com/RamtinHaf/Flipper-Zero-Bad-USB)
- [![grugnoymeme/flipperzero-badUSB stars](https://img.shields.io/github/stars/grugnoymeme/flipperzero-badUSB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/grugnoymeme/flipperzero-badUSB) [grugnoymeme/flipperzero-badUSB](https://github.com/grugnoymeme/flipperzero-badUSB)
- [![DoobTheGoober/BADUSB stars](https://img.shields.io/github/stars/DoobTheGoober/BADUSB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/DoobTheGoober/BADUSB) [DoobTheGoober/BADUSB](https://github.com/DoobTheGoober/BADUSB)
- [![anste5/BADUSBrepo stars](https://img.shields.io/github/stars/anste5/BADUSBrepo?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/anste5/BADUSBrepo) [anste5/BADUSBrepo](https://github.com/anste5/BADUSBrepo)
- [![anste5/BadUSB-badkb stars](https://img.shields.io/github/stars/anste5/BadUSB-badkb?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/anste5/BadUSB-badkb) [anste5/BadUSB-badkb](https://github.com/anste5/BadUSB-badkb)
- [![hooker01/FlipperZero-Payloads stars](https://img.shields.io/github/stars/hooker01/FlipperZero-Payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/hooker01/FlipperZero-Payloads) [hooker01/FlipperZero-Payloads](https://github.com/hooker01/FlipperZero-Payloads)
- [![dagnazty/Flipper_Zero_Bad_USB stars](https://img.shields.io/github/stars/dagnazty/Flipper_Zero_Bad_USB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/dagnazty/Flipper_Zero_Bad_USB) [dagnazty/Flipper_Zero_Bad_USB](https://github.com/dagnazty/Flipper_Zero_Bad_USB)
- [![r3dsh3rl0ck/Flipper-Zero-Bad-USB-Payloads stars](https://img.shields.io/github/stars/r3dsh3rl0ck/Flipper-Zero-Bad-USB-Payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/r3dsh3rl0ck/Flipper-Zero-Bad-USB-Payloads) [r3dsh3rl0ck/Flipper-Zero-Bad-USB-Payloads](https://github.com/r3dsh3rl0ck/Flipper-Zero-Bad-USB-Payloads)
- [![ClumsyLulz/Flipper_Zero_Badusb_hack5_payloads stars](https://img.shields.io/github/stars/ClumsyLulz/Flipper_Zero_Badusb_hack5_payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/ClumsyLulz/Flipper_Zero_Badusb_hack5_payloads) [ClumsyLulz/Flipper_Zero_Badusb_hack5_payloads](https://github.com/ClumsyLulz/Flipper_Zero_Badusb_hack5_payloads)
- [![narstybits/MacOS-DuckyScripts stars](https://img.shields.io/github/stars/narstybits/MacOS-DuckyScripts?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/narstybits/MacOS-DuckyScripts) [narstybits/MacOS-DuckyScripts](https://github.com/narstybits/MacOS-DuckyScripts)
- [![zer0dayf/Ghost-Audit stars](https://img.shields.io/github/stars/zer0dayf/Ghost-Audit?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/zer0dayf/Ghost-Audit) [zer0dayf/Ghost-Audit](https://github.com/zer0dayf/Ghost-Audit)
- [![Offensive-Wireless/Flipper-Zero stars](https://img.shields.io/github/stars/Offensive-Wireless/Flipper-Zero?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Offensive-Wireless/Flipper-Zero) [Offensive-Wireless/Flipper-Zero](https://github.com/Offensive-Wireless/Flipper-Zero)

### Flipper Zero Tools & Utilities

- [![Zarcolio/flipperzero stars](https://img.shields.io/github/stars/Zarcolio/flipperzero?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Zarcolio/flipperzero) [Zarcolio/flipperzero](https://github.com/Zarcolio/flipperzero)
- [![descambiado/flipper-purple-team stars](https://img.shields.io/github/stars/descambiado/flipper-purple-team?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/descambiado/flipper-purple-team) [descambiado/flipper-purple-team](https://github.com/descambiado/flipper-purple-team)
- [![D4rkDr4gon/flipper-zero-Utils stars](https://img.shields.io/github/stars/D4rkDr4gon/flipper-zero-Utils?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/D4rkDr4gon/flipper-zero-Utils) [D4rkDr4gon/flipper-zero-Utils](https://github.com/D4rkDr4gon/flipper-zero-Utils)
- [![Angrido/Flipper-WiFi-Grabber stars](https://img.shields.io/github/stars/Angrido/Flipper-WiFi-Grabber?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Angrido/Flipper-WiFi-Grabber) [Angrido/Flipper-WiFi-Grabber](https://github.com/Angrido/Flipper-WiFi-Grabber)
- [![gam3r999/Flipper-Zero-Android stars](https://img.shields.io/github/stars/gam3r999/Flipper-Zero-Android?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/gam3r999/Flipper-Zero-Android) [gam3r999/Flipper-Zero-Android](https://github.com/gam3r999/Flipper-Zero-Android)
- [![gam3r999/Flipper-Zero-iOS stars](https://img.shields.io/github/stars/gam3r999/Flipper-Zero-iOS?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/gam3r999/Flipper-Zero-iOS) [gam3r999/Flipper-Zero-iOS](https://github.com/gam3r999/Flipper-Zero-iOS)
- [![heeeyflo/flipperzero-pin-bypass stars](https://img.shields.io/github/stars/heeeyflo/flipperzero-pin-bypass?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/heeeyflo/flipperzero-pin-bypass) [heeeyflo/flipperzero-pin-bypass](https://github.com/heeeyflo/flipperzero-pin-bypass)

### Awesome Lists & Curated Collections

- [![djsime1/awesome-flipperzero stars](https://img.shields.io/github/stars/djsime1/awesome-flipperzero?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/djsime1/awesome-flipperzero) [djsime1/awesome-flipperzero](https://github.com/djsime1/awesome-flipperzero)
- [![anasancho/awesome-flipperzero stars](https://img.shields.io/github/stars/anasancho/awesome-flipperzero?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/anasancho/awesome-flipperzero) [anasancho/awesome-flipperzero](https://github.com/anasancho/awesome-flipperzero)
- [![RogueMaster/awesome-flipperzero-withModules stars](https://img.shields.io/github/stars/RogueMaster/awesome-flipperzero-withModules?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/RogueMaster/awesome-flipperzero-withModules) [RogueMaster/awesome-flipperzero-withModules](https://github.com/RogueMaster/awesome-flipperzero-withModules)

### Asset Databases (IR, Sub-GHz, NFC)

- [![UberGuidoZ/Flipper stars](https://img.shields.io/github/stars/UberGuidoZ/Flipper?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/UberGuidoZ/Flipper) [UberGuidoZ/Flipper](https://github.com/UberGuidoZ/Flipper)
- [![UberGuidoZ/Flipper-IRDB stars](https://img.shields.io/github/stars/UberGuidoZ/Flipper-IRDB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/UberGuidoZ/Flipper-IRDB) [UberGuidoZ/Flipper-IRDB](https://github.com/UberGuidoZ/Flipper-IRDB)
- [![Zero-Sploit/FlipperZero-Subghz-DB stars](https://img.shields.io/github/stars/Zero-Sploit/FlipperZero-Subghz-DB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Zero-Sploit/FlipperZero-Subghz-DB) [Zero-Sploit/FlipperZero-Subghz-DB](https://github.com/Zero-Sploit/FlipperZero-Subghz-DB)

### Plugin Collections

- [![xMasterX/all-the-plugins stars](https://img.shields.io/github/stars/xMasterX/all-the-plugins?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/xMasterX/all-the-plugins) [xMasterX/all-the-plugins](https://github.com/xMasterX/all-the-plugins)
- [![xMasterX/flipperzero-good-faps stars](https://img.shields.io/github/stars/xMasterX/flipperzero-good-faps?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/xMasterX/flipperzero-good-faps) [xMasterX/flipperzero-good-faps](https://github.com/xMasterX/flipperzero-good-faps)

### Individual Apps

- [![honeer/flipper-base stars](https://img.shields.io/github/stars/honeer/flipper-base?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/honeer/flipper-base) [honeer/flipper-base](https://github.com/honeer/flipper-base)
- [![SYOP200/Flipper-Zero-Downloads stars](https://img.shields.io/github/stars/SYOP200/Flipper-Zero-Downloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/SYOP200/Flipper-Zero-Downloads) [SYOP200/Flipper-Zero-Downloads](https://github.com/SYOP200/Flipper-Zero-Downloads)
- [![i12bp8/TagTinker stars](https://img.shields.io/github/stars/i12bp8/TagTinker?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/i12bp8/TagTinker) [i12bp8/TagTinker](https://github.com/i12bp8/TagTinker)
- [![Clawzman/Flipper_ListEM stars](https://img.shields.io/github/stars/Clawzman/Flipper_ListEM?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Clawzman/Flipper_ListEM) [Clawzman/Flipper_ListEM](https://github.com/Clawzman/Flipper_ListEM)
- [![jblanked/FlipLibrary stars](https://img.shields.io/github/stars/jblanked/FlipLibrary?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/jblanked/FlipLibrary) [jblanked/FlipLibrary](https://github.com/jblanked/FlipLibrary)
- [![x0452950/flipper-nfc-toolkit stars](https://img.shields.io/github/stars/x0452950/flipper-nfc-toolkit?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/x0452950/flipper-nfc-toolkit) [x0452950/flipper-nfc-toolkit](https://github.com/x0452950/flipper-nfc-toolkit)
- [![TFD-42/Mhz_Localiser stars](https://img.shields.io/github/stars/TFD-42/Mhz_Localiser?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/TFD-42/Mhz_Localiser) [TFD-42/Mhz_Localiser](https://github.com/TFD-42/Mhz_Localiser)

### Flipper Zero BadUSB / BadKB (new)

- [![SHUR1K-N/Flipper-Zero-BadKB-Files stars](https://img.shields.io/github/stars/SHUR1K-N/Flipper-Zero-BadKB-Files?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/SHUR1K-N/Flipper-Zero-BadKB-Files) [SHUR1K-N/Flipper-Zero-BadKB-Files](https://github.com/SHUR1K-N/Flipper-Zero-BadKB-Files)
- [![Mr-Proxy-source/BadUSB-Payloads stars](https://img.shields.io/github/stars/Mr-Proxy-source/BadUSB-Payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Mr-Proxy-source/BadUSB-Payloads) [Mr-Proxy-source/BadUSB-Payloads](https://github.com/Mr-Proxy-source/BadUSB-Payloads)
- [![bst04/payloads_flipperZero stars](https://img.shields.io/github/stars/bst04/payloads_flipperZero?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/bst04/payloads_flipperZero) [bst04/payloads_flipperZero](https://github.com/bst04/payloads_flipperZero)
- [![desktopsetup/BadOS stars](https://img.shields.io/github/stars/desktopsetup/BadOS?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/desktopsetup/BadOS) [desktopsetup/BadOS](https://github.com/desktopsetup/BadOS)
- [![desktopsetup/BadDroid stars](https://img.shields.io/github/stars/desktopsetup/BadDroid?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/desktopsetup/BadDroid) [desktopsetup/BadDroid](https://github.com/desktopsetup/BadDroid)
- [![evilvodun/wifi_passwords stars](https://img.shields.io/github/stars/evilvodun/wifi_passwords?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/evilvodun/wifi_passwords) [evilvodun/wifi_passwords](https://github.com/evilvodun/wifi_passwords)
- [![TBJr/Flipper-payloads stars](https://img.shields.io/github/stars/TBJr/Flipper-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/TBJr/Flipper-payloads) [TBJr/Flipper-payloads](https://github.com/TBJr/Flipper-payloads)
- [![AgeOfMarcus/flipper_badkb_payloads stars](https://img.shields.io/github/stars/AgeOfMarcus/flipper_badkb_payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/AgeOfMarcus/flipper_badkb_payloads) [AgeOfMarcus/flipper_badkb_payloads](https://github.com/AgeOfMarcus/flipper_badkb_payloads)
- [![MrzpUnkn/FlipperUsbExfil stars](https://img.shields.io/github/stars/MrzpUnkn/FlipperUsbExfil?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/MrzpUnkn/FlipperUsbExfil) [MrzpUnkn/FlipperUsbExfil](https://github.com/MrzpUnkn/FlipperUsbExfil)
- [![cgarey2014/BadUSB-Scripts stars](https://img.shields.io/github/stars/cgarey2014/BadUSB-Scripts?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/cgarey2014/BadUSB-Scripts) [cgarey2014/BadUSB-Scripts](https://github.com/cgarey2014/BadUSB-Scripts)
- [![graydav1/badkb-scripts stars](https://img.shields.io/github/stars/graydav1/badkb-scripts?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/graydav1/badkb-scripts) [graydav1/badkb-scripts](https://github.com/graydav1/badkb-scripts)
- [![avltree9798/macos_badkb_scripts stars](https://img.shields.io/github/stars/avltree9798/macos_badkb_scripts?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/avltree9798/macos_badkb_scripts) [avltree9798/macos_badkb_scripts](https://github.com/avltree9798/macos_badkb_scripts)
- [![emrahustundag/ghost-audit-mac stars](https://img.shields.io/github/stars/emrahustundag/ghost-audit-mac?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/emrahustundag/ghost-audit-mac) [emrahustundag/ghost-audit-mac](https://github.com/emrahustundag/ghost-audit-mac)

### Hak5 Official Payload Repos

- [![hak5/usbrubberducky-payloads stars](https://img.shields.io/github/stars/hak5/usbrubberducky-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/hak5/usbrubberducky-payloads) [hak5/usbrubberducky-payloads](https://github.com/hak5/usbrubberducky-payloads)
- [![hak5/bashbunny-payloads stars](https://img.shields.io/github/stars/hak5/bashbunny-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/hak5/bashbunny-payloads) [hak5/bashbunny-payloads](https://github.com/hak5/bashbunny-payloads)
- [![hak5/keycroc-payloads stars](https://img.shields.io/github/stars/hak5/keycroc-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/hak5/keycroc-payloads) [hak5/keycroc-payloads](https://github.com/hak5/keycroc-payloads)

### DuckyScript Payload Collections

- [![UndedInside/DuckyScriptPayloads stars](https://img.shields.io/github/stars/UndedInside/DuckyScriptPayloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/UndedInside/DuckyScriptPayloads) [UndedInside/DuckyScriptPayloads](https://github.com/UndedInside/DuckyScriptPayloads)
- [![h1dd3n3y3/BadUSB stars](https://img.shields.io/github/stars/h1dd3n3y3/BadUSB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/h1dd3n3y3/BadUSB) [h1dd3n3y3/BadUSB](https://github.com/h1dd3n3y3/BadUSB)
- [![OMG-Tech/DuckyScript-Payloads stars](https://img.shields.io/github/stars/OMG-Tech/DuckyScript-Payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/OMG-Tech/DuckyScript-Payloads) [OMG-Tech/DuckyScript-Payloads](https://github.com/OMG-Tech/DuckyScript-Payloads)
- [![cvbenur/ducky-scripts-and-payloads stars](https://img.shields.io/github/stars/cvbenur/ducky-scripts-and-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/cvbenur/ducky-scripts-and-payloads) [cvbenur/ducky-scripts-and-payloads](https://github.com/cvbenur/ducky-scripts-and-payloads)
- [![547y4m/Payloads-for-USB-Rubber-Ducky stars](https://img.shields.io/github/stars/547y4m/Payloads-for-USB-Rubber-Ducky?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/547y4m/Payloads-for-USB-Rubber-Ducky) [547y4m/Payloads-for-USB-Rubber-Ducky](https://github.com/547y4m/Payloads-for-USB-Rubber-Ducky)
- [![dsymbol/ducky-payloads stars](https://img.shields.io/github/stars/dsymbol/ducky-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/dsymbol/ducky-payloads) [dsymbol/ducky-payloads](https://github.com/dsymbol/ducky-payloads)
- [![kawaiipantsu/duckyscript-payloads stars](https://img.shields.io/github/stars/kawaiipantsu/duckyscript-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/kawaiipantsu/duckyscript-payloads) [kawaiipantsu/duckyscript-payloads](https://github.com/kawaiipantsu/duckyscript-payloads)
- [![xloudo/custom-rubberducky-payloads stars](https://img.shields.io/github/stars/xloudo/custom-rubberducky-payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/xloudo/custom-rubberducky-payloads) [xloudo/custom-rubberducky-payloads](https://github.com/xloudo/custom-rubberducky-payloads)
- [![crashwire1/Rubber-Ducky-Payloads stars](https://img.shields.io/github/stars/crashwire1/Rubber-Ducky-Payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/crashwire1/Rubber-Ducky-Payloads) [crashwire1/Rubber-Ducky-Payloads](https://github.com/crashwire1/Rubber-Ducky-Payloads)

### BadUSB Hardware Platforms & Tools

- [![SpacehuhnTech/WiFiDuck stars](https://img.shields.io/github/stars/SpacehuhnTech/WiFiDuck?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/SpacehuhnTech/WiFiDuck) [SpacehuhnTech/WiFiDuck](https://github.com/SpacehuhnTech/WiFiDuck)
- [![dbisu/pico-ducky stars](https://img.shields.io/github/stars/dbisu/pico-ducky?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/dbisu/pico-ducky) [dbisu/pico-ducky](https://github.com/dbisu/pico-ducky)
- [![CedArctic/DigiSpark-Scripts stars](https://img.shields.io/github/stars/CedArctic/DigiSpark-Scripts?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/CedArctic/DigiSpark-Scripts) [CedArctic/DigiSpark-Scripts](https://github.com/CedArctic/DigiSpark-Scripts)
- [![MTK911/Attiny85 stars](https://img.shields.io/github/stars/MTK911/Attiny85?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/MTK911/Attiny85) [MTK911/Attiny85](https://github.com/MTK911/Attiny85)
- [![mayankmetha/Rucky stars](https://img.shields.io/github/stars/mayankmetha/Rucky?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/mayankmetha/Rucky) [mayankmetha/Rucky](https://github.com/mayankmetha/Rucky)

### BadUSB Attack-Specific Repos

- [![AleksaMCode/WiFi-password-stealer stars](https://img.shields.io/github/stars/AleksaMCode/WiFi-password-stealer?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/AleksaMCode/WiFi-password-stealer) [AleksaMCode/WiFi-password-stealer](https://github.com/AleksaMCode/WiFi-password-stealer)
- [![alexfrancow/badusb_botnet stars](https://img.shields.io/github/stars/alexfrancow/badusb_botnet?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/alexfrancow/badusb_botnet) [alexfrancow/badusb_botnet](https://github.com/alexfrancow/badusb_botnet)
- [![0cool-design/BadUSB stars](https://img.shields.io/github/stars/0cool-design/BadUSB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/0cool-design/BadUSB) [0cool-design/BadUSB](https://github.com/0cool-design/BadUSB)
- [![p0lymatic/InfestUSB stars](https://img.shields.io/github/stars/p0lymatic/InfestUSB?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/p0lymatic/InfestUSB) [p0lymatic/InfestUSB](https://github.com/p0lymatic/InfestUSB)
- [![tenable/router_badusb stars](https://img.shields.io/github/stars/tenable/router_badusb?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/tenable/router_badusb) [tenable/router_badusb](https://github.com/tenable/router_badusb)

### Generators, Converters & Defence

- [![InfoSecREDD/REPG stars](https://img.shields.io/github/stars/InfoSecREDD/REPG?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/InfoSecREDD/REPG) [InfoSecREDD/REPG](https://github.com/InfoSecREDD/REPG)
- [![InfoSecREDD/REPG-Community-Payloads stars](https://img.shields.io/github/stars/InfoSecREDD/REPG-Community-Payloads?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/InfoSecREDD/REPG-Community-Payloads) [InfoSecREDD/REPG-Community-Payloads](https://github.com/InfoSecREDD/REPG-Community-Payloads)
- [![Dukweeno/Duckuino stars](https://img.shields.io/github/stars/Dukweeno/Duckuino?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/Dukweeno/Duckuino) [Dukweeno/Duckuino](https://github.com/Dukweeno/Duckuino)
- [![htr-tech/ducky stars](https://img.shields.io/github/stars/htr-tech/ducky?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/htr-tech/ducky) [htr-tech/ducky](https://github.com/htr-tech/ducky)
- [![cecio/USBvalve stars](https://img.shields.io/github/stars/cecio/USBvalve?style=flat-square&label=%E2%98%85&color=blue)](https://github.com/cecio/USBvalve) [cecio/USBvalve](https://github.com/cecio/USBvalve)

> **Want to add your repo?** Fork this project, add your URL to [`Bad_USB_Classifier/url.txt`](Bad_USB_Classifier/url.txt), and open a Pull Request!

## Disclaimer

This toolkit is intended for authorized security testing, research, and educational purposes only. Users are responsible for legal compliance and obtaining proper authorization before testing security systems.

---

**Made with tools for security professionals by the community**

If you find this useful, please star the repository!
