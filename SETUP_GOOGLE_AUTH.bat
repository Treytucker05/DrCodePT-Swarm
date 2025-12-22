@echo off
title Google OAuth Setup
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

call "launchers\_bootstrap_python_env.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo [SETUP] Running Google OAuth setup...
echo        This will open your REGULAR browser (Chrome/Edge)
echo        NOT Playwright - so Google won't block it!
echo.

"%PY%" setup_google_auth.py

endlocal
