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
if not defined CODEX_REASONING_EFFORT_REASON set "CODEX_REASONING_EFFORT_REASON=low"

rem Default to quiet startup unless explicitly enabled
if not defined TREYS_AGENT_DEBUG set "TREYS_AGENT_DEBUG=1"
if not defined TREYS_AGENT_SETUP_VERBOSE set "TREYS_AGENT_SETUP_VERBOSE=0"
set "AGENT_QUIET=1"
set "AGENT_VERBOSE=0"
set "TQDM_DISABLE=1"
set "AGENT_AUTO_APPROVE=0"
set "AGENT_AUTO_ANSWER="

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
  echo [CLEANUP] Ensuring fresh environment...
  taskkill /F /FI "WINDOWTITLE eq DrCodePT LLM Server*" /T >nul 2>&1
  taskkill /F /IM codex.exe /T >nul 2>&1
  
  rem Kill anything on port 8000 (LLM Server port)
  for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
  )
)

if /I "%TREYS_AGENT_DEBUG%"=="1" (
  echo [START] Launching LLM Server...
)
start "DrCodePT LLM Server" /min "%PY%" "%~dp0..\agent\llm\server\app.py"

rem Wait for server to warm up by checking health endpoint
echo [WAIT] Waiting for LLM Server to be ready...
powershell -Command "$start = Get-Date; while (((Get-Date) - $start).TotalSeconds -lt 25) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } } catch { } Start-Sleep -Seconds 1 }; exit 1"
if errorlevel 1 (
  echo [ERROR] LLM Server failed to start or respond in 25s.
  echo [DEBUG] Check logs\server.log for details.
  pause
  exit /b 1
)

if /I "%TREYS_AGENT_DEBUG%"=="1" (
  echo [OK] LLM Server is ready.
  echo.
  echo [START] Launching Unified Agent...
)

rem Use the interactive mode with persistent memory (AgentRunner + ReAct planning)
"%PY%" -m agent --interactive --llm-backend server

echo.
pause
endlocal
