#!/usr/bin/env bash
###############################################################################
# PIXELLA - Interactive Installation Script
# curl | bash safe, fully interactive
###############################################################################

set -Eeuo pipefail

# Ensure interactive input even when piped
if [ -r /dev/tty ]; then
  exec </dev/tty
fi

###############################################################################
# Globals
###############################################################################
REPO_URL="https://github.com/DominionDev-coder/Pixella-chatbot"
INSTALL_DIR="$HOME/.pixella"
REPO_NAME="Pixella-chatbot"
PROJECT_ROOT="$INSTALL_DIR/$REPO_NAME"
INSTALLATION_MODE=""
VERSION=""
OS_TYPE=""
PYTHON_CMD=""
VENV_DIR=""
VENV_ACTIVATE_CMD=""
VENV_PYTHON_BIN=""

###############################################################################
# Colors
###############################################################################
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

###############################################################################
# Printing helpers
###############################################################################
print() { printf '%b\n' "$1"; }
step() { print "${BLUE}→${NC} $1"; }
ok() { print "${GREEN}✓${NC} $1"; }
warn() { print "${YELLOW}⚠${NC} $1"; }
err() { print "${RED}✗${NC} $1"; }

###############################################################################
# Interactive input (TTY-safe)
###############################################################################
ask() {
  local prompt="$1"
  local default="$2"
  local __var="$3"
  local reply

  if [ ! -r /dev/tty ]; then
    eval "$__var=\"${default}\""
    return
  fi

  while true; do
    printf "%s" "$prompt" > /dev/tty
    [ -n "$default" ] && printf " [%s]" "$default" > /dev/tty
    printf ": " > /dev/tty

    if IFS= read -r reply < /dev/tty; then
      reply="${reply:-$default}"
      eval "$__var=\"${reply}\""
      return
    fi
  done
}

###############################################################################
# Error cleanup
###############################################################################
cleanup_on_error() {
  err "Installation failed."
  if [ "$INSTALLATION_MODE" = "remote" ] && [ -d "$PROJECT_ROOT" ]; then
    warn "Cleaning up cloned repository..."
    rm -rf "$PROJECT_ROOT" || true
  fi
  exit 1
}
trap cleanup_on_error ERR

###############################################################################
# Header & user preview
###############################################################################
print_header() {
  print "${CYAN}"
  print "══════════════════════════════════════════════════════"
  print " 🤖 PIXELLA — Interactive Installation Script"
  print "══════════════════════════════════════════════════════"
  print "${NC}"
}

print_user_preview() {
  print "${CYAN}This installer is interactive.${NC}"
  print ""
  print "You will be asked to:"
  print "  • Select a Pixella version"
  print "  • Confirm or create a Python virtual environment"
  print "  • Install required Python dependencies"
  print "  • Optionally configure environment variables (.env)"
  print "  • Add Pixella to your PATH"
  print ""
  print "Nothing will be installed without your confirmation."
  print ""
}

###############################################################################
# OS detection
###############################################################################
detect_os() {
  step "Detecting operating system..."
  case "$(uname -s)" in
    Linux*)
      OS_TYPE="Linux"
      ok "Linux detected"
      ;;
    Darwin*)
      OS_TYPE="macOS"
      ok "macOS detected"
      ;;
    CYGWIN*|MINGW*|MSYS*)
      OS_TYPE="Windows"
      warn "Windows detected (WSL / Git Bash expected)"
      ;;
    *)
      err "Unsupported OS"
      exit 1
      ;;
  esac
}



###############################################################################
# Git detection
###############################################################################
check_git() {
  step "Checking Git installation..."
  if ! command -v git >/dev/null 2>&1; then
    err "Git is required but not installed."
    err "Please install Git and re-run the installer."
    exit 1
  fi
  ok "Git found"
}


###############################################################################
# Installation mode
###############################################################################
detect_installation_mode() {
  step "Detecting installation mode..."

  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SCRIPT_PARENT="$(dirname "$SCRIPT_DIR")"

  if [ -f "$SCRIPT_PARENT/requirements.txt" ] && [ -d "$SCRIPT_PARENT/.git" ]; then
    INSTALLATION_MODE="local"
    PROJECT_ROOT="$SCRIPT_PARENT"
    ok "Local installation detected"
  else
    INSTALLATION_MODE="remote"
    PROJECT_ROOT="$INSTALL_DIR/$REPO_NAME"
    ok "Remote installation detected"
  fi
}

