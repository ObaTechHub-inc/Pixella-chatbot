#!/bin/bash

###############################################################################
#                                                                             #
#  PIXELLA - Installation & Setup Script                                     #
#  Automated installation, configuration, and PATH export                    #
#  Repository: https://github.com/DominionDev-coder/Pixella-chatbot          #
#                                                                             #
###############################################################################

set -e  # Exit on any error

exec </dev/tty || true

# Determine if running in interactive mode
INTERACTIVE=1
if [ ! -t 0 ] && [ ! -t 1 ]; then
    INTERACTIVE=0
fi

# Function to ask user for input with default value
ask() {
    local prompt="$1"
    local default="$2"
    local var="$3"
    local input=""

    if [ "$INTERACTIVE" -ne 1 ]; then
        eval "$var=\"$default\""
        [ -n "$default" ] && print_warning "$prompt [$default] (auto)"
        return
    fi

    printf '%s' "$prompt" > /dev/tty
    [ -n "$default" ] && printf ' [%s]' "$default" > /dev/tty
    printf ': ' > /dev/tty

    if read -r input < /dev/tty; then
        eval "$var=\"${input:-$default}\""
    else
        eval "$var=\"$default\""
    fi
}


# Trap to cleanup on error
trap 'cleanup_on_error' ERR

cleanup_on_error() {
    print_error "Installation failed. Cleaning up..."
    if [ "$INSTALLATION_MODE" = "remote" ] && [ -d "$PROJECT_ROOT" ]; then
        rm -rf "$PROJECT_ROOT" 2>/dev/null || true
    fi
    exit 1
}

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Repository details
REPO_URL="https://github.com/DominionDev-coder/Pixella-chatbot"
REPO_NAME="Pixella-chatbot"
INSTALL_DIR="${HOME}/.pixella"
VERSION=""  # Will be set by user selection

# Global variables for OS and Python
OS_TYPE=""
PYTHON_CMD=""
VENV_DIR=""  # Will be set by create_and_activate_venv
VENV_ACTIVATE_CMD=""
VENV_PYTHON_BIN=""

# Version list - Update this when new releases are available
VERSION_LIST="v1.0.0 v1.20.0 v1.20.4 v1.20.5 v1.20.7"

# Function to check if version exists in list
version_exists() {
    local version="$1"
    for v in $VERSION_LIST; do
        if [ "$v" = "$version" ]; then
            return 0
        fi
    done
    return 1
}

# Function to compare two version strings (returns true if first > second)
version_greater() {
    local v1="$1"
    local v2="$2"

    # Remove 'v' prefix for comparison
    v1="${v1#v}"
    v2="${v2#v}"

    # Split versions into arrays
    IFS='.' read -ra VER1 <<< "$v1"
    IFS='.' read -ra VER2 <<< "$v2"

    # Compare each part
    for i in 0 1 2; do
        local part1="${VER1[$i]:-0}"
        local part2="${VER2[$i]:-0}"

        if [ "$part1" -gt "$part2" ]; then
            return 0  # v1 > v2
        elif [ "$part1" -lt "$part2" ]; then
            return 1  # v1 < v2
        fi
    done

    return 1  # equal or v1 <= v2
}

# Function to safely checkout a version with proper error handling
checkout_version() {
    local version="$1"
    local current_version

    current_version=$(git describe --tags --dirty --always 2>/dev/null || echo "unknown")

    git fetch --tags --force

    if git rev-parse "$version" >/dev/null 2>&1; then
        print_step "Switching to version $version..."
        if git checkout "$version" 2>/dev/null; then
            print_success "Switched to version $version"
            return 0
        else
            print_error "Failed to checkout $version"
            return 1
        fi
    else
        print_warning "Tag $version not found, staying on current ($current_version)"
        VERSION="$current_version"
        return 1
    fi
}

# Functions
# Portable print function that works with both bash and POSIX sh
print() {
    printf '%b\n' "$1"
}

print_header() {
    print "\n${CYAN}════════════════════════════════════════════════════════════${NC}"
    print "${CYAN}      🤖 PIXELLA - Installation & Setup Script${NC}"
    print "${CYAN}════════════════════════════════════════════════════════════${NC}\n"
}

