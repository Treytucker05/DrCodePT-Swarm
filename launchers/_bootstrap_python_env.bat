@echo off

rem Shared bootstrap for DrCodePT-Swarm launchers.
rem - Creates .venv (repo root) if missing
rem - Installs requirements.txt
rem - Installs Playwright Chromium browser binaries (one-time download)
rem - Exports PY pointing at the venv python.exe

set "ROOT=%~dp0.."
cd /d "%ROOT%"

set "VENV=%CD%\.venv"
set "PY=%VENV%\Scripts\python.exe"

echo.
echo [SETUP] Checking Python environment...

rem Create venv if missing
if not exist "%PY%" (
  echo [SETUP] Creating venv at %VENV%
  py -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. Ensure Python is installed and on PATH.
    exit /b 1
  )
)

echo [SETUP] Installing/updating Python deps...
"%PY%" -m pip install --upgrade pip >nul 2>nul
"%PY%" -m pip install -q -r "%CD%\requirements.txt" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] pip install failed. Check your internet connection and try again.
  exit /b 1
)

rem Install Playwright browsers (Chromium) if not present - silent mode
"%PY%" -m playwright install chromium >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Failed to install Playwright Chromium.
  exit /b 1
)

exit /b 0
