@echo off
REM ========================================================================
REM WRAPPER - Ensures window stays open and shows all errors
REM ========================================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set DASHBOARD_API_DIR=%SCRIPT_DIR%PROGRAMS\dashboard-api

cls
echo.
echo ========================================================================
echo   DrCodePT Dashboard API Launcher
echo ========================================================================
echo.

REM Start main script in a new command window that stays open
start "DrCodePT Dashboard API" /wait cmd /k "cd /d "%DASHBOARD_API_DIR%" && npm run start:api"

echo.
echo Server has stopped.
echo.
pause
