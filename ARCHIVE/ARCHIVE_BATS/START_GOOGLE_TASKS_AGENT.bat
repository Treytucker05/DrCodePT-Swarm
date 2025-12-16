@echo off
setlocal

rem Launcher for the Google Tasks/Calendar Gemini agent
rem Uses the copy inside DrCodePT-Swarm\PROGRAMS\google-tasks-agent

set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%PROGRAMS\google-tasks-agent"

if not exist "%APP_DIR%\package.json" (
  echo [ERROR] Could not find app directory:
  echo   %APP_DIR%
  echo Make sure PROGRAMS\google-tasks-agent exists under DrCodePT-Swarm.
  pause
  exit /b 1
)

cd /d "%APP_DIR%"

if not exist "node_modules" (
  echo [INFO] Installing npm dependencies for Google Tasks agent...
  call npm install
)

echo [INFO] Ensuring @google/generative-ai is installed...
call npm install @google/generative-ai

echo [INFO] Starting Google Tasks/Calendar agent...
start "Google Tasks Agent Dev Server" /D "%APP_DIR%" cmd /k npm run dev

REM Give Vite a moment to start, then open the browser
timeout /t 5 /nobreak >nul

start "" "http://localhost:7401"

endlocal
