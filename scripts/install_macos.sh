#!/bin/bash
# Installation script for Augmentorium on macOS

set -e

# Configuration
VENV_PATH="$HOME/.augmentorium/venv"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
TREE_SITTER_DIR="$HOME/.augmentorium/tree-sitter-grammars"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}     Augmentorium Installer for macOS       ${NC}"
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
mkdir -p "$LAUNCHD_DIR"

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

# Create launchd plist files
echo -e "${YELLOW}Creating launchd plist files...${NC}"

# Indexer service
cat > "$LAUNCHD_DIR/com.augmentorium.indexer.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.augmentorium.indexer</string>
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_PATH}/bin/augmentorium-indexer</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>${HOME}/.augmentorium/logs/indexer-error.log</string>
    <key>StandardOutPath</key>
    <string>${HOME}/.augmentorium/logs/indexer-output.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF

# Server service
cat > "$LAUNCHD_DIR/com.augmentorium.server.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.augmentorium.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_PATH}/bin/augmentorium-server</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>${HOME}/.augmentorium/logs/server-error.log</string>
    <key>StandardOutPath</key>
    <string>${HOME}/.augmentorium/logs/server-output.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
    </dict>
</dict>
</plist>
EOF

# Load services
echo -e "${YELLOW}Loading services...${NC}"
launchctl load "$LAUNCHD_DIR/com.augmentorium.indexer.plist"
launchctl load "$LAUNCHD_DIR/com.augmentorium.server.plist"

# Create command aliases
echo -e "${YELLOW}Creating command aliases...${NC}"
SHELL_PROFILE=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_PROFILE="$HOME/.profile"
fi

if [ -n "$SHELL_PROFILE" ]; then
    echo -e "${YELLOW}Adding aliases to $SHELL_PROFILE...${NC}"
    cat >> "$SHELL_PROFILE" << EOF

# Augmentorium aliases
alias augmentorium-start="launchctl load $LAUNCHD_DIR/com.augmentorium.indexer.plist $LAUNCHD_DIR/com.augmentorium.server.plist"
alias augmentorium-stop="launchctl unload $LAUNCHD_DIR/com.augmentorium.indexer.plist $LAUNCHD_DIR/com.augmentorium.server.plist"
alias augmentorium-restart="augmentorium-stop && augmentorium-start"
alias augmentorium-logs="tail -f $HOME/.augmentorium/logs/indexer-output.log $HOME/.augmentorium/logs/server-output.log"
alias augmentorium-setup="$VENV_PATH/bin/augmentorium-setup"
EOF
else
    echo -e "${YELLOW}Could not find shell profile file. Please add aliases manually.${NC}"
fi

# Create helper scripts
echo -e "${YELLOW}Creating helper scripts...${NC}"
mkdir -p "$HOME/.augmentorium/bin"

# Start script
cat > "$HOME/.augmentorium/bin/augmentorium-start.sh" << EOF
#!/bin/bash
launchctl load "$LAUNCHD_DIR/com.augmentorium.indexer.plist"
launchctl load "$LAUNCHD_DIR/com.augmentorium.server.plist"
echo "Augmentorium services started."
EOF

# Stop script
cat > "$HOME/.augmentorium/bin/augmentorium-stop.sh" << EOF
#!/bin/bash
launchctl unload "$LAUNCHD_DIR/com.augmentorium.indexer.plist"
launchctl unload "$LAUNCHD_DIR/com.augmentorium.server.plist"
echo "Augmentorium services stopped."
EOF

# Make scripts executable
chmod +x "$HOME/.augmentorium/bin/augmentorium-start.sh"
chmod +x "$HOME/.augmentorium/bin/augmentorium-stop.sh"

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
echo -e "  ${YELLOW}augmentorium-restart${NC} - Restart services"
echo -e "  ${YELLOW}augmentorium-logs${NC} - View service logs"
echo -e ""
echo -e "To set up a new project, use:"
echo -e "  ${YELLOW}augmentorium-setup PATH_TO_PROJECT${NC}"
echo -e ""
echo -e "Please restart your terminal or run '${YELLOW}source $SHELL_PROFILE${NC}' to use the aliases."
echo -e ""
echo -e "${GREEN}Enjoy using Augmentorium!${NC}"

# Deactivate virtual environment
deactivate