print_step() {
    print "${BLUE}→${NC} $1"
}

print_success() {
    print "${GREEN}✓ $1${NC}"
}

print_warning() {
    print "${YELLOW}⚠${NC} $1"
}

print_error() {
    print "${RED}✗ $1${NC}"
}

detect_os() {
    print_step "Detecting operating system..."
    case "$(uname -s)" in
        Linux*) 
            OS_TYPE="Linux"
            VENV_ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
            VENV_PYTHON_BIN="$VENV_DIR/bin/python"
            print_success "Detected Linux"
            ;;
        Darwin*) 
            OS_TYPE="macOS"
            VENV_ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
            VENV_PYTHON_BIN="$VENV_DIR/bin/python"
            print_success "Detected macOS"
            ;;
        CYGWIN*|MINGW32*|MSYS*|windows*) 
            OS_TYPE="Windows"
            # WSL/Git Bash compatible activation
            VENV_ACTIVATE_CMD="source \"$VENV_DIR/Scripts/activate\""
            VENV_PYTHON_BIN="$VENV_DIR/Scripts/python.exe" # Use python.exe for clarity
            print_warning "Detected Windows. Using WSL/Git Bash compatible commands."
            print_warning "For native PowerShell/CMD, manual steps may be needed for PATH."
            ;;
        *)
            print_error "Unsupported OS: $(uname -s)"
            exit 1
            ;;
    esac
}

# Detect if we're running from inside the cloned repo or standalone
detect_installation_mode() {
    print_step "Detecting installation mode..."
    
    # Check if install.sh is in scripts/ subdirectory of a repo
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    SCRIPT_PARENT="$(dirname "$SCRIPT_DIR")"
    
    if [ -f "$SCRIPT_PARENT/requirements.txt" ] && [ -f "$SCRIPT_PARENT/main.py" ]; then
        # We're inside the cloned repo
        PROJECT_ROOT="$SCRIPT_PARENT"
        INSTALLATION_MODE="local"
        print_success "Local installation detected (already in cloned repo: $PROJECT_ROOT)"
    else
        # We're standalone - need to clone
        INSTALLATION_MODE="remote"
        PROJECT_ROOT="$INSTALL_DIR"
        print_success "Standalone installation mode (will clone repo)"
    fi
}

# Function to resolve version input
resolve_version() {
    local input="$1"

    # Get available versions dynamically
    local available_versions=""
    if [ -d "$PROJECT_ROOT" ]; then
        cd "$PROJECT_ROOT"
        git fetch --tags --force >/dev/null 2>&1
        available_versions=$(git tag 2>/dev/null | tr '\n' ' ')
        cd - >/dev/null
    else
        # Fallback to hardcoded list if repo not cloned yet
        available_versions="$VERSION_LIST"
    fi

    # Handle special keywords
    if [ "$input" = "latest" ]; then
        # Find the latest version from available versions (highest version number)
        local latest=""
        for v in $available_versions; do
            if [ -z "$latest" ] || version_greater "$v" "$latest"; then
                latest="$v"
            fi
        done
        echo "$latest"
        return 0
    elif [ "$input" = "prerelease" ]; then
        # Find the prerelease version (lowest version number, typically earliest version)
        local prerelease=""
        for v in $available_versions; do
            if [ -z "$prerelease" ] || version_greater "$prerelease" "$v"; then
                prerelease="$v"
            fi
        done
        echo "$prerelease"
        return 0
    fi

    # Check if input already has v prefix
    case "$input" in
        v*)
            # Input already has v prefix, check if it exists
            for v in $available_versions; do
                if [ "$v" = "$input" ]; then
                    echo "$input"
                    return 0
                fi
            done
            ;;
        *)
            # Input doesn't have v prefix, try with v prefix
            local v_input="v$input"
            for v in $available_versions; do
                if [ "$v" = "$v_input" ]; then
                    echo "$v_input"
                    return 0
                fi
            done
            ;;
    esac

    # Handle partial versions (e.g., "1.20" -> latest in v1.20.x)
    if echo "$input" | grep -q '^[0-9]\+\.[0-9]\+$'; then
        local latest_version=""
        local v_prefix="v$input"
        for version in $available_versions; do
            case "$version" in
                "$v_prefix".*)
                    if [ -z "$latest_version" ] || version_greater "$version" "$latest_version"; then
                        latest_version="$version"
                    fi
                    ;;
            esac
        done
        if [ -n "$latest_version" ]; then
            echo "$latest_version"
            return 0
        fi
    fi

    # If no match found
    echo ""
    return 1
}

