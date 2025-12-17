@echo off
setlocal enabledelayedexpansion

rem === Terminal 1: Planner (Codex CLI - YAML Generator) ===

set "BASE=%~dp0"
cd /d "%BASE%..\agent"

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

if /i "%GOAL%"=="exit" (
    echo Exiting...
    goto END
)

if "%GOAL%"=="" (
    echo [ERROR] No goal provided.
    pause
    goto MAIN_LOOP
)

echo.
echo [INFO] Generating YAML plan with Codex...
echo.

rem Delete old temp_plan.yaml if it exists
if exist "temp_plan.yaml" del /f /q "temp_plan.yaml"

rem Create the meta-prompt that asks Codex to generate and save YAML
set "META_PROMPT=You are a task planner. Generate a YAML task plan for this goal: '%GOAL%'. Use the fs tool to write the YAML to a file named 'temp_plan.yaml'. The YAML must follow this schema: id (string), name (string), type (composite/atomic), goal (string), definition_of_done (list), stop_rules (list), on_fail (escalate/abort/handoff), steps (list with tool/action/inputs/verifier). Output ONLY valid YAML with no markdown formatting."

rem Call codex and capture the result
echo Calling Codex CLI...
codex --dangerously-bypass-approvals-and-sandbox "%META_PROMPT%"

rem Store the error level
set CODEX_EXIT=%ERRORLEVEL%

echo.
echo [INFO] Codex finished with exit code: %CODEX_EXIT%
echo.

rem Wait a moment for file system to sync
timeout /t 2 /nobreak >nul

rem Check if temp_plan.yaml was created
if exist "temp_plan.yaml" (
    echo [SUCCESS] Plan saved to: agent\temp_plan.yaml
    echo.
    echo --- YAML Preview (first 20 lines) ---
    type temp_plan.yaml | more /E +0
    echo.
    echo [INFO] Go to Terminal 2 and press Enter to execute.
) else (
    echo [WARNING] temp_plan.yaml was not created.
    echo.
    echo Possible reasons:
    echo   - Codex may have failed to execute the task
    echo   - The file may have been saved to a different location
    echo   - Codex may need to be run interactively
    echo.
    echo [INFO] You can manually create the YAML file and save it as temp_plan.yaml
)

echo.
echo Press any key to enter a new goal...
pause >nul
goto MAIN_LOOP

:END
endlocal
