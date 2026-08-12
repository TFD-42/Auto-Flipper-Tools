# BadUSB Classifier

Intelligent Ducky Script classifier and organizer for BadUSB payloads using keyword detection and AI-powered categorization.

## Features

- **Ducky Script Validation**: Detects valid BadUSB scripts using keyword matching
- **Multi-Level Classification**: 
  - Pattern-based detection (fast)
  - AI-powered classification via Ollama (accurate)
  - Automatic fallback to "unassigned" category
- **Batch Processing**: Recursively processes entire directory structures
- **Collision Handling**: Auto-renames files with duplicate names
- **Comprehensive Logging**: Detailed file and console logging with statistics
- **Error Resilience**: Graceful error handling for malformed files

## Installation

### Requirements
- Python 3.8+
- Ollama (optional, for AI classification)

### Setup

```bash
cd Bad_USB_Classifier
pip install -r requirements.txt
```

### Ollama Setup (Optional)

For AI-powered classification, install Ollama:
```bash
# https://ollama.ai
ollama pull qwen2.5:3b
```

## Usage

```bash
python classify_badusb.py <directory_path>
# or, with keyword-only classification (no Ollama calls, no pass 2):
python classify_badusb.py <directory_path> --no-ollama
```

### Example

```bash
python classify_badusb.py ./badusb_samples
```

Output structure:
```
badusb_samples/
├── classified_badusb/
│   ├── exfiltration/
│   ├── phishing/
│   ├── remote_access/
│   ├── credentials/
│   └── unassigned/
└── classification.log
```

### Building/refreshing the source corpus

```bash
# Clone (or `git pull` if already cloned) every repo listed in url.txt
python classify_badusb.py --urls url.txt --output ./badusb_repos

# Search GitHub/Reddit for new source repos not yet in url.txt (dry-run)
python discover_repos.py
# ...and append the ones you want to keep:
python discover_repos.py --write
```

### Enriching scripts before flashing

`payload_setup_agent.py` scans an already-classified folder, detects scripts
that need a value (Discord webhook, Telegram bot/chat id, attacker IP/port,
email, `[placeholder]` values...), and interactively fills them in — guiding
you through creating a Discord webhook from scratch if you don't have one
yet. See [`badusb_pipeline.py`](../badusb_pipeline.py) at the repo root for
the one-command version that chains classification and enrichment together.

```bash
python payload_setup_agent.py ./badusb_samples/classified_badusb
```

## Supported File Extensions

- `.txt` - Text-based scripts
- `.duck` - Ducky Script format
- `.ds` - Ducky Script variant

## Classification Categories

exfiltration, PassVault, remote_access, CartmanSong, general, phishing, ReverseShell, Chrome2Discord, iMessageExfil, prank, Telegram, credentials, incident_response, quackberry, Text2Speech, destructive, Mimikatz, ransom, web2Discord, EmailAndTextMessage, MOAB, execution, mobile, recon

## How It Works

1. **Validation Phase**: Verifies file contains valid Ducky Script keywords
2. **Detection Phase**: Searches for topic keywords in content
3. **Classification Phase**: If no match, queries Ollama for AI classification
4. **Organization Phase**: Moves files to appropriate category folder

## Logging

Classification logs are saved to `classification.log` with:
- Timestamp
- Log level (INFO, DEBUG, ERROR)
- Processing status and details

## Configuration

Edit these constants in `classify_badusb.py`:

```python
OLLAMA_MODEL = "qwen2.5:3b"          # Change AI model
VALID_KEYWORDS = {...}               # Modify Ducky Script keywords
TOPICS = [...]                       # Add/remove categories
SUPPORTED_EXTENSIONS = {".txt", ...} # Change file types
```

## Performance

- **Pattern Detection**: ~10-50ms per file
- **AI Classification**: ~500-1000ms per file (depends on content size)
- **Batch Processing**: 100+ files/minute on typical hardware

## Limitations

- Requires Ollama running locally for AI classification
- Large files (>10MB) may timeout during AI classification
- Accuracy depends on script quality and keyword presence

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

Areas for contribution:
- Additional classification categories
- Support for more script formats (AutoIt, AutoHotkey)
- Performance optimizations
- Test coverage
- Documentation improvements

## License

MIT License - See LICENSE file

## References & Origins

This tool was inspired by and references:
- [Flipper Zero](https://flipperzero.one/) - Multi-tool device for security professionals
- [BadUSB Research](https://adamcaudill.com/2014/10/17/badusb/) - Concept and security implications
- [Ducky Script Documentation](https://docs.hak5.org/hak5-usb-rubber-ducky/) - Official script syntax
- Flipper Zero BadUSB community payloads and research

## Security Notice

This tool is designed for authorized security testing, research, and defensive purposes only. Users are responsible for legal compliance when working with BadUSB payloads.

## Author

Developed as part of BK_Flipper_Full_Pipline suite for security automation and analysis.

## Support

For issues, questions, or feature requests: Open an issue on GitHub
