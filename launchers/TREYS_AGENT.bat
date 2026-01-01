@echo off
title Trey's Agent (Unified)
setlocal EnableExtensions EnableDelayedExpansion

rem Ensure we run from repo root
cd /d "%~dp0.."

rem Codex calls can take a while (especially with --search); bump default timeout if unset.
if not defined CODEX_TIMEOUT_SECONDS set "CODEX_TIMEOUT_SECONDS=600"

rem Default to quiet startup unless explicitly enabled
if not defined TREYS_AGENT_DEBUG set "TREYS_AGENT_DEBUG=0"
if not defined TREYS_AGENT_SETUP_VERBOSE set "TREYS_AGENT_SETUP_VERBOSE=0"
set "AGENT_QUIET=1"
set "AGENT_VERBOSE=0"
set "TQDM_DISABLE=1"

call "%~dp0_bootstrap_python_env.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

rem Check Codex CLI auth status using the same invocation as runtime calls
if /I "%TREYS_AGENT_DEBUG%"=="1" echo [CHECK] Codex CLI auth status (runtime check):
"%PY%" -c "import os; os.environ['AGENT_QUIET']='1'; from agent.llm.codex_cli_client import CodexCliClient; import sys; sys.exit(0 if CodexCliClient.from_env().check_auth() else 1)"
if errorlevel 1 (
  echo [WARN] Codex CLI not authenticated or unavailable. Run: codex login
)

if /I "%TREYS_AGENT_DEBUG%"=="1" (
  echo.
  echo [START] Launching Unified Agent...
)

rem Use the interactive mode with persistent memory (AgentRunner + ReAct planning)
rem This is the recommended mode: reasons through tasks, remembers past work, learns from failures
rem For legacy mode, set TREYS_AGENT_LEGACY=1 and use: "%PY%" "%~dp0..\agent\treys_agent.py"
"%PY%" -m agent --interactive

echo.
pause
endlocal
