@echo off
title Trey's Agent (Unified)
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

rem Check Codex CLI auth status using the same invocation as runtime calls
echo [CHECK] Codex CLI auth status (runtime check):
"%PY%" -c "from agent.llm.codex_cli_client import CodexCliClient; import sys; sys.exit(0 if CodexCliClient.from_env().check_auth() else 1)"
if errorlevel 1 (
  echo [WARN] Codex CLI not authenticated or unavailable. Run: codex login
)

echo.
echo [START] Launching Unified Agent...

rem Use the new unified entrypoint
rem Add --legacy flag to use old treys_agent if needed
"%PY%" -m agent --interactive

echo.
pause
endlocal
