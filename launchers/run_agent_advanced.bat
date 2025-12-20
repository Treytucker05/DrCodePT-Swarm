@echo off
setlocal enabledelayedexpansion

rem === DrCodePT-Swarm Advanced Agent Launcher ===
rem This script uses the locally authenticated Codex CLI to generate plans and executes them with your custom supervisor.

set "BASE=%~dp0"
call "%BASE%_bootstrap_python_env.bat"
if errorlevel 1 (
    pause
    exit /b 1
)
cd /d "%BASE%..\agent"

echo =================================================================
echo == DrCodePT-Swarm Advanced Agent (Codex CLI)
echo =================================================================
echo.
echo This agent uses your Codex CLI login to generate verified, executable plans.
echo.
echo Features:
echo   - Codex CLI-powered planning (no API keys)
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

echo.
echo [INFO] Generating plan with Codex CLI...
echo.

rem Call the planner, save YAML to a temp file, then execute it
set "PLAN_FILE=%TEMP%\drcodept_plan_%RANDOM%.yaml"
"%PY%" agent_planner.py "%GOAL%" > "%PLAN_FILE%"
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
"%PY%" codex_bridge.py "%PLAN_FILE%"
del "%PLAN_FILE%" >nul 2>&1

echo.
echo =================================================================
echo [INFO] Task execution complete.
echo =================================================================
pause

endlocal