###############################################################################
# Version selection
###############################################################################
select_version() {
  step "Selecting Pixella version..."

  local tags
  tags="$(git ls-remote --tags "$REPO_URL" 2>/dev/null | awk -F/ '{print $NF}' | grep -v '\^{}' | sort -V || true)"

  if [ -z "$tags" ]; then
    err "Failed to fetch versions."
    exit 1
  fi

  print ""
  print "Available options:"
  print "  latest   (recommended. stable and released version)"
  print "  main     (development branch)"
  print ""

  print "Available release versions:"
  while IFS= read -r tag; do
    print "  $tag"
  done <<< "$tags"
  print ""

  while true; do
    ask "Enter version" "latest" input

    case "$input" in
      latest)
        VERSION="$(printf "%s\n" "$tags" | tail -n 1)"
        VERSION_MODE="release"
        ok "Using latest stable release: $VERSION"
        return
        ;;
      main)
        VERSION="main"
        VERSION_MODE="main"
        warn "⚠ You selected 'main'"
        warn "This branch may be unstable due to ongoing development."
        warn "Recommended only for developers, bug fixers,"
        warn "or users testing new features."
        ask "Continue with unstable 'main' branch?" "n" confirm
        case "$confirm" in
          y|Y) ;;
          *) err "Installation aborted."; exit 1 ;;
        esac

        return
        ;;
      *)
        if printf "%s\n" "$tags" | grep -qx "$input"; then
          VERSION="$input"
          VERSION_MODE="release"
          ok "Selected release version: $VERSION"
          return
        fi
        ;;
    esac

    warn "Invalid selection, try again."
  done
}


###############################################################################
# Python detection
###############################################################################
check_python_version() {
  step "Checking Python installation..."

  for cmd in python3.11 python3.12 python3.13 python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
      PYTHON_CMD="$cmd"
      ok "Using $PYTHON_CMD"
      return
    fi
  done

  err "Python 3.11+ is required"
  exit 1
}


###############################################################################
# Update bin/pixella
###############################################################################
update_bin_pixella() {
  step "updating bin/pixella Python command..."

  sed -i.bak "s|^PYTHON_CMD=.*$|PYTHON_CMD=\"$PYTHON_CMD\"|" "$PROJECT_ROOT/bin/pixella" || true
  rm -f "$PROJECT_ROOT/bin/pixella.bak"
  ok "bin/pixella updated to use detected system Python"
  return
}


###############################################################################
# Clone repository
###############################################################################
clone_repository() {
  step "Preparing Pixella source code..."

  mkdir -p "$INSTALL_DIR"

  if [ -d "$PROJECT_ROOT/.git" ]; then
    warn "Repository already exists"
    ask "Update existing installation?" "y" ans
    case "$ans" in
      y|Y)
        cd "$PROJECT_ROOT"
        git fetch origin
        git fetch --tags --force
        git status --porcelain | grep -q . && warn "Local changes detected, skipping pull" || git pull
        ;;
      *)
        ok "Using existing repository"
        ;;
    esac
  else
    git clone "$REPO_URL" "$PROJECT_ROOT"
  fi

  cd "$PROJECT_ROOT"
  git fetch origin
  git fetch --tags --force

  if [ "$VERSION_MODE" = "main" ]; then
    git checkout main
  else
    git checkout "tags/$VERSION"
  fi


  if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
    err "Invalid Pixella project structure, please report this error on GitHub, We'll fix it"
    exit 1
  fi

  ok "Repository ready ($VERSION)"
}


