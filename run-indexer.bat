@echo off
REM Run script for Augmentorium Indexer on Windows

REM Activate the virtual environment
call .\.venv\Scripts\activate.bat

REM Set Ollama URL if not passed as argument
SET OLLAMA_URL=http://your-server-ip:11434
SET FOUND_OLLAMA_ARG=0

FOR %%A IN (%*) DO (
    IF "%%A"=="--ollama-url" SET FOUND_OLLAMA_ARG=1
)

IF %FOUND_OLLAMA_ARG%==0 (
    REM Run the indexer script with default Ollama URL
    python scripts\run_indexer.py --ollama-url %OLLAMA_URL% %*
) ELSE (
    REM Run with the provided arguments
    python scripts\run_indexer.py %*
)

REM If you get to this point, the script has been interrupted or has ended
echo Indexer has stopped.