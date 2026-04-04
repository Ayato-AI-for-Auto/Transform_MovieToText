@echo off
cd /d "%~dp0"
if exist "scripts\run.bat" (
    call "scripts\run.bat"
) else (
    echo [ERROR] scripts\run.bat not found.
    pause
)
