@echo off
setlocal enabledelayedexpansion

rem === DrCodePT-Swarm Autonomous Agent Launcher ===
rem This script uses codex exec to generate plans and pipes them to your custom supervisor.

set "BASE=%~dp0"
cd /d "%BASE%..\agent"

echo =================================================================
echo == DrCodePT-Swarm Autonomous Agent (10/10 Edition)
echo =================================================================
echo.
echo This agent will:
echo   1. Take your natural language goal
echo   2. Generate a YAML plan using codex exec
echo   3. Execute the plan using your custom supervisor
echo   4. Verify the results and trigger self-healing if needed
echo.
echo =================================================================
echo.

rem Prompt the user for a goal
set /p "GOAL=Enter your goal: "

if "%GOAL%"=="" (
    echo.
    echo [ERROR] No goal provided. Exiting.
    pause
    exit /b 1
)

echo.
echo [INFO] Generating plan with codex exec...
echo.

rem Run codex exec and pipe to the bridge
codex exec --sandbox danger-full-access "%GOAL%" | python codex_bridge.py

echo.
echo =================================================================
echo [INFO] Task execution complete.
echo =================================================================
pause

endlocal