select_version() {
    print_step "Selecting Pixella version..."

    # First clone/fetch repository to get available versions
    if [ ! -d "$PROJECT_ROOT" ]; then
        print_step "Fetching available versions from repository..."
        mkdir -p "$INSTALL_DIR" || {
            print_error "Failed to create installation directory $INSTALL_DIR"
            exit 1
        }

        # Clone to temporary location to get tags
        TEMP_DIR=$(mktemp -d)
        if git clone "$REPO_URL" "$TEMP_DIR" 2>/dev/null; then
            cd "$TEMP_DIR"
            git fetch --tags --force >/dev/null 2>&1

            print "${CYAN}Available versions:${NC}"
            git tag | sort -V | while read -r tag; do
                echo "  $tag"
            done
            echo

            cd - >/dev/null
            rm -rf "$TEMP_DIR"
        else
            print_warning "Could not fetch versions from repository, using cached list"
            print "${CYAN}Available versions:${NC}"
            echo "  v1.0.0   (prerelease)"
            echo "  v1.20.0, v1.20.4, v1.20.5, v1.20.7  (latest: v1.20.7)"
            echo
        fi
    else
        cd "$PROJECT_ROOT"
        git fetch --tags --force >/dev/null 2>&1

        print "${CYAN}Available versions:${NC}"
        git tag | sort -V | while read -r tag; do
            echo "  $tag"
        done
        echo
        cd - >/dev/null
    fi

    print "${CYAN}You can specify:${NC}"
    echo "  - 'latest' -> gets the latest stable version"
    echo "  - 'prerelease' -> gets the prerelease version"
    echo

    while true; do
        ask "Enter version" "latest" input
        if [ -z "$input" ]; then
            print "${RED}Version cannot be empty.${NC}"
            continue
        fi

        VERSION=$(resolve_version "$input")
        if [ -n "$VERSION" ]; then
            print_success "Selected version: $VERSION"
            break
        else
            print "${RED}Invalid version '$input'. Please try again.${NC}"
            print "${YELLOW}Available options: latest, prerelease, or specific version tags shown above${NC}"
        fi
    done
}

clone_repository() {
    print_step "Cloning Pixella repository..."

    if [ -d "$PROJECT_ROOT" ]; then
        print_success "Local installation detected (already in cloned repo: $PROJECT_ROOT)"
        ask "Do you want to update it?" "y" REPLY
        echo

        case $REPLY in
            [Yy]* )
                cd "$PROJECT_ROOT" || {
                    print_error "Failed to change to directory $PROJECT_ROOT"
                    exit 1
                }

                git fetch origin
                git fetch --tags --force

                if ! git pull origin main 2>/dev/null; then
                    print_warning "Git pull failed, using existing files"
                fi

                checkout_version "$VERSION"
                ;;
            * )
                print_success "Using existing installation at $PROJECT_ROOT"
                cd "$PROJECT_ROOT" || exit 1

                git fetch --tags --force

                checkout_version "$VERSION"
                ;;
        esac
    else
        mkdir -p "$INSTALL_DIR" || {
            print_error "Failed to create installation directory $INSTALL_DIR"
            exit 1
        }

        echo "$VERSION" > "$INSTALL_DIR/.pixella_version" 2>/dev/null || true

        if ! git clone "$REPO_URL" "$PROJECT_ROOT"; then
            print_error "Failed to clone repository from $REPO_URL"
            exit 1
        fi

        cd "$PROJECT_ROOT" || exit 1

        # 🔑 CRITICAL FIX: ensure tags exist
        git fetch --tags --force

        if ! checkout_version "$VERSION"; then
            print_error "Version tag $VERSION not found."
            print_error "Available tags:"
            git tag
            exit 1
        fi
    fi

    print_success "Repository ready at $PROJECT_ROOT (version $VERSION)"
}

