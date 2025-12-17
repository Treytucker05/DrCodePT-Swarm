@echo off
setlocal enabledelayedexpansion

rem === Terminal 1: Planner (Codex CLI - YAML Generator) ===

set "BASE=%~dp0"
cd /d "%BASE%..\agent"

rem Check if planner_system_prompt.txt exists
if not exist "planner_system_prompt.txt" (
    echo [ERROR] planner_system_prompt.txt not found in agent directory!
    echo Please create this file with the TaskDefinition schema documentation.
    pause
    exit /b 1
)

:MAIN_LOOP
cls
echo =================================================================
echo == Terminal 1: Planner (Codex CLI)
echo =================================================================
echo.
echo Instructions:
echo   1. Type your goal below
echo   2. Codex will generate a YAML plan
echo   3. The plan will be automatically saved to temp_plan.yaml
echo   4. Go to Terminal 2 and press Enter to execute
echo.
echo =================================================================
echo.

set /p "GOAL=Enter your goal (or type 'exit' to quit): "

rem Sanitize for control checks (strip double-quotes)
set "GOAL_CLEAN=%GOAL:"=%"

if /i "%GOAL_CLEAN%"=="exit" (
    echo Exiting...
    goto END
)

if "%GOAL_CLEAN%"=="" (
    echo [ERROR] No goal provided.
    pause
    goto MAIN_LOOP
)

echo.
echo [INFO] Generating YAML plan with Codex...
echo.

rem Delete old temp_plan.yaml if it exists
if exist "temp_plan.yaml" del /f /q "temp_plan.yaml"

rem Create a temporary file with the full prompt
set "TEMP_PROMPT=%TEMP%\codex_prompt_%RANDOM%.txt"

rem Write the system prompt and user goal to temp file
type planner_system_prompt.txt > "%TEMP_PROMPT%"
echo. >> "%TEMP_PROMPT%"
echo === USER GOAL === >> "%TEMP_PROMPT%"
echo %GOAL% >> "%TEMP_PROMPT%"
echo. >> "%TEMP_PROMPT%"
echo Generate the YAML plan and save it to: %CD%\temp_plan.yaml >> "%TEMP_PROMPT%"

rem Call codex exec with the prompt file; write last message to temp_plan.yaml
echo Calling Codex CLI (exec mode)...
codex exec --dangerously-bypass-approvals-and-sandbox --sandbox danger-full-access --output-last-message temp_plan.yaml < "%TEMP_PROMPT%"

rem Store the error level
set CODEX_EXIT=%ERRORLEVEL%

rem Clean up temp file
if exist "%TEMP_PROMPT%" del /f /q "%TEMP_PROMPT%"

echo.
echo [INFO] Codex finished with exit code: %CODEX_EXIT%
echo.

rem Wait a moment for file system to sync
timeout /t 2 /nobreak >nul

rem Check if temp_plan.yaml was created
if exist "temp_plan.yaml" (
    echo [SUCCESS] Plan saved to: agent\temp_plan.yaml
    echo.
    echo --- YAML Preview (first 30 lines) ---
    powershell -Command "Get-Content temp_plan.yaml | Select-Object -First 30"
    echo.
    echo [INFO] Go to Terminal 2 and press Enter to execute.
) else (
    echo [WARNING] temp_plan.yaml was not created.
    echo.
    echo Possible reasons:
    echo   - Codex may have failed to execute the task
    echo   - The file may have been saved to a different location
    echo   - Check if Codex displayed any errors above
    echo.
    echo [INFO] You can manually create the YAML file and save it as temp_plan.yaml
)

echo.
echo Press any key to enter a new goal...
pause >nul
goto MAIN_LOOP

:END
endlocal
