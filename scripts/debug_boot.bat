@echo off
setlocal
cd /d "%~dp0"

echo [DEBUG BOOT] checking files...
if not exist "main.py" echo [ERROR] main.py missing!
if not exist ".venv" echo [ERROR] .venv missing!

echo [DEBUG BOOT] environment variables...
set

echo [DEBUG BOOT] trying to run python...
uv run python -c "print('Python OK')"

echo [DEBUG BOOT] trying to load app components...
uv run python -c "import logging; from src.logger import setup_logger; setup_logger(); print('Logger OK'); from src.app import FletApp; print('App Load OK')"

echo [DEBUG BOOT] full launch...
uv run python main.py

echo [DEBUG BOOT] done.
pause
