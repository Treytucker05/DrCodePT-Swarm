@echo off
setlocal
rem Determine this script's folder
set "SCRIPT_DIR=%~dp0"

rem Convert the WSL launcher path
for /f "usebackq delims=" %%P in (`wsl wslpath -a "%SCRIPT_DIR%run_codex_wsl.sh"`) do set "WSL_SCRIPT=%%P"

rem Launch Codex inside WSL (Ubuntu)
wsl -d Ubuntu -- bash -lc "\"%WSL_SCRIPT%\" %*"

if errorlevel 1 (
  echo.
  echo Codex did not start. See message above.
  pause
)

endlocal
