@echo off
rem Self-elevate if not already running as administrator.
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo Running DISM (this can take 5-20 minutes)...
dism /online /cleanup-image /restorehealth
set dism_rc=%errorlevel%
echo DISM completed with exit code %dism_rc%.
echo.

echo Running SFC (System File Checker)...
sfc /scannow
set sfc_rc=%errorlevel%
echo SFC completed with exit code %sfc_rc%.
echo.

echo Notes:
echo - If SFC reports it repaired files, reboot when convenient.
echo - Exit code 0 means success; 1 means minor issues; >1 indicates a problem.
echo.
pause
