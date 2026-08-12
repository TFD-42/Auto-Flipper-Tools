# Promotion & Production-Readiness Report — Bad_Usb_Forge

*Second pass, run with `+ wiki full`. Builds on the previous audit (still valid, see git history of this file); this update covers what changed since (the GUI, more tests/CI) and delivers full wiki content.*

Generated via `github-repo-promoter` skill audit (`scripts/repo_audit.py`, live GitHub data via authenticated `gh` CLI). All claims below trace to the audit JSON or a file read directly.

## 0. Secrets check

`secrets.scanned_files: 41`, `sensitive_filenames: []`, `possible_secrets: []` — **clean**. (A dedicated, deeper pass — full git history, not just the working tree — was also run separately this session via a secret-scanning skill; also clean. See that report for detail.)

## 1. Attribution & Provenance — unchanged, still Insufficient

No `upstream` remote, no provenance-mentioning commits, no earlier-dated copyright holder. 19 local commits now (up from 11), still no fork/reuse signal. Correctly no Acknowledgments-for-forking section added.

Content attribution (third-party payloads processed) is still handled correctly and completely — the README's credits section and the new `Source-Repositories.md` wiki page both state plainly this project doesn't claim authorship of what it classifies.

## 2. Production-Readiness — what changed since the last pass

| Item | Status | Note |
|---|---|---|
| Tests | ✅ improved | 3 test files now (was 2): `test_classify_badusb.py`, `test_payload_setup_agent.py`, `test_gui_app.py` |
| CI | ✅ | still `tests.yml` + `security-scan.yml` + `release.yml`, unchanged file count but the GUI's tests now run in the same matrix |
| Dependency pinning | ⚠️ unchanged | `requests>=2.32.0`, still an unpinned floor (documented reason: no fixed release exists yet for the one open CVE, per earlier session notes) |
| Community-health files | ✅ | `CODE_OF_CONDUCT.md`, `CHANGELOG.md` both now present (were missing last pass) |
| **Wiki** | ❌ → drafted this pass | `github.has_wiki: true` but no content exists yet in the repo. 8 pages drafted in `wiki-drafts/` — see §5 |
| **`docs/*.md` staleness** (new finding) | ⚠️ | `docs/USAGE.md` and `docs/ARCHITECTURE.md` predate the pipeline, enrichment agent, and GUI — some examples (manual output-path editing, a fabricated log-line format, GitLab CI snippet) no longer match the current tool. Not fixed in this pass (out of scope for a promotion audit to silently rewrite existing docs pages) but flagged, and the more accurate content now lives in the wiki drafts instead |
| **README internal inconsistency** (new finding, fixed) | ✅ fixed | The Roadmap section still listed "Web interface for classification" as planned, while the "Current Tools" section (added when the GUI shipped) already listed it as done. Removed the stale Roadmap line — this is the only direct edit made to `README.md` in this pass, everything else stays in `.suggested`/draft form |

## 3. SEO — a live-data finding you should know about

**Your GitHub topics currently include two entries that don't look intentional**: `automated` and `badini`, alongside the 12 solid ones from last pass. Neither was set by this tool (nothing in this session ran `gh repo edit`). `badini` in particular reads like a typo — possibly meant to be `badusb`-adjacent, or a duplicate/mis-paste. Worth checking `https://github.com/TFD-42/Bad_Usb_Forge` → Settings → Topics and removing it if it wasn't intentional.

Suggested topic additions from last pass (`ollama`, `cli`, `cross-platform`) are still worth adding — the GUI addition this session makes `cli` slightly less exclusively true (there's now a real GUI too), so consider `desktop-gui` or `flask` as an alternative/addition if you want the GUI to be discoverable by its own keywords.

Description is unchanged and still accurate — no update needed.

## 4. Docs — nothing new rewritten this pass

`README.md` already got its full copywriting pass last time (hook-first, badges, honest limitations) and is still accurate apart from the one Roadmap line fixed in §2. This pass's writing effort went into the wiki instead (§5), since that's what was explicitly requested (`+ wiki full`).

## 5. Wiki — full content, drafted in `wiki-drafts/`

GitHub Wikis are a **separate git repository** (`https://github.com/TFD-42/Bad_Usb_Forge.wiki.git`) — these can't be pushed as part of a normal PR to the main repo. 8 ready-to-paste pages:

| Page | Covers |
|---|---|
| `Home.md` | Landing page, links to everything else, one-paragraph project summary |
| `Installation.md` | One-line installers, standalone executables, manual install, optional extras (`[gui]`, `[dev]`, `[build]`) |
| `Usage-CLI.md` | All 4 CLI commands with real, verified flags — plus a note that it supersedes the stale parts of `docs/USAGE.md` |
| `GUI-Guide.md` | The 3-column interface, written from this session's actual verified browser testing (drag & drop, clone-by-URL, clone-by-list, the enrichment form, webhook validation) |
| `Architecture.md` | How classification, enrichment, and the Ollama tool-calling safety pattern actually work — covers the pipeline/GUI layer that `docs/ARCHITECTURE.md` predates |
| `Source-Repositories.md` | Full 79-repo credits list with live star badges, generated by `scripts/generate_credits_badges.py` (same content as the README section, wiki-relative links fixed since wiki pages live in a different git repo and can't use repo-relative paths) |
| `FAQ.md` | Pulled and lightly expanded from the README's FAQ |
| `Troubleshooting.md` | Pulled from the README plus 2 new entries (missing `git`, PowerShell execution policy) that weren't in the README's shorter troubleshooting section |

**To publish**: clone the wiki repo separately and copy these files in (renaming to match — GitHub wiki page URLs are derived from filename, so `Usage-CLI.md` becomes the `Usage-CLI` page, matching the links already used throughout these drafts):

```bash
git clone https://github.com/TFD-42/Bad_Usb_Forge.wiki.git /tmp/afl-wiki
cp wiki-drafts/*.md /tmp/afl-wiki/
cd /tmp/afl-wiki && git add -A && git commit -m "Add full wiki content" && git push
```

Not run automatically — this is exactly the kind of newly-public push that should go out only after you've reviewed the content.

## Sections with nothing new to report

- No new attribution evidence (still correctly silent on fork/reuse).
- No new dependency-pinning issues beyond the one already known and documented.
- No secrets, in the working tree or in git history (checked both this session).
