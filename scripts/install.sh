#!/usr/bin/env bash
# BK_Flipper_Full_Pipline — automated installer for macOS / Linux / Unix.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/TFD-42/BK_Flipper_Full_Pipline/main/scripts/install.sh | bash
#   # or, from a local clone:
#   ./scripts/install.sh
#
# This script: detects the OS, checks for Python 3.8+, creates a dedicated
# venv in ~/.auto-flipper-tools/venv, installs the package (from the local
# repo if present, otherwise clones it), and exposes the CLI commands via
# small wrappers in ~/.auto-flipper-tools/bin. Never installs anything with
# sudo. Fully self-contained: removing ~/.auto-flipper-tools uninstalls
# everything.
set -euo pipefail

REPO_URL="https://github.com/TFD-42/BK_Flipper_Full_Pipline.git"
INSTALL_ROOT="${AUTO_FLIPPER_HOME:-$HOME/.auto-flipper-tools}"
VENV_DIR="$INSTALL_ROOT/venv"
BIN_DIR="$INSTALL_ROOT/bin"
MIN_PY_MAJOR=3
MIN_PY_MINOR=8

log()  { printf '\033[1;34m[install]\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$1" >&2; exit 1; }

detect_os() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux)  echo "linux" ;;
    *)      echo "unix" ;;
  esac
}

find_python() {
  for candidate in python3.12 python3.11 python3.10 python3.9 python3.8 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      ver="$("$candidate" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || true)"
      [ -z "$ver" ] && continue
      major="${ver%%.*}"; minor="${ver##*.}"
      if [ "$major" -eq "$MIN_PY_MAJOR" ] && [ "$minor" -ge "$MIN_PY_MINOR" ]; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

OS="$(detect_os)"
log "Detected OS: $OS"

PYTHON_BIN="$(find_python)" || {
  warn "Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ not found."
  case "$OS" in
    macos) warn "Install it with: brew install python3   (Homebrew: https://brew.sh)" ;;
    linux) warn "Install it with your package manager, e.g. sudo apt install python3 python3-venv" ;;
    *)     warn "Install Python 3.8+ from https://www.python.org/downloads/" ;;
  esac
  die "Installation aborted — Python missing."
}
log "Using Python: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"

if ! command -v git >/dev/null 2>&1; then
  die "git is required but was not found. Install it, then re-run this script."
fi

# Detects a local checkout (script run from the repo) otherwise clones.
# ${BASH_SOURCE[0]} is absent when the script arrives via `curl | bash` (no
# local file, read from stdin) — under `set -u` it must be guarded with
# ${BASH_SOURCE[0]:-} to avoid crashing on "unbound variable".
SOURCE_PATH="${BASH_SOURCE[0]:-}"
REPO_DIR=""
if [ -n "$SOURCE_PATH" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"
  REPO_DIR="$(dirname "$SCRIPT_DIR")"
fi
if [ -n "$REPO_DIR" ] && [ -f "$REPO_DIR/pyproject.toml" ] && grep -q '^name = "auto-flipper-tools"' "$REPO_DIR/pyproject.toml" 2>/dev/null; then
  log "Local repo detected: $REPO_DIR"
  SOURCE_DIR="$REPO_DIR"
else
  SOURCE_DIR="$INSTALL_ROOT/src"
  if [ -d "$SOURCE_DIR/.git" ]; then
    log "Updating the existing repo..."
    git -C "$SOURCE_DIR" pull --ff-only
  else
    log "Cloning the repo into $SOURCE_DIR..."
    mkdir -p "$INSTALL_ROOT"
    git clone --depth 1 "$REPO_URL" "$SOURCE_DIR"
  fi
fi

log "Creating the venv in $VENV_DIR..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

log "Installing the package..."
"$VENV_DIR/bin/pip" install --upgrade -q pip
"$VENV_DIR/bin/pip" install -q "$SOURCE_DIR"

mkdir -p "$BIN_DIR"
for cmd in badusb-pipeline badusb-classify badusb-setup-agent badusb-discover; do
  wrapper="$BIN_DIR/$cmd"
  cat > "$wrapper" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/$cmd" "\$@"
EOF
  chmod +x "$wrapper"
done

log "Installed. Available commands: badusb-pipeline, badusb-classify, badusb-setup-agent, badusb-discover"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    warn "$BIN_DIR is not in your PATH."
    warn "Add this line to your ~/.bashrc or ~/.zshrc, then reopen your terminal:"
    warn "  export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac

log "Quick test:"
"$BIN_DIR/badusb-pipeline" --help | head -3 || true

log "Ready. Example: badusb-pipeline /path/to/your/badusb/scripts"
