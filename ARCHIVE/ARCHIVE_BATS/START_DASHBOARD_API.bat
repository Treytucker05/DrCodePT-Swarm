@echo off
REM ========================================================================
REM DrCodePT Dashboard API Startup Script
REM ========================================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set DASHBOARD_API_DIR=%SCRIPT_DIR%PROGRAMS\dashboard-api

REM Use /K to keep window open after command completes
cmd /k "cd /d "%DASHBOARD_API_DIR%" && npm run start:api"
