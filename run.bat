@echo off
setlocal
cd /d %~dp0

echo ==========================================
echo   Movie to Text (Whisper) Startup
echo ==========================================
echo.
echo Launching application using uv...
echo.

uv run main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)
endlocal
