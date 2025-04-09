@echo off
echo Starting Indexer...
start "Indexer" cmd.exe /k "call .\.venv\Scripts\activate.bat & python scripts/run_indexer.py --config k:/Documents/augmentorium/config.yaml"

echo Starting Server...
start "Server" cmd.exe /k "call .\.venv\Scripts\activate.bat & python scripts\run_server.py"

echo Starting GUI (placeholder)...
start "GUI Placeholder" cmd.exe /k "call .\.venv\Scripts\activate.bat & echo GUI placeholder - not yet implemented"

echo All processes started in separate windows.