manual_python_installation() {
    print_step "Manual Python Installation"
    print_warning "Please download and install Python 3.11 from python.org"
    
    while true; do
        ask "Have you installed Python 3.11?" "n" REPLY
        echo
        case $REPLY in
            [Yy]* )
            if command -v python3.11 &> /dev/null; then
                print_success "Python 3.11 is now installed."
                PYTHON_CMD="python3.11"
                return 0
            else
                print_error "Python 3.11 not found in PATH."
                ask "Continue with another Python version?" "y" REPLY
                echo
                case $REPLY in
                    [Nn]* )
                        cleanup_and_abort
                        ;;
                    * )
                        return 1
                        ;;
                esac
            fi
            ;;
            [Nn]* )
            ask "Continue with another Python version?" "y" REPLY
            echo
            case $REPLY in
                [Nn]* )
                    cleanup_and_abort
                    ;;
                * )
                    return 1
                    ;;
            esac
            ;;
        esac
    done
}

install_python3_11() {
    print_step "Attempting to install Python 3.11..."
    
    case "$OS_TYPE" in
        macOS) 
            if ! command -v brew &> /dev/null; then
                print_error "Homebrew not found. Please install Homebrew first."
                return 1
            fi
            brew install python@3.11
            ;; 
        Linux) 
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y python3.11
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y python3.11
            elif command -v yum &> /dev/null; then
                sudo yum install -y python3.11
            else
                print_error "Unsupported Linux distribution."
                return 1
            fi
            ;; 
        Windows) 
            print_error "Automatic installation of Python on Windows is not supported."
            return 1
            ;; 
    esac
    
    if command -v python3.11 &> /dev/null; then
        print_success "Python 3.11 installed successfully."
        PYTHON_CMD="python3.11"
        return 0
    else
        print_error "Python 3.11 installation failed."
        manual_python_installation
        return $?
    fi
}

check_python_version() {
    print_step "Checking for a compatible Python version..."
    
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_success "Found recommended Python version: $PYTHON_CMD"
        return
    fi

    print_warning "Python 3.11 is recommended."
    ask "Python 3.11 not found. Install it now?" "y" REPLY
    echo
    case $REPLY in
        [Yy]* )
        install_python3_11
        if [ $? -ne 0 ]; then
            # If installation fails and user wants to continue with another version
            for cmd in python3.12 python3.13; do
                if command -v "$cmd" &> /dev/null; then
                    PYTHON_CMD="$cmd"
                    print_success "Found compatible Python version: $PYTHON_CMD"
                    return
                fi
            done
        else
            return
        fi
        ;;
        * )
        ;;
    esac
    
    for cmd in python3.12 python3.13; do
        if command -v "$cmd" &> /dev/null; then
            PYTHON_CMD="$cmd"
            print_success "Found compatible Python version: $PYTHON_CMD"
            return
        fi
    done
    
    print_error "No compatible Python version found (tried 3.11, 3.12, 3.13)."
    cleanup_and_abort
}

cleanup_and_abort() {
    print_error "Installation aborted."
    if [ "$INSTALLATION_MODE" = "remote" ]; then
        print_step "Cleaning up cloned repository..."
        rm -rf "$PROJECT_ROOT"
        print_success "Cleanup complete."
    fi
    exit 1
}


check_python_dependencies() {
    # Check if required packages are installed in current Python environment
    local python_cmd="$1"
    
    # Try to import all key packages from requirements.txt
    if "$python_cmd" -c "
import chromadb
import langchain
import streamlit
import typer
import rich
import google.api_core
try:
    import langchain_google_genai
except ImportError:
    import langchain_google_genai
try:
    import dotenv
except ImportError:
    import python_dotenv
" 2>/dev/null; then
        return 0  # All dependencies found
    fi
    
    return 1  # Dependencies not found
}

