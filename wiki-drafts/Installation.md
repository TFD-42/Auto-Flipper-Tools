# Installation

## Automated install (recommended)

### macOS / Linux / Unix

```bash
curl -fsSL https://raw.githubusercontent.com/TFD-42/Bad_Usb_Forge/main/scripts/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/TFD-42/Bad_Usb_Forge/main/scripts/install.ps1 | iex
```

Both scripts:
- detect your OS and verify Python 3.8+ is available
- create an isolated venv under `~/.auto-flipper-tools` (`%USERPROFILE%\.auto-flipper-tools` on Windows)
- install the package and add `badusb-pipeline`, `badusb-classify`, `badusb-setup-agent`, `badusb-discover` to your PATH
- **never** use `sudo`/admin rights

They're validated on every push by CI across ubuntu/macos/windows (see the `Install script` job in [tests.yml](https://github.com/TFD-42/Bad_Usb_Forge/blob/main/.github/workflows/tests.yml)).

## Standalone executables (no Python required)

Download the executable for your OS from the [latest release](https://github.com/TFD-42/Bad_Usb_Forge/releases/latest):

- `badusb-pipeline-linux`
- `badusb-pipeline-macos`
- `badusb-pipeline-windows.exe`

These are built by the release pipeline with PyInstaller and cover the unified `badusb_pipeline.py` entry point only — for the other CLIs (`badusb-classify`, `badusb-setup-agent`, `badusb-discover`) or the [GUI](GUI-Guide), use the pip install instead.

## Manual install from source

```bash
git clone https://github.com/TFD-42/Bad_Usb_Forge.git
cd Bad_Usb_Forge
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e .
```

### Optional extras

```bash
pip install -e ".[gui]"    # 3-column desktop GUI (Flask)
pip install -e ".[dev]"    # pytest, black, isort, flake8, mypy, bandit
pip install -e ".[build]"  # pyinstaller, build — for producing your own executables
```

## Dependencies

- **Python 3.8+** — the only hard requirement.
- **Ollama** (optional) — only used as a fallback when keyword matching can't confidently classify a file or detect a placeholder. Every command supports `--no-ollama` to skip it entirely (fully offline, deterministic). Install from [ollama.ai](https://ollama.ai) if you want the fallback.
- **git** — required for `--urls`/`discover_repos.py` (clones community source repos) and for the GUI's "clone by URL" and "clone from URL list" features.

## Verify it worked

```bash
badusb-pipeline --help
```

or, from a manual install:

```bash
python badusb_pipeline.py --help
```
