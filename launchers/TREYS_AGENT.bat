@echo off
title Trey's Agent
setlocal EnableExtensions EnableDelayedExpansion

rem Ensure we run from repo root
cd /d "%~dp0.."

rem Codex calls can take a while (especially with --search); bump default timeout if unset.
if not defined CODEX_TIMEOUT_SECONDS set "CODEX_TIMEOUT_SECONDS=600"

call "%~dp0_bootstrap_python_env.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

echo.
echo [START] Launching Trey's Agent...
cd /d "%CD%\agent"
"%PY%" treys_agent.py

echo.
pause
endlocal
