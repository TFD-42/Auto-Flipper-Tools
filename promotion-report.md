# Promotion & Production-Readiness Report — Auto-Flipper-Tools

Generated via `github-repo-promoter` skill audit (`scripts/repo_audit.py`, live
GitHub data via authenticated `gh` CLI). All claims below trace to the audit
JSON or a file read directly — nothing invented.

## Addendum — full badge-based backlinks (follow-up request)

Per your follow-up, the partial credits table (§1, ~40 of ~90 repos) has been
replaced with a fully generated, complete version:

- **`scripts/generate_credits_badges.py`** — new script, parses `url.txt` and
  emits one entry per repo with a **live shields.io stars badge** (dynamic,
  never hardcoded — see the badge-fabrication rule in §3) that doubles as a
  real backlink to the original author's repo, grouped under the same
  category headers `url.txt` already uses.
- Spliced into `README.suggested.md`'s "Source Repositories & Credits"
  section — now **79 repos**, one badge+link each, organized by category.
- **While generating this I checked every URL against the GitHub API and
  found 2 dead links** already in `url.txt` (`UNC0V3R3D/Flipper_Zero-BadUsb`
  and `Unknown3613/BruceFlipperScripts`, both HTTP 404 — deleted/renamed
  upstream) that predate this session. Removed from `url.txt` (was 81 parsed
  repos, now 79) so the generated badges don't point at broken links.
- Re-run `python3 scripts/generate_credits_badges.py` any time `url.txt`
  changes to regenerate this section — this also permanently fixes the
  sync-drift problem flagged in the original §1 finding below.

## 0. Secrets check (ran first, as required)

`secrets.scanned_files: 20`, `sensitive_filenames: []`, `possible_secrets: []` — **clean**, nothing flagged in the current working tree.

Separately, in this same session, a **real** leak was found and fixed:
7 commits already pushed to `origin/main` carried author metadata
`Scooby <scooby@Scoobys-MacBook-Air.local>` (a real local username/hostname),
and now-deleted setup docs contained `/Users/scooby/...` and a second
identifier. This was rewritten out of the public history via `git filter-repo`
+ force-push (with your explicit approval), verified clean via a fresh clone,
and local dangling refs were purged (`git gc --prune=now`). See `CHANGELOG.suggested.md` for the changelog entry. This is resolved, not a current risk — noted here only for the record.

## 1. Attribution & Provenance

**Code/fork attribution: Insufficient — no evidence found, correctly nothing added.**
Checked `git.remotes` (only `origin`, no `upstream`), `git.commits_mentioning_provenance` (empty), and `license.copyright_lines` (a single generic "Auto-Flipper-Tools Contributors" notice, no earlier/other name). `github.fork` is `false` with no parent. This codebase (classifier, enrichment agent, discovery script, pipeline) shows no signal of being forked from or reusing another project's source — no Acknowledgments-for-forking section was added, per the skill's own rule to stay silent absent evidence.

