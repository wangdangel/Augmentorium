@echo off
echo Starting Indexer...
REM Use %~dp0 to ensure paths are relative to the script's location
start "Indexer" cmd.exe /k "call "%~dp0.venv\Scripts\activate.bat" & python "%~dp0scripts\run_indexer.py""

echo Starting Server...
REM Use %~dp0 to ensure paths are relative to the script's location
start "Server" cmd.exe /k "call "%~dp0.venv\Scripts\activate.bat" & python "%~dp0scripts\run_server.py""

echo Starting GUI (placeholder)...
REM Use %~dp0 to ensure paths are relative to the script's location
start "GUI Placeholder" cmd.exe /k "call "%~dp0.venv\Scripts\activate.bat" & echo GUI placeholder - not yet implemented"

echo All processes started in separate windows.