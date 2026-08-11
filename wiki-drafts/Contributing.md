# Contributing

Full guide lives in [CONTRIBUTING.md](https://github.com/TFD-42/Auto-Flipper-Tools/blob/main/CONTRIBUTING.md) — this page is a quick pointer, not a duplicate.

## Quick start for contributors

```bash
git clone https://github.com/TFD-42/Auto-Flipper-Tools.git
cd Auto-Flipper-Tools
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

pytest                                              # run the test suite
black . && isort .                                  # format
flake8 Bad_USB_Classifier/ gui/ --select=E9,F63,F7,F82  # critical lint
mypy Bad_USB_Classifier/ gui/app.py --ignore-missing-imports  # type-check
```

## Adding a payload classifier or automation script

BadUSB-specific ethical checklist (from CONTRIBUTING.md):
- No hardcoded malicious payloads targeting real, non-consented systems.
- No examples demonstrating real-world attacks on common devices without an explicit educational-use marker.
- Include a `--dry-run`/`--safe` option if your script could write keystrokes.
- Tested in a safe environment (VM / isolated machine) before submitting.

## Adding a new payload source repo

Add the URL to [`Bad_USB_Classifier/url.txt`](https://github.com/TFD-42/Auto-Flipper-Tools/blob/main/Bad_USB_Classifier/url.txt) (one per line, under the relevant `# === category ===` heading) and open a PR. If you have `scripts/generate_credits_badges.py` handy, run it to regenerate the README's credits section so your addition gets a badge and a backlink automatically.

## Code of Conduct

See [CODE_OF_CONDUCT.md](https://github.com/TFD-42/Auto-Flipper-Tools/blob/main/CODE_OF_CONDUCT.md) (Contributor Covenant 2.1).
