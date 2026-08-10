#!/usr/bin/env bash
# Auto-Flipper-Tools — installateur automatisé macOS / Linux / Unix.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/TFD-42/Auto-Flipper-Tools/main/scripts/install.sh | bash
#   # ou, depuis un clone local:
#   ./scripts/install.sh
#
# Ce script: détecte l'OS, vérifie Python 3.8+, crée un venv dédié dans
# ~/.auto-flipper-tools/venv, installe le package (depuis le dépôt local si
# présent, sinon clone le dépôt), et expose les commandes CLI via de petits
# wrappers dans ~/.auto-flipper-tools/bin. N'installe jamais rien avec sudo.
# Tout est auto-contenu: supprimer ~/.auto-flipper-tools désinstalle tout.
set -euo pipefail

REPO_URL="https://github.com/TFD-42/Auto-Flipper-Tools.git"
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
log "OS détecté: $OS"

PYTHON_BIN="$(find_python)" || {
  warn "Python ${MIN_PY_MAJOR}.${MIN_PY_MINOR}+ introuvable."
  case "$OS" in
    macos) warn "Installe-le avec: brew install python3   (Homebrew: https://brew.sh)" ;;
    linux) warn "Installe-le avec ton gestionnaire de paquets, ex: sudo apt install python3 python3-venv" ;;
    *)     warn "Installe Python 3.8+ depuis https://www.python.org/downloads/" ;;
  esac
  die "Installation interrompue — Python manquant."
}
log "Python utilisé: $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"

if ! command -v git >/dev/null 2>&1; then
  die "git est requis mais introuvable. Installe-le puis relance ce script."
fi

# Repère un checkout local (script lancé depuis le dépôt) sinon clone.
# ${BASH_SOURCE[0]} est absent quand le script arrive via `curl | bash` (pas
# de fichier local, lu depuis stdin) — sous `set -u` il faut le protéger
# avec ${BASH_SOURCE[0]:-} pour ne pas planter sur "unbound variable".
SOURCE_PATH="${BASH_SOURCE[0]:-}"
REPO_DIR=""
if [ -n "$SOURCE_PATH" ]; then
  SCRIPT_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"
  REPO_DIR="$(dirname "$SCRIPT_DIR")"
fi
if [ -n "$REPO_DIR" ] && [ -f "$REPO_DIR/pyproject.toml" ] && grep -q '^name = "auto-flipper-tools"' "$REPO_DIR/pyproject.toml" 2>/dev/null; then
  log "Dépôt local détecté: $REPO_DIR"
  SOURCE_DIR="$REPO_DIR"
else
  SOURCE_DIR="$INSTALL_ROOT/src"
  if [ -d "$SOURCE_DIR/.git" ]; then
    log "Mise à jour du dépôt existant..."
    git -C "$SOURCE_DIR" pull --ff-only
  else
    log "Clonage du dépôt dans $SOURCE_DIR..."
    mkdir -p "$INSTALL_ROOT"
    git clone --depth 1 "$REPO_URL" "$SOURCE_DIR"
  fi
fi

log "Création du venv dans $VENV_DIR..."
"$PYTHON_BIN" -m venv "$VENV_DIR"

log "Installation du package..."
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

log "Installé. Commandes disponibles: badusb-pipeline, badusb-classify, badusb-setup-agent, badusb-discover"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    warn "$BIN_DIR n'est pas dans ton PATH."
    warn "Ajoute cette ligne à ton ~/.bashrc ou ~/.zshrc puis rouvre ton terminal:"
    warn "  export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac

log "Test rapide:"
"$BIN_DIR/badusb-pipeline" --help | head -3 || true

log "Prêt. Exemple: badusb-pipeline /chemin/vers/tes/scripts/badusb"
