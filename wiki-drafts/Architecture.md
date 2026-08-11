# Architecture

## Module map

```
badusb_pipeline.py          orchestrates the two modules below into one pass
gui/app.py                  Flask backend calling the same two modules directly
Bad_USB_Classifier/
  classify_badusb.py        classification (pass 1 + pass 2)
  payload_setup_agent.py    placeholder detection + enrichment
  discover_repos.py         GitHub/Reddit source discovery
  ollama_agent.py           shared Ollama tool-calling wrapper
```

## Classification (`classify_badusb.py`)

**Pass 1 — fast scan:**
1. `is_ducky_script()` — keyword-based validation (`STRING`, `DELAY`, `REM`, `GUI`, ...). Files that don't match are skipped.
2. Bundle detection — a Ducky script sitting alongside supporting files (helper scripts, images, docs) in the same folder is treated as one unit and classified together, not split apart.
3. Deduplication — `DedupIndex` skips exact content matches and near-duplicate "header fingerprint" matches (same first few non-trivial lines, ignoring author/credit `REM` comments).
4. `classify_content()` — first tries `extract_topic_from_content()` (keyword match against the 24 known topics), then falls back to `ask_ollama_fast()` if nothing matched and Ollama is enabled, then `unassigned` as a last resort.

**Pass 2 — deep Ollama refinement** (only runs when Ollama is enabled): re-reads every classified file individually with a longer prompt and majority-votes bundles across all their readable files, potentially moving items to a more accurate category than pass 1's quick match found.

Both passes are skippable — `use_ollama=False` (or `--no-ollama`) makes the whole run deterministic and network-free.

## Enrichment (`payload_setup_agent.py`)

1. `scan_file()` runs a list of `FieldSpec` regex patterns against each classified file — Discord webhook, Telegram bot token, Telegram chat id, attacker IP (`LHOST`), attacker port (`LPORT`), email, generic URL, and `[BRACKET_PLACEHOLDER]`-style tokens (filtered against a small allowlist/ALL-CAPS heuristic to avoid false positives like PowerShell type casts `[Math]`, `[int]`).
2. Files with zero regex matches are `plug_and_play` — copied through with no changes needed.
3. Files with matches go into `SetupPlan.to_configure`, grouped by field type across the whole run so a value can be entered once and reused, or per-file if preferred.
4. `apply_and_copy()` writes the resolved values back into the matched substrings and produces a `setup_report.md` (which script got which value, and which are still pending).

**Safety pattern**: when regex finds nothing and Ollama is enabled, `ollama_fallback_scan()` asks the model to suggest fields via a structured tool call (`report_fields_needed`) — never free text. Every suggested substring is checked for a verbatim match in the actual file content before being trusted; anything that doesn't literally appear in the file is discarded. The model never edits a file directly.

## Repo discovery (`discover_repos.py`)

Searches GitHub's public search API and Reddit's public JSON search endpoint for BadUSB/Ducky-Script-related repos, extracts `github.com/owner/repo` links, and diffs against what's already in `url.txt`. Dry-run by default. Never clones anything — that stays `classify_badusb.py --urls`'s job, kept as a separate explicit step so a human reviews the list first.

## `ollama_agent.py` — the shared safety contract

Every AI interaction in this project goes through `chat_with_tools()`, which enforces one rule throughout the codebase: **the model can only act via a structured tool call that a human-written Python function then executes deterministically** — never by having free-text output parsed and acted on directly. This is why the enrichment agent's Ollama fallback can't silently corrupt a script: the tool call proposes a substring, and the calling code independently verifies it exists in the file before touching anything.

## The unified pipeline and GUI

`badusb_pipeline.py` is a thin orchestrator: call `run_classifier()`, then `analyze_tree()` + `collect_field_values()` + `apply_and_copy()` on the result, writing everything into one clean output folder instead of the intermediate `classified_badusb/` + `ready_to_flash/` split the standalone tools produce by default.

`gui/app.py` is a Flask app that calls the exact same functions directly (no subprocess, no shelling out to the CLI) — the 3-column UI is a thin visual layer over the same classification and enrichment logic, kept in a separate `ready/` folder per column so the source/classified/enriched stages stay visually distinct. See [GUI Guide](GUI-Guide) for the user-facing walkthrough.

## Note on `docs/ARCHITECTURE.md`

The existing `docs/ARCHITECTURE.md` file describes an earlier, classifier-only version of the project (no enrichment agent, no pipeline orchestration, no GUI). Its description of pass 1/pass 2 classification is still directionally accurate; this wiki page is the more complete and current picture.
