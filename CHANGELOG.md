# Changelog

All notable changes to Bad_Usb_Forge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - Unreleased

### Added
- `gui/` — local 3-column desktop GUI (Flask backend + vanilla JS/HTML frontend), `badusb-gui` console script (`pip install -e ".[gui]"`). Source (drag & drop a folder, browse, or clone by URL) → Classified (one-click classify) → Ready to flash (per-field enrichment form, with the Discord webhook guide inline and server-side URL validation). Runs on 127.0.0.1 only; verified end-to-end in a real browser session (clone → classify → enrich-scan → validation-reject → apply → real file injection confirmed on disk), plus a dedicated `tests/test_gui_app.py` suite (path-traversal rejection, full flow, reset).

## [1.1.0] - 2026-08-10

### Added
- `badusb_pipeline.py` — unified one-command entry point chaining classification and enrichment into a single clean output folder.
- `Bad_USB_Classifier/payload_setup_agent.py` — semi-interactive enrichment agent: detects placeholders (Discord webhook, Telegram bot/chat id, attacker IP/port, email, bracket placeholders), guides Discord webhook creation from scratch, validates URL format before accepting it.
- `Bad_USB_Classifier/discover_repos.py` — searches GitHub's search API and Reddit's public JSON search for new BadUSB source repos not yet in `url.txt`; dry-run by default, `--write` to append reviewed candidates.
- `Bad_USB_Classifier/ollama_agent.py` — shared Ollama tool-calling wrapper used by the enrichment agent; every model suggestion is re-verified against the actual file content before being trusted.
- Cross-platform automated installers: `scripts/install.sh` (macOS/Linux/Unix) and `scripts/install.ps1` (Windows), both self-contained under `~/.auto-flipper-tools`, no sudo/admin required.
- `pyproject.toml` packaging — `pip install .` now works, with `badusb-pipeline`, `badusb-classify`, `badusb-setup-agent`, `badusb-discover` console scripts.
- `.github/workflows/release.yml` — tag-triggered release pipeline: tests on 3 OS → build sdist/wheel → build standalone PyInstaller executables per OS → publish to GitHub Releases, gated on tests passing.
- `.github/workflows/tests.yml` — new `install-script` job validating the installers for real on ubuntu/macos/windows runners.
- `tests/` — first unit test suite for this project (14 tests covering the classifier and enrichment agent).
- `--no-ollama` / `--model` flags on `classify_badusb.py`, wired through the whole pipeline, so classification can run fully offline and deterministically.
- `classify_badusb.py --urls` now clones/pulls sources via `git` instead of downloading GitHub zip archives.

### Fixed
- `pytest` in CI no longer silently passes on zero collected tests (removed a masking `|| true`).
- `discover_repos.py`: `urllib.request.quote` (doesn't exist) → `urllib.parse.quote`, which would have crashed at runtime.
- `classify_badusb.py`: majority-vote winner selection (`max(votes, key=votes.get)`) now correctly typed.
- Bandit-flagged missing URL-scheme validation before `urlopen()` in `discover_repos.py`.

### Changed
- Repository history was rewritten (`git filter-repo`) to remove a local username/hostname that had leaked into 7 commits' author metadata and into now-deleted setup docs — see the repo's commit history for details.

## [1.0.0] - 2024-01-15

### Added

#### BadUSB Classifier
- Initial release with core classification engine
- Ducky Script validation using keyword detection
- Multi-level classification system: pattern-based detection (fast), AI-powered classification via Ollama (accurate), automatic fallback to unassigned category
- Support for 24 BadUSB payload categories
- Recursive directory processing
- File collision handling with auto-rename
- Comprehensive logging with statistics

#### File Support
- `.txt` — text-based scripts
- `.duck` — Ducky Script format
- `.ds` — Ducky Script variant
