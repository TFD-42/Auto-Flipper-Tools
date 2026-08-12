# FAQ

**Do I need Ollama for this tool?**
No. `--no-ollama` (CLI) or the "Ollama en secours" checkbox left unticked (GUI) runs the full classify + enrich pipeline with pattern/keyword matching alone and zero network calls. Ollama is only a fallback for files keyword matching can't confidently classify or scan for placeholders.

**Is this tool legal to use?**
Yes, but only for authorized security testing and research. Always obtain proper authorization before using any payload against a system you don't own or don't have explicit permission to test. See [ETHICS.md](https://github.com/TFD-42/BK_Flipper_Full_Pipline/blob/main/ETHICS.md).

**What script formats are supported?**
Ducky Script: `.txt`, `.duck`, `.ds`.

**Can I use this commercially?**
Yes, under the MIT license. Please include license attribution — see [LICENSE](https://github.com/TFD-42/BK_Flipper_Full_Pipline/blob/main/LICENSE).

**Does this tool claim authorship of the payloads it organizes?**
No. It classifies and organizes third-party community payloads sourced from the repos in `Bad_USB_Classifier/url.txt`. Full credit and copyright remain with each original author — see [Source Repositories & Credits](Source-Repositories).

**CLI or GUI — which should I use?**
Either produces the same result. The CLI (`badusb_pipeline.py`) is faster for scripting/automation; the [GUI](GUI-Guide) (`badusb-gui`) is better if you'd rather drag & drop and fill in a form than remember flags.

**Where does my Discord webhook / attacker IP get stored?**
Nowhere but the output scripts you generate yourself, on your own machine. The enrichment agent writes values directly into the copied scripts in your chosen output folder — nothing is sent anywhere by the tool itself.

**Does this work without an internet connection?**
The core classify + enrich pipeline does, with `--no-ollama`. Fetching new source repos (`--urls`, `discover_repos.py`) and the optional Ollama fallback obviously need network access.
