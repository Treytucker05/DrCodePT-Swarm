@echo off
setlocal enabledelayedexpansion

rem === Terminal 2: Executor (Custom Supervisor) ===

set "BASE=%~dp0"
call "%BASE%_bootstrap_python_env.bat"
if errorlevel 1 (
    pause
    exit /b 1
)
cd /d "%BASE%..\agent"

:MAIN_LOOP
cls
echo =================================================================
echo == Terminal 2: Executor (Custom Supervisor)
echo =================================================================
echo.
echo Instructions:
echo   1. After copying the YAML from Terminal 1
echo   2. Save it to: agent\temp_plan.yaml
echo   3. Press Enter here to execute the plan
echo.
echo =================================================================
echo.

set /p "DUMMY=Press Enter when temp_plan.yaml is ready (or type 'exit' to quit): "

if /i "%DUMMY%"=="exit" (
    echo Exiting...
    goto END
)

rem Check if the plan file exists
if not exist "temp_plan.yaml" (
    echo.
    echo [ERROR] temp_plan.yaml not found in agent directory.
    echo Please save the YAML plan from Terminal 1 first.
    echo.
    pause
    goto MAIN_LOOP
)

echo.
echo [INFO] Executing plan with custom supervisor...
echo.

rem Execute the plan using codex_bridge.py
"%PY%" codex_bridge.py temp_plan.yaml

echo.
echo =================================================================
echo [INFO] Execution complete.
echo =================================================================
echo.

rem Archive the executed plan
if exist "temp_plan.yaml" (
    set "TIMESTAMP=%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
    set "TIMESTAMP=!TIMESTAMP: =0!"
    move /y "temp_plan.yaml" "tasks\executed_plan_!TIMESTAMP!.yaml" >nul 2>&1
    echo [INFO] Plan archived to tasks\executed_plan_!TIMESTAMP!.yaml
    echo.
)

pause
goto MAIN_LOOP

:END
endlocal
