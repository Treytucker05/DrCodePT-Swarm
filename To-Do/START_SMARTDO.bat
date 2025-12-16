@echo off
setlocal

set PORT=3010
set URL=http://localhost:%PORT%/

REM Change to the folder this script lives in
cd /d "%~dp0"

echo Checking for any process on port %PORT% ...
powershell -NoLogo -NoProfile -Command ^
  "Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Write-Output ('Stopping PID {0}' -f $_.OwningProcess); Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

echo Starting SmartDo dev server on %URL% ...
start "SmartDo Dev Server" cmd /k "npm run dev"

REM Give the server time to start, then open the app
timeout /t 5 /nobreak >nul
start "" %URL%

echo Browser launched to %URL%
echo The server runs in the window titled SmartDo Dev Server. Close that window to stop it.
pause
endlocal