create_and_activate_venv() {
    if [ "$INSTALLATION_MODE" = "local" ]; then
        # Local installation - check existing environments
        print_step "Checking Python environment and dependencies..."
        
        # Check for existing virtual environment
        local venv_found=""
        if [ -d ".venv" ]; then
            VENV_DIR=".venv"
            venv_found="yes"
        elif [ -d "venv" ]; then
            VENV_DIR="venv"
            venv_found="yes"
        fi
        
        if [ -n "$venv_found" ]; then
            print_success "Found existing virtual environment ($VENV_DIR)"
            
            # Set activation commands based on OS
            if [ "$OS_TYPE" = "Windows" ]; then
                VENV_ACTIVATE_CMD="source \"$VENV_DIR/Scripts/activate\""
                VENV_PYTHON_BIN="$VENV_DIR/Scripts/python.exe"
            else
                VENV_ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
                VENV_PYTHON_BIN="$VENV_DIR/bin/python"
            fi
            
            # Try to activate and check dependencies
            if eval "$VENV_ACTIVATE_CMD" 2>/dev/null; then
                if check_python_dependencies "$VENV_PYTHON_BIN"; then
                    print_success "Virtual environment has required dependencies."
                    PYTHON_CMD="$VENV_PYTHON_BIN"
                    
                    # Even if everything is good, ask about version update
                    echo
                    ask "Do you want to update or downgrade Pixella version?" "n" REPLY
                    echo
                    case $REPLY in
                        [Yy]* )
                        # Check current version
                        local current_version=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
                        print "${CYAN}Current version: $current_version${NC}"
                        select_version
                        
                        # If user selected a different version, checkout and update
                        if [ "$VERSION" != "$current_version" ]; then
                            print_step "Switching to version $VERSION..."
                            if git checkout "$VERSION" 2>/dev/null; then
                                print_success "Switched to version $VERSION"
                                # Reinstall dependencies for new version
                                print_step "Reinstalling dependencies for new version..."
                                "$PYTHON_CMD" -m pip install --upgrade pip setuptools wheel
                                "$PYTHON_CMD" -m pip install -r "$PROJECT_ROOT/requirements.txt"
                                print_success "Dependencies updated"
                            else
                                print_warning "Could not checkout version $VERSION, staying on current"
                                VERSION="$current_version"
                            fi
                        fi
                        ;;
                        * )
                        ;;
                    esac
                    
                    return 0
                else
                    print_warning "Virtual environment exists but missing dependencies."
                    eval "deactivate" 2>/dev/null || true
                fi
            else
                print_warning "Cannot activate existing virtual environment."
            fi
        fi
        
        # No working venv found, check system Python
        print_step "Checking system Python environment..."
        if check_python_dependencies "$PYTHON_CMD"; then
            print_success "System Python has required dependencies. Using system Python."
            return 0
        else
            print_warning "System Python missing required dependencies."
        fi
        
        # Neither venv nor system has dependencies - offer solutions
        echo
        echo "Choose installation option:"
        echo "1. Create virtual environment (.venv) and install dependencies"
        echo "2. Install dependencies in system Python (not recommended)"
        echo
        
        while true; do
            ask "Select option (1 or 2)" "1" choice
            case $choice in
                1)
                    print_step "Creating virtual environment (.venv)..."
                    VENV_DIR=".venv"
                    if [ "$OS_TYPE" = "Windows" ]; then
                        VENV_ACTIVATE_CMD="source \"$VENV_DIR/Scripts/activate\""
                        VENV_PYTHON_BIN="$VENV_DIR/Scripts/python.exe"
                    else
                        VENV_ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
                        VENV_PYTHON_BIN="$VENV_DIR/bin/python"
                    fi
                    
                    "$PYTHON_CMD" -m venv "$VENV_DIR" || {
                        print_error "Failed to create virtual environment"
                        exit 1
                    }
                    print_success "Virtual environment created."
                    
                    eval "$VENV_ACTIVATE_CMD" || {
                        print_error "Failed to activate virtual environment"
                        exit 1
                    }
                    print_success "Virtual environment activated."
                    
                    PYTHON_CMD="$VENV_PYTHON_BIN"
                    break
                    ;;
                2)
                    print_warning "Installing dependencies in system Python (not recommended)."
                    print_warning "This may affect other Python applications on your system."
                    ask "Are you sure?" "n" REPLY
                    echo
                    case $REPLY in
                        [Yy]* )
                        break
                        ;;
                    esac
                    # If not sure, loop back to choice
                    ;;
                *)
                    print "${RED}Invalid choice. Please select 1 or 2.${NC}"
                    ;;
            esac
        done
        
    else
        # Remote installation - ask about venv creation
        print_step "Setting up Python environment..."
        
        if [ -d ".venv" ]; then
            print_warning "Virtual environment already exists."
            ask "Do you want to recreate it?" "n" REPLY
            echo
            case $REPLY in
                [Yy]* )
                rm -rf ".venv"
                create_venv="yes"
                ;;
                * )
                # Try to reuse existing venv
                VENV_DIR=".venv"
                if [ "$OS_TYPE" = "Windows" ]; then
                    VENV_ACTIVATE_CMD="source \"$VENV_DIR/Scripts/activate\""
                    VENV_PYTHON_BIN="$VENV_DIR/Scripts/python.exe"
                else
                    VENV_ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
                    VENV_PYTHON_BIN="$VENV_DIR/bin/python"
                fi
                
                if eval "$VENV_ACTIVATE_CMD" 2>/dev/null; then
                    print_success "Reusing existing virtual environment."
                    PYTHON_CMD="$VENV_PYTHON_BIN"
                    return 0
                else
                    print_warning "Cannot activate existing venv, will create new one."
                    rm -rf ".venv"
                    create_venv="yes"
                fi
                ;;
            esac
        else
            echo "Do you want to create a virtual environment? (recommended)"
            echo "1. Yes, create virtual environment (.venv)"
            echo "2. No, use system Python"
            echo
            
            while true; do
                ask "Select option (1 or 2)" "1" choice
                case $choice in
                    1)
                        create_venv="yes"
                        break
                        ;;
                    2)
                        print_warning "Using system Python (not recommended)."
                        return 0
                        ;;
                    *)
                        print "${RED}Invalid choice. Please select 1 or 2.${NC}"
                        ;;
                esac
            done
        fi
        
        if [ "$create_venv" = "yes" ]; then
            VENV_DIR=".venv"
            if [ "$OS_TYPE" = "Windows" ]; then
                VENV_ACTIVATE_CMD="source \"$VENV_DIR/Scripts/activate\""
                VENV_PYTHON_BIN="$VENV_DIR/Scripts/python.exe"
            else
                VENV_ACTIVATE_CMD="source \"$VENV_DIR/bin/activate\""
                VENV_PYTHON_BIN="$VENV_DIR/bin/python"
            fi
            
            "$PYTHON_CMD" -m venv "$VENV_DIR" || {
                print_error "Failed to create virtual environment"
                exit 1
            }
            print_success "Virtual environment created."
            
            eval "$VENV_ACTIVATE_CMD" || {
                print_error "Failed to activate virtual environment"
                exit 1
            }
            print_success "Virtual environment activated."
            
            PYTHON_CMD="$VENV_PYTHON_BIN"
        fi
    fi
}


