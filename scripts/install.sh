#!/bin/bash

###############################################################################
#                                                                             #
#  PIXELLA - Installation & Setup Script                                     #
#  Automated installation, configuration, and PATH export                    #
#  Repository: https://github.com/DominionDev-coder/Pixella-chatbot          #
#                                                                             #
###############################################################################

set -e  # Exit on any error

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

# Functions
print_header() {
    echo -e "\n${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}      🤖 PIXELLA - Installation & Setup Script${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}\n"
}

print_step() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
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
        print_success "Local installation detected (already in cloned repo)"
    else
        # We're standalone - need to clone
        INSTALLATION_MODE="remote"
        PROJECT_ROOT="$INSTALL_DIR"
        print_success "Standalone installation mode (will clone repo)"
    fi
}

clone_repository() {
    print_step "Cloning Pixella repository..."
    
    if [ -d "$PROJECT_ROOT" ]; then
        print_warning "Pixella directory already exists at $PROJECT_ROOT"
        read -p "Do you want to update it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$PROJECT_ROOT"
            git pull origin main 2>/dev/null || print_warning "Git pull failed, will use existing files"
        else
            print_success "Using existing installation at $PROJECT_ROOT"
            return 0
        fi
    else
        mkdir -p "$INSTALL_DIR"
        git clone "$REPO_URL" "$PROJECT_ROOT" || {
            print_error "Failed to clone repository"
            print_error "Make sure git is installed and the URL is correct"
            exit 1
        }
    fi
    
    print_success "Repository ready at $PROJECT_ROOT"
}

check_python_version() {
    print_step "Checking Python version..."
    
    PYTHON_CMD=""
    
    for cmd in python3.11 python3.12 python3; do
        if command -v "$cmd" &> /dev/null; then
            VERSION=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
            if [[ "$VERSION" == "3.11" ]] || [[ "$VERSION" == "3.12" ]]; then
                PYTHON_CMD="$cmd"
                print_success "Found compatible Python version: $VERSION ($PYTHON_CMD)"
                break
            fi
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        print_error "Python 3.11 or 3.12 is required."
        print_error "Python 3.13 and above may have compatibility issues."
        exit 1
    fi
}

check_dependencies() {
    print_step "Checking system dependencies..."
    
    # Check for pip
    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        print_error "pip is not installed for $PYTHON_CMD"
        exit 1
    fi
    print_success "pip found"
    
    # Check for git if doing remote installation
    if [ "$INSTALLATION_MODE" = "remote" ]; then
        if ! command -v git &> /dev/null; then
            print_error "git is required for remote installation"
            exit 1
        fi
        print_success "git found"
    fi
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
    
    # Prompt for API key
    echo
    read -p "Enter your Google API Key (or press Enter to skip): " API_KEY
    if [ ! -z "$API_KEY" ]; then
        # Escape special characters for sed
        API_KEY_ESCAPED=$(printf '%s\n' "$API_KEY" | sed -e 's/[\/&]/\\&/g')
        sed -i '' "s/your-api-key-here/$API_KEY_ESCAPED/" "$ENV_FILE"
        print_success "API key configured"
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
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}      ✓ Installation Complete!${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
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
    
    detect_installation_mode
    
    check_python_version
    check_dependencies
    
    # Clone if remote installation
    if [ "$INSTALLATION_MODE" = "remote" ]; then
        clone_repository
    fi
    
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
