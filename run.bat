@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Movie to Text (Whisper) Startup
echo ==========================================
echo.

:: 1. Check for uv package manager
where uv >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "%~dp0uv.exe" (
        echo [INFO] uv is not installed. Downloading standalone uv...
        curl -sSfL -o uv.exe https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.exe
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to download uv. Please check your internet connection.
            pause
            exit /b 1
        )
    )
    set "UV_CMD=%~dp0uv.exe"
) else (
    set "UV_CMD=uv"
)

:: 2. Check for virtual environment and set it up if missing
if not exist ".venv" (
    echo [INFO] First run or missing environment detected.
    echo [INFO] Setting up the isolated Python environment...
    echo [INFO] This will download Python and PyTorch (over 2GB). Please be patient.
    echo.
    
    "%UV_CMD%" python install 3.11
    "%UV_CMD%" venv
    "%UV_CMD%" pip install -e .
    
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to setup environment.
        pause
        exit /b 1
    )
    echo [INFO] Environment setup complete!
)

echo [INFO] Launching application...
echo.

:: 3. Run the application
"%UV_CMD%" run main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)
endlocal