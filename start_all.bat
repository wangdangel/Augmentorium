@echo off
echo Starting Indexer...
REM Use %~dp0 to ensure paths are relative to the script's location
start "Indexer" cmd.exe /k "call "%~dp0.venv\Scripts\activate.bat" & python "%~dp0scripts\run_indexer.py""

echo Starting Server...
REM Use %~dp0 to ensure paths are relative to the script's location
start "Server" cmd.exe /k "call "%~dp0.venv\Scripts\activate.bat" & python "%~dp0scripts\run_server.py""

echo Starting Gooey (frontend)...
REM Start the frontend (Gooey) from the augmentorium\frontend folder using npx
start "Gooey" cmd.exe /k "cd /d "%~dp0frontend" && npm run dev"
echo All processes started in separate windows.