###############################################################################
# Virtual environment
###############################################################################
create_and_activate_venv() {
  step "Python environment setup..."

  ask "Create and use a virtual environment?" "y" choice
  case "$choice" in
    y|Y)
      VENV_DIR=".venv"
      if [ -d "$VENV_DIR" ]; then
        warn "Virtual environment already exists, reusing it"
      else
        "$PYTHON_CMD" -m venv "$VENV_DIR"
      fi


      if [ "$OS_TYPE" = "Windows" ]; then
        VENV_ACTIVATE_CMD="source $VENV_DIR/Scripts/activate"
        VENV_PYTHON_BIN="$VENV_DIR/Scripts/python.exe"
      else
        VENV_ACTIVATE_CMD="source $VENV_DIR/bin/activate"
        VENV_PYTHON_BIN="$VENV_DIR/bin/python"
      fi

      eval "$VENV_ACTIVATE_CMD"
      PYTHON_CMD="$VENV_PYTHON_BIN"

      ok "Virtual environment activated"
      ;;
    *)
      warn "Using system Python"
      ;;
  esac
}


###############################################################################
# Clear pip cache
###############################################################################
clear_pip_cache() {
  ask "Do you want to clear the pip cache? This can help with slow or failed installs" "y" clear_cache
  if [[ "$clear_cache" =~ ^[Yy]$ ]]; then
    step "Clearing pip cache..."
    "$PYTHON_CMD" -m pip cache purge || true
    ok "Pip cache cleared"
  else
    warn "Skipping pip cache clear"
  fi
}


###############################################################################
# Install dependencies (optimized)
###############################################################################
install_requirements() {
  step "Preparing dependency installation (NumPy compatibility fix)..."

  # Hard pin NumPy < 2 to avoid pyarrow binary crash
  "$PYTHON_CMD" -m pip install --upgrade pip setuptools wheel
  "$PYTHON_CMD" -m pip install "numpy<2"

  ok "NumPy pinned to < 2 (pyarrow compatibility)"

  step "Installing Python dependencies..."

  "$PYTHON_CMD" -m pip install \
    --prefer-binary \
    --no-build-isolation \
    -r requirements.txt

  ok "Dependencies installed"
}


###############################################################################
# Verify pyarrow installation
###############################################################################
verify_pyarrow() {
  step "Verifying pyarrow installation..."

  if ! "$PYTHON_CMD" - <<'EOF'
import pyarrow, numpy
print("pyarrow:", pyarrow.__version__)
print("numpy:", numpy.__version__)
EOF
  then
    err "pyarrow failed to load"
    err "This system may not support current wheels"
    err "Please ensure Python 3.11 and NumPy < 2"
    exit 1
  fi

  ok "pyarrow verified"
}


create_env_template() {
  ENV_TEMPLATE="$PROJECT_ROOT/.env.template"
  if [ ! -f "$ENV_TEMPLATE" ]; then
    step "Creating .env.template file..."
    cat > "$ENV_TEMPLATE" <<EOL
# Pixella Environment Configuration
# copy this file to .env and fill in your values
# required fields are marked with required
GOOGLE_API_KEY=          # your Google API key (required)
GOOGLE_AI_MODEL=gemini-2.5-flash  # Google AI model to use
USERNAME=                # your username (optional)
USER_PERSONA=           # your persona or hobby (optional)
ALWAYS_DEBUG=false      # set to true to always enable debug mode
DISABLE_COLORS=false    # set to true to disable colored output
EMBEDDING_MODEL=models/embedding-001  # embedding model path
MEMORY_PATH=$PROJECT_ROOT/data/memory  # path to memory storage
MODELS_CACHE_DIR=$PROJECT_ROOT/models  # path to models cache directory
DB_PATH=$PROJECT_ROOT/db/chroma  # path to SQLite database file
EOL
    ok ".env.template created"
  else
    warn ".env.template already exists, skipping creation"
  fi

}


