# Usage — Command Line

## One command: classify + enrich

```bash
badusb-pipeline /path/to/any/badusb/scripts
```

Works on any folder of `.txt`/`.duck`/`.ds` scripts, loose or nested. Produces a single output folder (`<source>_organized` by default, or pick one with `--output`) that's classified by theme and has placeholders filled in — nothing left to do but copy it onto the Flipper Zero's SD card, in `badusb/`.

Flags:

| Flag | What it does |
|---|---|
| `--output DIR` / `-o DIR` | Custom output location |
| `--no-ollama` | Fully offline: keyword-matching only, no AI fallback, no network calls |
| `--model NAME` | Ollama model to use for the fallback (default: `qwen2.5-1.5b-heretic:latest`) |

## The individual tools

### Classifier only

```bash
badusb-classify /path/to/payloads --no-ollama
```

Recursive, dedup-aware, two-pass classification into 24 topic categories (`exfiltration`, `credentials`, `ReverseShell`, `prank`, `Telegram`, `Mimikatz`, ...). Bundles (a script + its supporting files in one folder) are kept together and classified as a unit; single scripts are classified individually. Exact-content and header-fingerprint duplicates are skipped.

### Enrichment agent only

```bash
badusb-setup-agent /path/to/classified_folder
```

Scans for scripts that need a value before they'll work — Discord webhook, Telegram bot/chat id, attacker IP/port, email, `[bracket]` placeholders — and interactively asks for each one (once per field type, reused across all matching files, or per-file if you prefer). If you don't have a Discord webhook yet, it walks you through creating one from scratch and validates the URL format before accepting it. Nothing is ever applied without you confirming a value first.

### Refresh the bundled source corpus

```bash
badusb-classify --urls Bad_USB_Classifier/url.txt
```

Clones (or `git pull`s, if already cloned) every repo listed in `url.txt` — currently ~79 community BadUSB/Ducky-Script source repos. See [Source Repositories & Credits](Source-Repositories).

### Find new sources

```bash
badusb-discover
```

Searches GitHub's search API and Reddit's public JSON search for BadUSB payload repos not yet in `url.txt`. Dry-run by default — it only prints candidates. Add `--write` to append reviewed candidates to `url.txt`. It never clones anything itself; that stays a separate, explicit step so you can review the list first.

## A realistic session

```bash
# 1. See what's out there that you don't already track
badusb-discover --write

# 2. Pull down everything in the (now larger) source list
badusb-classify --urls Bad_USB_Classifier/url.txt --output ~/badusb_repos

# 3. Classify + enrich in one pass
badusb-pipeline ~/badusb_repos --no-ollama

# 4. Copy the result onto your Flipper's SD card
cp -r ~/badusb_repos_organized/* /Volumes/FLIPPER/badusb/
```

## Note on `docs/USAGE.md`

The older `docs/USAGE.md` in the repo predates the unified pipeline, the enrichment agent, and the GUI, and some of its examples (custom output via source editing, a specific log line format) no longer match the current tool. This wiki page reflects what's actually verified working today; `docs/USAGE.md` is due for a refresh.
