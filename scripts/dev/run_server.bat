@echo off
call ".venv\Scripts\activate.bat"
python -m augmentorium.server --log-level DEBUG "$@"
