@echo off

rem === DrCodePT-Swarm Two-Terminal Agent Launcher ===

echo =================================================================
echo == DrCodePT-Swarm Two-Terminal Agent
echo =================================================================
echo.
echo This will open two terminals:
echo   Terminal 1: Codex CLI (Planner)
echo   Terminal 2: Custom Supervisor (Executor)
echo.
echo Workflow:
echo   1. In Terminal 1, type your goal
echo   2. Copy the YAML output
echo   3. Save it to: agent\temp_plan.yaml
echo   4. In Terminal 2, press Enter to execute
echo.
echo =================================================================
echo.
pause

rem Launch Terminal 1 (Planner)
start "Terminal 1: Planner" cmd /k "launchers\terminal1_planner.bat"

rem Wait a moment
timeout /t 2 /nobreak >nul

rem Launch Terminal 2 (Executor)
start "Terminal 2: Executor" cmd /k "launchers\terminal2_executor.bat"

echo.
echo Both terminals launched successfully.
echo.