**Content attribution (the thing you specifically asked about): already good practice, found one real gap.**
The README already has a full "Source Repositories & Credits" section crediting ~40 individual authors by name/link, explicitly framed as classifying third-party payloads rather than claiming authorship — this is exactly right and predates this session. The gap: `Bad_USB_Classifier/url.txt` has grown to **~90 repos** (Hak5's official repos, DuckyScript collections, hardware platforms, attack-specific repos, generators/converters — several whole categories) while the README table still only covers the original ~40. A reader could reasonably assume the table is the complete list when it's now roughly half. Fixed in `README.suggested.md`: the table is now explicitly labeled "highlighted subset — see `url.txt` for the full list," with a one-line statement that this project doesn't claim authorship of anything it classifies.

## 2. Production-Readiness Checklist

| Item | Status | Note |
|---|---|---|
| README hook above the fold | ✅ | Present; tightened wording in the draft |
| Badge row | ⚠️→✅ | Existing badges were accurate but thin (License, Python version, a generic "security: active scanning" badge with no link). Draft adds real CI badges (now genuinely justified — `tests.yml`/`security-scan.yml` exist) and a Cross-Platform badge (now genuinely justified — install scripts + 3-OS CI matrix + per-OS executables) |
| Table of contents | ❌ | `readme.length_chars` = 18,833, well past the ~4,000 trigger. Not added in the draft — optional, your call, since GitHub auto-generates a heading nav for READMEs already |
| Quickstart | ✅ | Present and copy-pasteable; now includes the new one-line installers |
| Features as benefits | ✅ | Present |
| Single install command | ✅→✅✅ | Was already `pip install -r requirements.txt`; now also has one-line `curl`/`irm` installers and standalone executables (this session) |
| Dependencies pinned | ⚠️ | `requests>=2.28.0` (unpinned floor) in both `requirements.txt` files — bumped to `>=2.32.0` in this session to match `pyproject.toml` and to move past a requests CVE with no available floor fix below that version (found during an earlier checklist pass) |
| Dev-dependency separation | ✅ (new) | `pyproject.toml` now has a `[project.optional-dependencies] dev` extra — `pip install -e ".[dev]"` |
| CONTRIBUTING.md | ✅ | Present, includes BadUSB-specific ethics section |
| CODE_OF_CONDUCT.md | ❌ | Missing. Drafted as `CODE_OF_CONDUCT.suggested.md` (Contributor Covenant 2.1, short form, with a scope note pointing at ETHICS.md/SECURITY.md) — this repo already invests in community infra (issue templates, PR template, SECURITY.md), so it fits; skip it if you'd rather not formalize a community process |
| SECURITY.md | ✅ | Present |
| CHANGELOG.md | ❌ | Missing. Drafted as `CHANGELOG.suggested.md`, populated with this session's real changes plus the existing v1.0.0 history recovered from the old README |
| Issue/PR templates | ✅ | Both present |
| CI present | ✅ | `tests.yml`, `security-scan.yml`, and (new this session) `release.yml` |
| Tests exist | ✅ (new) | Was **0 tests** despite `pytest ... \|\| true` in CI silently reporting green — fixed earlier this session (14 real tests, `\|\| true` removed so CI now actually fails on regressions) |
| Docs structure | ✅ | `docs/` has 3 consistent files; no wiki content yet despite `github.has_wiki: true` |
| GitHub description | ✅ | Already solid, keyword-forward, live via `gh` — see §3 |
| GitHub topics | ✅ | Already 12 specific tags — see §3 for a small delta |
| Homepage URL | ❌ | Empty. No docs site exists to point it at yet — not actionable right now |
| Social preview image | — | Couldn't check via API; verify manually at Settings → General → Social preview |

## 3. SEO — GitHub Description, Topics, Backlinks

**Description** — current (`gh api`, live): *"Automated BadUSB classifier and Flipper Zero automation toolkit — AI-powered Ducky Script analysis, batch classification, and payload organization for security professionals"* (159 chars). Already keyword-forward and accurate. Only change I'd suggest, if you want to re-set it, is folding in "cross-platform" now that it's true:

> `Cross-platform BadUSB/Ducky Script classifier + enrichment for Flipper Zero — AI-powered (Ollama), works offline, one-line install`

**Topics** — current 12: `automation`, `badusb`, `classification`, `ducky-script`, `flipper`, `flipper-zero`, `open-source`, `payload-analysis`, `python`, `security-automation`, `security-research`, `security-tools`. All still accurate. Suggested additions (specific, not generic — matches what's actually in the code now):
- `ollama` — real dependency/differentiator, currently unrepresented
- `cli` — now genuinely a CLI toolkit with console_scripts
- `pyinstaller` or `standalone-executable` — new release artifact type
- `cross-platform` — now genuinely true (was arguably a stretch before this session)

I did **not** run `gh repo edit` to apply either of these — that field is public the instant it changes, so it's your call on exact wording. One-liner if you want it:
```bash
gh repo edit TFD-42/Auto-Flipper-Tools \
  --description "Cross-platform BadUSB/Ducky Script classifier + enrichment for Flipper Zero — AI-powered (Ollama), works offline, one-line install" \
  --add-topic ollama --add-topic cli --add-topic cross-platform
```

**Badges** — see `README.suggested.md`. Added: real CI badges (linked to the actual workflow files), a Cross-Platform badge, a "Local-first / optional AI" badge (precise wording — the classifier and enrichment agent both run fully offline with `--no-ollama`; Ollama is a fallback, not a requirement). Deliberately **not** added: a PyPI badge (not published there — see backlinks below), a star-count badge (repo has 3 stars per the live audit; a hand-typed badge would go stale — use the dynamic `img.shields.io/github/stars/...` badge yourself if/when you want one).

**Backlinks / discovery checklist** (all external actions, your call on which to pursue):

- **Awesome-flipperzero lists** — the README/`url.txt` already reference `djsime1/awesome-flipperzero`, `anasancho/awesome-flipperzero`, and `RogueMaster/awesome-flipperzero-withModules`. A PR adding one line to one or more of these (name + one-sentence description + link) is likely the single best backlink available given the exact-match audience. Pitch: *"Auto-Flipper-Tools — classifies and organizes BadUSB/Ducky Script payloads from ~90 community repos into ready-to-flash categories, with AI-optional enrichment for webhooks/IPs/tokens."*
- **PyPI** — the package now builds cleanly (`python -m build`, verified this session) but isn't published. Publishing it is both a distribution channel and a backlink (PyPI project pages link back to the repo and are independently indexed). Not done automatically — publishing is a one-way action (a PyPI name, once claimed, can't be un-claimed) that should be your call.
- **Homebrew** — a formula/cask isn't set up; worth considering given the macOS-friendly standalone executable now exists, but it's meaningful ongoing maintenance (Homebrew formulas need to track releases).
- **LibHunt / AlternativeTo** — reasonable free listings; AlternativeTo works if there's a well-known closest tool to compare against (arguably Hak5's own payload tooling, or the various one-off classifier scripts this project's `url.txt` already lists as sources).
- **dev.to / blog write-up** — a "why I built a BadUSB payload classifier" post would explain the *why* in a way the README structurally can't, and is a genuine backlink. Only worth it once you're comfortable with the repo getting more eyes on it (it's already public with the identity fix applied, so no blocker there).
- **Show HN / r/flipperzero** — plausible once you're happy with the polish pass in this report; note the sub already gets tool-share posts, so a specific, working, easy-to-try tool (the one-line installer helps a lot here) tends to land better than a vague announcement.

## 4. What changed and why (docs)

- `README.suggested.md` — reordered hook to lead with the concrete one-line pitch, updated directory structure/current-tools list to match what's actually in the repo now, replaced the two sets of **unverified performance numbers** (no benchmark script existed anywhere in the repo — these looked like leftover marketing copy) with a number I actually measured this session (959 real files, 4 real community repos, 1.83s, keyword-only mode — see the Performance section), fixed the credits-table completeness gap from §1, added the badges from §3, tightened the FAQ/troubleshooting to reflect `--no-ollama` accurately.
- `CHANGELOG.suggested.md` — didn't exist; drafted with this session's real, verifiable changes plus the v1.0.0 history recovered from the old README's feature list.
- `CODE_OF_CONDUCT.suggested.md` — didn't exist; drafted, optional.
- `requirements.txt` / `Bad_USB_Classifier/requirements.txt` — bumped `requests` floor from `2.28.0` to `2.32.0` to match `pyproject.toml` and move past a CVE affecting older floors (no fixed version exists yet above 2.32.5 as of this session — noted, not fully resolvable upstream).

None of the `.suggested.md`/`.suggested` files have been applied over the originals — review and rename (drop `.suggested`) whichever ones you want to keep, or ask me to apply them directly.

## Sections with nothing to report

- **Fork/code attribution**: confirmed no evidence — correctly left blank rather than guessed.
- **License mismatch**: `LICENSE` and `pyproject.toml` both say MIT, consistent, no action needed.
- **CI security findings**: bandit currently reports 0 Medium/High (checked earlier this session); nothing new to flag here.
