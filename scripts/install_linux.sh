#!/bin/bash
# Installation script for Augmentorium on Linux

set -e

# Configuration
VENV_PATH="$HOME/.augmentorium/venv"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
TREE_SITTER_DIR="$HOME/.augmentorium/tree-sitter-grammars"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}     Augmentorium Installer for Linux       ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check for required commands
echo -e "${YELLOW}Checking dependencies...${NC}"
MISSING_DEPS=0

if ! command_exists python3; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or newer.${NC}"
    MISSING_DEPS=1
fi

if ! command_exists pip3; then
    echo -e "${RED}pip is not installed. Please install pip.${NC}"
    MISSING_DEPS=1
fi

if ! command_exists git; then
    echo -e "${RED}git is not installed. Please install git.${NC}"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${RED}Please install the missing dependencies and run the installer again.${NC}"
    exit 1
fi

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$HOME/.augmentorium"
mkdir -p "$HOME/.augmentorium/logs"
mkdir -p "$TREE_SITTER_DIR"
mkdir -p "$SYSTEMD_USER_DIR"

# Create virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
else
    echo -e "${YELLOW}Virtual environment already exists. Skipping creation.${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Install or upgrade Augmentorium
if [ -z "$1" ]; then
    # No argument, install from PyPI
    echo -e "${YELLOW}Installing Augmentorium from PyPI...${NC}"
    pip install --upgrade augmentorium
else
    # Argument provided, install from directory
    echo -e "${YELLOW}Installing Augmentorium from $1...${NC}"
    pip install --upgrade "$1"
fi

# Create systemd service files
echo -e "${YELLOW}Creating systemd service files...${NC}"

# Indexer service
cat > "$SYSTEMD_USER_DIR/augmentorium-indexer.service" << EOF
[Unit]
Description=Augmentorium Indexer Service
After=network.target

[Service]
Type=simple
ExecStart=$VENV_PATH/bin/augmentorium-indexer
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

# Server service
cat > "$SYSTEMD_USER_DIR/augmentorium-server.service" << EOF
[Unit]
Description=Augmentorium MCP Server
After=network.target

[Service]
Type=simple
ExecStart=$VENV_PATH/bin/augmentorium-server
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

# Reload systemd
echo -e "${YELLOW}Reloading systemd...${NC}"
systemctl --user daemon-reload

# Enable services
echo -e "${YELLOW}Enabling services...${NC}"
systemctl --user enable augmentorium-indexer.service
systemctl --user enable augmentorium-server.service

# Create command aliases
echo -e "${YELLOW}Creating command aliases...${NC}"
SHELL_PROFILE=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_PROFILE="$HOME/.profile"
fi

if [ -n "$SHELL_PROFILE" ]; then
    echo -e "${YELLOW}Adding aliases to $SHELL_PROFILE...${NC}"
    cat >> "$SHELL_PROFILE" << EOF

# Augmentorium aliases
alias augmentorium-start="systemctl --user start augmentorium-indexer.service augmentorium-server.service"
alias augmentorium-stop="systemctl --user stop augmentorium-indexer.service augmentorium-server.service"
alias augmentorium-status="systemctl --user status augmentorium-indexer.service augmentorium-server.service"
alias augmentorium-logs="journalctl --user -fu augmentorium-indexer.service -fu augmentorium-server.service"
alias augmentorium-setup="$VENV_PATH/bin/augmentorium-setup"
EOF
else
    echo -e "${YELLOW}Could not find shell profile file. Please add aliases manually.${NC}"
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"
systemctl --user start augmentorium-indexer.service
systemctl --user start augmentorium-server.service

# Installation complete
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}     Augmentorium installation complete     ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Services are running in the background."
echo -e "You can manage them with the following commands:"
echo -e "  ${YELLOW}augmentorium-start${NC} - Start services"
echo -e "  ${YELLOW}augmentorium-stop${NC} - Stop services"
echo -e "  ${YELLOW}augmentorium-status${NC} - Check service status"
echo -e "  ${YELLOW}augmentorium-logs${NC} - View service logs"
echo -e ""
echo -e "To set up a new project, use:"
echo -e "  ${YELLOW}augmentorium-setup PATH_TO_PROJECT${NC}"
echo -e ""
echo -e "Please restart your shell or run '${YELLOW}source $SHELL_PROFILE${NC}' to use the aliases."
echo -e ""
echo -e "${GREEN}Enjoy using Augmentorium!${NC}"

# Deactivate virtual environment
deactivate