###############################################################################
# Environment setup
###############################################################################
setup_env_file() {
  step "Environment configuration..."

  ENV_FILE="$PROJECT_ROOT/.env"
  ENV_TEMPLATE="$PROJECT_ROOT/.env.template"

  # Ensure template exists
  if [ ! -f "$ENV_TEMPLATE" ]; then
    err ".env.template not found. This should not happen."
    exit 1
  fi

  # Create .env from template if it doesn't exist
  if [ ! -f "$ENV_FILE" ]; then
    step "Creating .env from .env.template..."
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    ok ".env created"
  else
    warn ".env already exists, preserving user values"
  fi

  # Helper to set or append env vars
  set_env_var() {
    local key="$1"
    local value="$2"

    if grep -q "^${key}=" "$ENV_FILE"; then
      sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
    else
      echo "${key}=${value}" >> "$ENV_FILE"
    fi
  }

  # GOOGLE_API_KEY
  ask "Enter Google API Key (required)" "" API_KEY
  if [ -n "$API_KEY" ]; then
    set_env_var "GOOGLE_API_KEY" "$API_KEY"
    ok "GOOGLE_API_KEY set"
  else
    warn "No API key provided (Pixella may not work)"
  fi

  # GOOGLE_AI_MODEL
  ask "Enter Google AI Model" "gemini-2.5-flash" AI_MODEL
  if [ -n "$AI_MODEL" ]; then
    set_env_var "GOOGLE_AI_MODEL" "$AI_MODEL"
    ok "AI model set to $AI_MODEL"
  else
    warn "No AI model provided, using default(gemini-2.5-flash)"
  fi

  # USERNAME
  ask "Enter your username (optional)" "" USERNAME
  if [ -n "$USERNAME" ]; then
    set_env_var "USERNAME" "$USERNAME"
    ok "USERNAME set to $USERNAME"
  else
    warn "No username provided, you may set it later in .env"
  fi

  # USER_PERSONA
  ask "Enter your persona or hobby (optional)" "" PERSONA
  if [ -n "$PERSONA" ]; then
    set_env_var "USER_PERSONA" "$PERSONA"
    ok "USER_PERSONA set to $PERSONA"
  else
    warn "No persona provided, you may set it later in .env"
  fi

}

###############################################################################
# PATH export (UNCHANGED)
###############################################################################
export_to_path() {
  step "Configuring PATH..."

  BIN_DIR="$PROJECT_ROOT/bin"

  # Detect user shell
  USER_SHELL="$(basename "$SHELL")"
  case "$USER_SHELL" in
    bash)
      [ -f "$HOME/.bashrc" ] && SHELL_RC="$HOME/.bashrc" || SHELL_RC="$HOME/.bash_profile"
      ;;
    zsh)
      SHELL_RC="$HOME/.zshrc"
      ;;
    fish)
      SHELL_RC="$HOME/.config/fish/config.fish"
      ;;
    *)
      SHELL_RC="$HOME/.profile"
      ;;
  esac

  # Check if already exported
  if grep -q "# added by Pixella Chatbot install script" "$SHELL_RC" 2>/dev/null; then
    ok "PATH already configured in $SHELL_RC"
    return
  fi

  # Append export block
  {
    echo ""
    echo "# added by Pixella Chatbot install script"
    case "$USER_SHELL" in
      fish)
        echo "set -gx PATH $BIN_DIR \$PATH"
        ;;
      *)
        echo "export PATH=\"$BIN_DIR:\$PATH\""
        ;;
    esac
  } >> "$SHELL_RC"

  ok "PATH updated in $SHELL_RC"
  warn "Restart terminal or run: source $SHELL_RC"
}

###############################################################################
# Finish
###############################################################################
finish() {
  print ""
  print "${GREEN}══════════════════════════════════════════════════════"
  print "✓ Pixella installation complete!"
  print "══════════════════════════════════════════════════════${NC}"
  print ""
  print "Try:"
  print "  pixella --help"
}

###############################################################################
# Main
###############################################################################
main() {
  print_header
  print_user_preview

  detect_os
  detect_installation_mode
  check_git
  select_version
  check_python_version

  [ "$INSTALLATION_MODE" = "remote" ] && clone_repository

  cd "$PROJECT_ROOT"
  if [ ! -f "requirements.txt" ]; then
    err "Invalid Pixella project structure. please report this error on GitHub, We'll fix it"
    exit 1
  fi

  update_bin_pixella
  create_and_activate_venv
  clear_pip_cache
  install_requirements
  verify_pyarrow
  create_env_template
  setup_env_file
  export_to_path
  finish
}

main "$@"
