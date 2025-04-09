@echo off
REM Setup script for Augmentorium on Windows

echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Installing augmentorium in development mode...
pip install -e .

echo Virtual environment setup complete!
echo Run run_indexer.bat and run_server.bat to start Augmentorium.