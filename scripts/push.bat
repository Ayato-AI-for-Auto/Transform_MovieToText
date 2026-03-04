@echo off
setlocal enabledelayedexpansion

echo [1/3] Running Ruff Format/Check...
uv run ruff format .
if !errorlevel! neq 0 (
    echo [ERROR] Ruff format failed.
    exit /b !errorlevel!
)
uv run ruff check . --fix
if !errorlevel! neq 0 (
    echo [ERROR] Ruff check failed.
    exit /b !errorlevel!
)

echo [2/3] Running Unit Tests (pytest)...
uv run pytest
if !errorlevel! neq 0 (
    echo [ERROR] Tests failed. Push aborted.
    exit /b !errorlevel!
)

echo [3/3] Pushing to GitHub...
git push
if !errorlevel! neq 0 (
    echo [ERROR] Git push failed.
    exit /b !errorlevel!
)

echo.
echo [SUCCESS] CI passed and code pushed successfully!
pause
