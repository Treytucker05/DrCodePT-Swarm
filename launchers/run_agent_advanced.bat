@echo off
setlocal enabledelayedexpansion

rem === DrCodePT-Swarm Advanced Agent Launcher ===
rem This script uses Claude API to generate plans and executes them with your custom supervisor.

set "BASE=%~dp0"
cd /d "%BASE%..\agent"

rem Load CLAUDE_API_KEY from .env (ignore comments/blank lines)
set "CLAUDE_API_KEY="
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (`findstr /b /i "CLAUDE_API_KEY=" ".env"`) do (
        set "CLAUDE_API_KEY=%%b"
    )
)

echo =================================================================
echo == DrCodePT-Swarm Advanced Agent (Claude-Powered)
echo =================================================================
echo.
echo This agent uses Claude API to generate verified, executable plans.
echo.
echo Features:
echo   - Claude-powered planning
echo   - Custom supervisor execution
echo   - Automatic verification
echo   - Self-healing on failure
echo   - Active learning from mistakes
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

if "%CLAUDE_API_KEY%"=="" (
    echo.
    echo [ERROR] CLAUDE_API_KEY is not set. Update agent\.env and try again.
    pause
    exit /b 1
)

echo.
echo [INFO] Generating plan with Claude API...
echo.

rem Call the planner, save YAML to a temp file, then execute it
set "PLAN_FILE=%TEMP%\drcodept_plan_%RANDOM%.yaml"
python agent_planner.py "%GOAL%" > "%PLAN_FILE%"
if errorlevel 1 (
    echo.
    echo [ERROR] Planner failed. See messages above.
    del "%PLAN_FILE%" >nul 2>&1
    pause
    exit /b 1
)
for %%F in ("%PLAN_FILE%") do if %%~zF==0 (
    echo.
    echo [ERROR] Planner produced empty output.
    del "%PLAN_FILE%" >nul 2>&1
    pause
    exit /b 1
)
python codex_bridge.py "%PLAN_FILE%"
del "%PLAN_FILE%" >nul 2>&1

echo.
echo =================================================================
echo [INFO] Task execution complete.
echo =================================================================
pause

endlocal