check_dependencies() {
    print_step "Checking system dependencies..."
    
    # Check for git if doing remote installation
    if [ "$INSTALLATION_MODE" = "remote" ]; then
        if ! command -v git &> /dev/null; then
            print_error "git is required for remote installation"
            print_error "Please install git and try again"
            exit 1
        fi
        print_success "git found"
    fi
    
    # Check for curl (for potential future use)
    if command -v curl &> /dev/null; then
        print_success "curl found"
    else
        print_warning "curl not found - some features may not work"
    fi
    
    # Check for basic commands
    local required_cmds=("mkdir" "cp" "rm" "echo" "cat")
    for cmd in "${required_cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "Required command '$cmd' not found"
            exit 1
        fi
    done
    print_success "Basic system commands available"
}

install_requirements() {
    print_step "Installing Python requirements..."
    
    if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_error "requirements.txt not found at $PROJECT_ROOT"
        exit 1
    fi
    
    $PYTHON_CMD -m pip install --upgrade pip setuptools wheel
    $PYTHON_CMD -m pip install -r "$PROJECT_ROOT/requirements.txt"
    
    print_success "Python packages installed"
}

setup_directories() {
    print_step "Setting up directories..."
    
    mkdir -p "$PROJECT_ROOT/bin"
    mkdir -p "$PROJECT_ROOT/db"
    mkdir -p "$PROJECT_ROOT/data"
    
    print_success "Directories created"
}

