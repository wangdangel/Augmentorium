@echo off
call ".venv\Scripts\activate.bat"
python -m augmentorium.indexer --log-level DEBUG "$@"
