#!/bin/bash
# === Augmentorium Linux Setup Script ===
# This script checks for Python 3, Node.js, and Supervisor, installs dependencies, and registers Supervisor to auto-start on boot.

set -e

# --- Check for root privileges ---
if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root. Use: sudo ./setup_augmentorium_linux.sh"
  exit 1
fi

# === Check for Python 3 ===
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed. Please install it using your package manager (e.g., sudo apt install python3)."
  exit 1
fi

# === Check for Node.js ===
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is not installed. Installing Node.js..."
  if command -v apt-get >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
  elif command -v yum >/dev/null 2>&1; then
    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
    yum install -y nodejs
  else
    echo "Please install Node.js manually."
    exit 1
  fi
fi

# === (Optional) Create/activate virtual environment ===
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# === Install Python dependencies ===
pip install --upgrade pip
pip install -r requirements.txt

# === Generate supervisord.conf with correct Linux paths ===
cat <<EOF > supervisord.conf
[supervisord]
logfile=supervisord.log
loglevel=info

[program:server]
environment=PROJECT_DIR="$(pwd)"
command=%(ENV_PROJECT_DIR)s/.venv/bin/python scripts/run_server.py
directory=%(ENV_PROJECT_DIR)s
autostart=true
autorestart=true
stdout_logfile=server.log
stderr_logfile=server.err.log

[program:indexer]
environment=PROJECT_DIR="$(pwd)"
command=%(ENV_PROJECT_DIR)s/.venv/bin/python scripts/run_indexer.py
directory=%(ENV_PROJECT_DIR)s
autostart=true
autorestart=true
stdout_logfile=indexer.log
stderr_logfile=indexer.err.log

[program:frontend]
environment=PROJECT_DIR="$(pwd)"
command=%(ENV_PROJECT_DIR)s/.venv/bin/python -m http.server 6656 --directory %(ENV_PROJECT_DIR)s/frontend/dist
directory=%(ENV_PROJECT_DIR)s/frontend/dist
autostart=true
autorestart=true
stdout_logfile=frontend.log
stderr_logfile=frontend.err.log
EOF

# === Ensure Supervisor is installed ===
pip show supervisor >/dev/null 2>&1 || pip install supervisor

# === Register Supervisor as a systemd service ===
SUPERVISORD_PATH="$(pwd)/.venv/bin/supervisord"
SERVICE_FILE="/etc/systemd/system/augmentorium-supervisor.service"
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Augmentorium Supervisor Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$(pwd)
ExecStart=$SUPERVISORD_PATH -c $(pwd)/supervisord.conf
Restart=always
User=$(logname)

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable augmentorium-supervisor.service
systemctl restart augmentorium-supervisor.service

# === Open the frontend in the default web browser (if possible) ===
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://localhost:6656 &
fi

echo "\nSetup complete!"
echo "The Augmentorium backend, indexer, and frontend will now be managed by Supervisor as a systemd service."
echo "You can check the status with: sudo systemctl status augmentorium-supervisor.service"