create_env_template() {
    print_step "Checking environment configuration..."
    
    if [ ! -f "$PROJECT_ROOT/.env.template" ]; then
        print_warning ".env.template not found, creating from config..."
        cd "$PROJECT_ROOT"
        $PYTHON_CMD -c "from config import generate_env_template; generate_env_template()" 2>/dev/null || print_warning "Could not auto-generate template"
    fi
}

setup_env_file() {
    print_step "Setting up environment file..."
    
    ENV_FILE="$PROJECT_ROOT/.env"
    
    if [ -f "$ENV_FILE" ]; then
        print_success ".env file already exists"
        return 0
    fi
    
    # Check for template
    if [ -f "$PROJECT_ROOT/.env.template" ]; then
        cp "$PROJECT_ROOT/.env.template" "$ENV_FILE"
        print_success "Created .env from template"
    else
        # Create minimal .env
        cat > "$ENV_FILE" << 'EOF'
# Pixella Configuration
GOOGLE_API_KEY=your-api-key-here
GOOGLE_AI_MODEL=gemini-1.5-flash
USER_NAME=User
USER_PERSONA=helpful-assistant
EOF
        print_success "Created minimal .env file"
    fi
    
    # Prompt for API key and update using a Python script for cross-platform compatibility
    echo
    ask "Enter your Google API Key (or press Enter to skip)" "" API_KEY
    if [ ! -z "$API_KEY" ]; then
        # Create a temporary Python script to update the .env file
        PYTHON_SCRIPT_PATH="$PROJECT_ROOT/scripts/update_env.py"
        mkdir -p "$(dirname "$PYTHON_SCRIPT_PATH")" # Ensure scripts directory exists
        cat > "$PYTHON_SCRIPT_PATH" << EOM
import os
import sys

def update_env_file(env_file, key_to_update, new_value):
    try:
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write(f"{key_to_update}={new_value}\n")
            return

        with open(env_file, 'r') as f:
            lines = f.readlines()

        updated = False
        with open(env_file, 'w') as f:
            for line in lines:
                if line.strip().startswith(f"{key_to_update}="):
                    f.write(f"{key_to_update}={new_value}\n")
                    updated = True
                else:
                    f.write(line)
            if not updated:
                f.write(f"{key_to_update}={new_value}\n")
    except Exception as e:
        print(f"Error updating .env file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python update_env.py <env_file_path> <key> <value>", file=sys.stderr)
        sys.exit(1)
    
    env_file = sys.argv[1]
    key_to_update = sys.argv[2]
    new_value = sys.argv[3]
    update_env_file(env_file, key_to_update, new_value)

EOM
        # Execute the Python script using the venv's python
        "$PYTHON_CMD" "$PYTHON_SCRIPT_PATH" "$ENV_FILE" "GOOGLE_API_KEY" "$API_KEY"
        rm "$PYTHON_SCRIPT_PATH" # Clean up the temporary script
        print_success "API key configured"
    fi
}

update_pixella_executable() {
    print_step "Updating pixella executable..."
    
    local pixella_executable="$PROJECT_ROOT/bin/pixella"
    
    # Escape for sed
    local escaped_python_cmd=$(printf '%s\n' "$PYTHON_CMD" | sed 's:[&/\\]:\\&:g')

    if [ -f "$pixella_executable" ]; then
        # Replace the placeholder with the correct python command
        sed -i.bak "s|PYTHON_CMD_PLACEHOLDER|$escaped_python_cmd|g" "$pixella_executable"
        rm "${pixella_executable}.bak"
        print_success "pixella executable updated to use $PYTHON_CMD"
    else
        print_warning "pixella executable not found. Skipping update."
    fi
}


