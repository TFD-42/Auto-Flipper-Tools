# Installation Guide

Complete setup instructions for Bad_Usb_Forge.

## System Requirements

- **OS**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 1GB available space

## Step 1: Clone Repository

```bash
git clone https://github.com/TFD-42/Bad_Usb_Forge.git
cd Bad_Usb_Forge
```

## Step 2: Create Virtual Environment (Recommended)

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Optional - Install Ollama

For AI-powered classification (optional but recommended):

### macOS/Linux

```bash
curl https://ollama.ai/install.sh | sh
```

### Windows

Download from: https://ollama.ai/download

### Setup Model

```bash
ollama pull qwen2.5:3b
```

## Verification

Verify installation:

```bash
python Bad_USB_Classifier/classify_badusb.py --help
```

Expected output:
```
Usage: python classify_badusb.py <directory>
```

## Troubleshooting

### Python Not Found

**Error**: `python: command not found`

**Solution**: 
- Linux/macOS: Use `python3` instead of `python`
- Windows: Ensure Python is added to PATH

### Permission Denied

**Error**: `Permission denied: 'venv/bin/activate'`

**Solution**:
```bash
chmod +x venv/bin/activate
```

### Module Not Found

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Ollama Connection Error

**Error**: `Ollama not found - ensure it's installed and in PATH`

**Solution**:
```bash
# Verify Ollama is installed
ollama --version

# If not installed, install from ollama.ai
```

## Next Steps

1. Read [USAGE.md](USAGE.md) for basic usage
2. Check [README.md](../README.md) for features
3. Review [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute

## Getting Help

- 📖 Check documentation files
- 🐛 Search GitHub issues
- 💬 Open a new discussion
- 📧 Contact maintainers
