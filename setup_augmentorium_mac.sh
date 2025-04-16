#!/bin/bash
# === Augmentorium Mac Setup Script ===
# This script checks for Python 3, Node.js, Homebrew, and Supervisor, installs dependencies, and registers Supervisor to auto-start on boot (using launchd).

set -e

# --- Check for root privileges ---
if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root. Use: sudo ./setup_augmentorium_mac.sh"
  exit 1
fi

# === Check for Homebrew ===
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is not installed. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$($(brew --prefix)/bin/brew shellenv)"' >> /Users/$(logname)/.zprofile
  eval "$($(brew --prefix)/bin/brew shellenv)"
fi

# === Check for Python 3 ===
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Installing Python 3 via Homebrew..."
  brew install python
fi

# === Check for Node.js ===
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is not installed. Installing Node.js using Homebrew..."
  brew install node
fi

# === (Optional) Create/activate virtual environment ===
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# === Install Python dependencies ===
pip install --upgrade pip
pip install -r requirements.txt

# === Ensure Supervisor is installed ===
pip show supervisor >/dev/null 2>&1 || pip install supervisor

# === Register Supervisor as a launchd service ===
SUPERVISORD_PATH="$(pwd)/.venv/bin/supervisord"
PLIST_FILE="/Library/LaunchDaemons/com.augmentorium.supervisor.plist"
cat <<EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.augmentorium.supervisor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SUPERVISORD_PATH</string>
        <string>-c</string>
        <string>$(pwd)/supervisord.conf</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>UserName</key>
    <string>$(logname)</string>
    <key>StandardOutPath</key>
    <string>$(pwd)/supervisord.log</string>
    <key>StandardErrorPath</key>
    <string>$(pwd)/supervisord.err</string>
</dict>
</plist>
EOF

chown root:wheel "$PLIST_FILE"
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

# === Open the frontend in the default web browser (if possible) ===
if command -v open >/dev/null 2>&1; then
  open http://localhost:6656 &
fi

echo "\nSetup complete!"
echo "The Augmentorium backend, indexer, and frontend will now be managed by Supervisor as a launchd service."
echo "You can check the status with: sudo launchctl list | grep augmentorium"
