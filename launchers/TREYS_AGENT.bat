@echo off
title Trey's Agent (Unified)
setlocal EnableExtensions EnableDelayedExpansion

rem Ensure we run from repo root
cd /d "%~dp0.."

rem Set Codex home directory to use ChatGPT Pro OAuth session
set "CODEX_HOME=%USERPROFILE%\.codex"

rem Ensure we run from repo root
cd /d "%~dp0.."

rem Codex calls can take a while (especially with --search); bump default timeout if unset.
if not defined CODEX_TIMEOUT_SECONDS set "CODEX_TIMEOUT_SECONDS=600"

rem Codex 5.2 model configuration
if not defined CODEX_MODEL set "CODEX_MODEL=gpt-5.2-codex"
if not defined CODEX_MODEL_FAST set "CODEX_MODEL_FAST=gpt-5.2-codex"
if not defined CODEX_MODEL_REASON set "CODEX_MODEL_REASON=gpt-5.2-codex"
if not defined CODEX_REASONING_EFFORT_FAST set "CODEX_REASONING_EFFORT_FAST=low"
if not defined CODEX_REASONING_EFFORT_REASON set "CODEX_REASONING_EFFORT_REASON=xhigh"

rem Default to quiet startup unless explicitly enabled
if not defined TREYS_AGENT_DEBUG set "TREYS_AGENT_DEBUG=1"
if not defined TREYS_AGENT_SETUP_VERBOSE set "TREYS_AGENT_SETUP_VERBOSE=0"
set "AGENT_QUIET=1"
set "AGENT_VERBOSE=0"
set "TQDM_DISABLE=1"

call "%~dp0_bootstrap_python_env.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

rem Codex CLI is the primary LLM backend
rem Uses free Codex access from ChatGPT Pro subscription
rem If you need to re-authenticate: codex logout && codex login

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
