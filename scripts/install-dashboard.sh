#!/bin/bash
# Installation script for Augmentorium Dashboard

set -e

# Configuration
ROOT_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
DASHBOARD_DIR="$ROOT_DIR/dashboard"
SERVER_DIR="$ROOT_DIR/server"
TEMP_DIR="/tmp/augmentorium-dashboard"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print header
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}     Augmentorium Dashboard Installer       ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check for required commands
echo -e "${YELLOW}Checking dependencies...${NC}"
MISSING_DEPS=0

if ! command_exists node; then
    echo -e "${RED}Node.js is not installed. Please install Node.js 14 or newer.${NC}"
    MISSING_DEPS=1
fi

if ! command_exists npm; then
    echo -e "${RED}npm is not installed. Please install npm.${NC}"
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
mkdir -p "$DASHBOARD_DIR"
mkdir -p "$SERVER_DIR/dashboard/build"

# Clone or update dashboard repository
if [ -d "$TEMP_DIR" ]; then
    echo -e "${YELLOW}Updating dashboard repository...${NC}"
    cd "$TEMP_DIR"
    git pull
else
    echo -e "${YELLOW}Cloning dashboard repository...${NC}"
    git clone https://github.com/yourusername/augmentorium-dashboard.git "$TEMP_DIR"
    cd "$TEMP_DIR"
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
npm install

# Build dashboard
echo -e "${YELLOW}Building dashboard...${NC}"
npm run build

# Copy build files
echo -e "${YELLOW}Copying dashboard files...${NC}"
cp -r build/* "$SERVER_DIR/dashboard/build/"

# Copy server files
echo -e "${YELLOW}Copying server files...${NC}"
cp src/server/dashboard.py "$SERVER_DIR/"

# Add dashboard to server/__init__.py
INIT_FILE="$SERVER_DIR/__init__.py"
if ! grep -q "from .dashboard import" "$INIT_FILE"; then
    echo -e "${YELLOW}Adding dashboard to server/__init__.py...${NC}"
    # Add import statement after the last import
    sed -i '/^from/a from .dashboard import start_dashboard' "$INIT_FILE"
    
    # Add export statement
    if grep -q "__all__ =" "$INIT_FILE"; then
        # Add to existing __all__ list
        sed -i 's/__all__ = \[/__all__ = \["start_dashboard", /' "$INIT_FILE"
    else
        # Add new __all__ list
        echo -e "\n__all__ = [\"start_dashboard\", \"start_server\"]" >> "$INIT_FILE"
    fi
fi

# Check for Flask and Flask-CORS
echo -e "${YELLOW}Checking for Flask and Flask-CORS...${NC}"
if ! pip show flask-cors &> /dev/null; then
    echo -e "${YELLOW}Installing Flask-CORS...${NC}"
    pip install flask-cors
fi

# Add dashboard to requirements.txt
REQUIREMENTS_FILE="$ROOT_DIR/requirements.txt"
if ! grep -q "flask-cors" "$REQUIREMENTS_FILE"; then
    echo -e "${YELLOW}Adding Flask-CORS to requirements.txt...${NC}"
    echo "flask-cors>=2.0.0" >> "$REQUIREMENTS_FILE"
fi

# Create a simple startup script for the dashboard
DASHBOARD_SCRIPT="$ROOT_DIR/scripts/start_dashboard.py"
echo -e "${YELLOW}Creating dashboard startup script...${NC}"
cat > "$DASHBOARD_SCRIPT" << EOF
#!/usr/bin/env python3
"""
Standalone script to start the Augmentorium dashboard
"""

import os
import sys
import logging
import argparse

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from augmentorium.config.manager import ConfigManager
from augmentorium.server.mcp import MCPServer
from augmentorium.server.dashboard import DashboardAPI
from augmentorium.utils.logging import setup_logging

def main():
    """Main entry point for dashboard"""
    parser = argparse.ArgumentParser(description="Augmentorium Dashboard")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                      default="INFO", help="Set the logging level")
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level)
    
    # Load configuration
    config = ConfigManager(args.config)
    
    # Create MCP server (without starting it)
    mcp_server = MCPServer(config)
    
    # Start dashboard
    dashboard_api = DashboardAPI(
        config_manager=config,
        mcp_server=mcp_server,
        host=args.host,
        port=args.port
    )
    
    # Run dashboard
    dashboard_api.run()

if __name__ == "__main__":
    main()
EOF

# Make the script executable
chmod +x "$DASHBOARD_SCRIPT"

# Add startup script to setup.py
SETUP_FILE="$ROOT_DIR/setup.py"
if ! grep -q "augmentorium-dashboard" "$SETUP_FILE"; then
    echo -e "${YELLOW}Adding dashboard script to setup.py...${NC}"
    # Add to entry_points console_scripts
    sed -i '/console_scripts/a \ \ \ \ \ \ \ \ "augmentorium-dashboard=augmentorium.scripts.start_dashboard:main",' "$SETUP_FILE"
fi

# Installation complete
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Augmentorium Dashboard installation complete   ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "You can start the dashboard with the following command:"
echo -e "  ${YELLOW}augmentorium-dashboard${NC}"
echo ""
echo -e "Or by running:"
echo -e "  ${YELLOW}python scripts/start_dashboard.py${NC}"
echo ""
echo -e "The dashboard will be available at http://localhost:8081"
echo ""
echo -e "${GREEN}Enjoy using Augmentorium Dashboard!${NC}"
