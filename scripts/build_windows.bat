@echo off
setlocal enabledelayedexpansion

echo [BUILD] Starting Movie to Text v2.5 Windows Build...

:: Check for uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uv is not installed. Please install it with: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    exit /b 1
)

:: Sync dependencies
echo [BUILD] Syncing dependencies...
uv pip install -e .

:: Generate Icon (Ensure assets/icon.ico exists or use the generated png)
:: For now, we'll assume the user might want to convert the PNG to ICO manually or we use a basic converter if available.
:: But for this script, we'll just check if icon.png exists.
if not exist "assets\icon.png" (
    echo [WARNING] assets\icon.png not found. Build will proceed with default icon.
)

:: Build with PyInstaller via flet pack
echo [BUILD] Packaging application...
python -m flet pack main.py ^
    --name "MovieToText" ^
    --icon "assets/icon.png" ^
    --add-data "src;src" ^
    --add-data "assets;assets" ^
    --product-name "Transform Movie to Text" ^
    --product-version "2.5.0" ^
    --copyright "Ayato-AI-for-Auto" ^
    --description "Premium Windows Transcription Tool"

if %errorlevel% equ 0 (
    echo [SUCCESS] Build complete! Check the 'dist' folder.
) else (
    echo [ERROR] Build failed.
)

pause
