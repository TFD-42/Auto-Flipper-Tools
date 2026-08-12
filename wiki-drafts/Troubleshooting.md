# Troubleshooting

## `Ollama not found - ensure it's installed and in PATH`

Install Ollama from [ollama.ai](https://ollama.ai), or just add `--no-ollama` (CLI) / leave "Ollama en secours" unchecked (GUI) to skip AI entirely — the pipeline works fully without it.

## `Ollama request timed out`

Only affects the optional Ollama fallback path. Re-run with `--no-ollama` for the deterministic keyword-only path, or increase `OLLAMA_TIMEOUT_FAST`/`OLLAMA_TIMEOUT_DEEP` in `Bad_USB_Classifier/classify_badusb.py`.

## `Cannot read file` / `Cannot move file` (Permission Denied)

Check file permissions on the source folder and ensure you have write access to the output directory.

## `ModuleNotFoundError: No module named 'requests'` (or `flask`, `pytest`, ...)

You're running from source without installing dependencies. From the repo root:

```bash
pip install -r requirements.txt          # core (requests)
pip install -e ".[gui]"                  # + Flask, for the GUI
pip install -e ".[dev]"                  # + test/lint tooling
```

## `git: command not found` (installers, `--urls`, `discover_repos.py`, GUI clone features)

Install git — [git-scm.com/downloads](https://git-scm.com/downloads) — then retry. The installers, source-corpus refresh, and the GUI's clone-by-URL features all shell out to a real `git` binary.

## URL de webhook Discord invalide (GUI enrichment form)

The enrichment agent validates the format server-side (`https://discord.com/api/webhooks/<id>/<token>`) before writing anything. If you're not sure how to get a real one, click "Pas encore de webhook ? Guide" in the form for step-by-step instructions from a brand-new Discord account.

## Windows PowerShell install script won't run (`running scripts is disabled`)

PowerShell's execution policy is blocking the `irm | iex` one-liner. Either run PowerShell as your normal user and use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
irm https://raw.githubusercontent.com/TFD-42/Bad_Usb_Forge/main/scripts/install.ps1 | iex
```

or download `scripts/install.ps1` and inspect it before running, if you'd rather not change the execution policy at all.

## Still stuck?

- [Open an issue](https://github.com/TFD-42/Bad_Usb_Forge/issues)
- Check [FAQ](FAQ) and [Usage — CLI](Usage-CLI) / [Usage — GUI](GUI-Guide)
