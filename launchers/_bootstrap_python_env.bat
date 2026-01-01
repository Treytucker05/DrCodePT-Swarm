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

set "SETUP_VERBOSE=%TREYS_AGENT_SETUP_VERBOSE%"
if not defined SETUP_VERBOSE set "SETUP_VERBOSE=0"

if /I "%SETUP_VERBOSE%"=="1" (
  echo.
  echo [SETUP] Checking Python environment...
)

rem Create venv if missing
if not exist "%PY%" (
  echo [SETUP] Creating venv at %VENV%
  py -m venv "%VENV%"
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. Ensure Python is installed and on PATH.
    exit /b 1
  )
)

if /I "%SETUP_VERBOSE%"=="1" echo [SETUP] Installing/updating Python deps...
"%PY%" -m pip install --upgrade pip >nul 2>nul
"%PY%" -m pip install -q -r "%CD%\requirements.txt" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] pip install failed. Check your internet connection and try again.
  exit /b 1
)

if /I "%SETUP_VERBOSE%"=="1" echo [SETUP] Ensuring UI automation deps (pywinauto, uiautomation, pynput)...
"%PY%" -m pip install -q pywinauto uiautomation pynput >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Failed to install UI automation dependencies.
  exit /b 1
)

rem Check if Tesseract OCR is available (required for screen reading)
if /I "%SETUP_VERBOSE%"=="1" echo [SETUP] Checking Tesseract OCR installation...
"%PY%" -c "import pytesseract; pytesseract.get_tesseract_version()" >nul 2>nul
if errorlevel 1 (
  echo [WARN] Tesseract OCR not found. Screen text reading will be limited.
  echo [WARN] Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
  echo [WARN] Or use chocolatey: choco install tesseract
)

rem Install Playwright browsers (Chromium) if not present - silent mode
"%PY%" -m playwright install chromium >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Failed to install Playwright Chromium.
  exit /b 1
)

exit /b 0