export_to_path() {
    print_step "Configuring PATH..."
    
    BIN_DIR="$PROJECT_ROOT/bin"
    SHELL_RC=""
    
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    if [ -z "$SHELL_RC" ]; then
        print_warning "Could not determine shell configuration file"
        print_warning "Please manually add $BIN_DIR to your PATH"
        return 1
    fi
    
    # Check if already in PATH
    if grep -q "# added by pixella chatbot install script" "$SHELL_RC" 2>/dev/null; then
        print_success "Pixella PATH already configured in $SHELL_RC"
        return 0
    fi
    
    # Add to PATH
    echo "" >> "$SHELL_RC"
    echo "# added by pixella chatbot install script" >> "$SHELL_RC"
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
    
    print_success "Added to PATH ($SHELL_RC)"
    print_warning "Please restart your terminal or run 'source $SHELL_RC' to apply changes."
}

verify_installation() {
    print_step "Verifying installation..."
    
    cd "$PROJECT_ROOT"
    
    if $PYTHON_CMD main.py > /dev/null 2>&1; then
        print_success "Installation verified successfully"
        return 0
    else
        print_warning "Verification had warnings (this may be normal if dependencies are missing)"
        return 0
    fi
}

print_next_steps() {
    echo
    print "${CYAN}════════════════════════════════════════════════════════════${NC}"
    print "${CYAN}      ✓ Installation Complete!${NC}"
    print "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo
    echo "Next steps:"
    echo
    if [ "$INSTALLATION_MODE" = "remote" ]; then
        echo "1. Reload your shell configuration:"
        echo "   source $HOME/.zshrc  # or source $HOME/.bashrc"
        echo
    fi
    echo "2. Start using Pixella:"
    echo "   pixella --help               # View available commands"
    echo "   pixella cli --interactive    # Start interactive mode"
    echo "   pixella ui                   # Start web interface"
    echo
    echo "3. Configure Pixella:"
    echo "   pixella config --show        # View current settings"
    echo "   $PROJECT_ROOT/.env          # Edit configuration file"
    echo
    echo "Documentation: https://github.com/DominionDev-coder/Pixella-chatbot"
    echo
}

# Main installation flow
main() {
    print_header
    
    detect_os
    detect_installation_mode
    
    # Ask for version selection in both local and remote modes
    if [ "$INSTALLATION_MODE" = "local" ]; then
        print "${CYAN}Local installation detected.${NC}"
        echo "You can select a specific version to use or stay on current."
        select_version
        
        # For local mode, checkout the selected version if different from current
        local current_version=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        if [ "$VERSION" != "$current_version" ] && [ "$VERSION" != "main" ] && [ "$VERSION" != "latest" ]; then
            print_step "Switching to version $VERSION..."
            if git checkout "$VERSION" 2>/dev/null; then
                print_success "Switched to version $VERSION"
            else
                print_warning "Could not checkout version $VERSION, staying on current ($current_version)"
                VERSION="$current_version"
            fi
        fi
    else
        # Check if user has installed before
        if [ -f "$INSTALL_DIR/.pixella_version" ]; then
            local saved_version=$(cat "$INSTALL_DIR/.pixella_version" 2>/dev/null)
            if [ -n "$saved_version" ]; then
                print "${CYAN}Previous installation used version: $saved_version${NC}"
                echo "Do you want to:"
                echo "1. Keep the same version ($saved_version)"
                echo "2. Update/downgrade to a different version"
                echo
                
                while true; do
                    ask "Select option (1 or 2)" "1" choice
                    case $choice in
                        1)
                            VERSION="$saved_version"
                            print_success "Using version: $VERSION"
                            break
                            ;;
                        2)
                            select_version
                            break
                            ;;
                        *)
                            print "${RED}Invalid choice. Please select 1 or 2.${NC}"
                            ;;
                    esac
                done
            else
                select_version
            fi
        else
            select_version
        fi
    fi
    
    check_python_version
    check_dependencies
    
    # Clone if remote installation
    if [ "$INSTALLATION_MODE" = "remote" ]; then
        clone_repository
    fi
    
    cd "$PROJECT_ROOT"
    
    create_and_activate_venv
    
    update_pixella_executable

    setup_directories
    create_env_template
    setup_env_file
    install_requirements
    export_to_path
    verify_installation
    print_next_steps
}

# Run main function
main "$@"
