@echo off
setlocal enabledelayedexpansion

title Codex - DrCodePT-Swarm

echo.
echo ========================================
echo   ChatGPT Codex CLI Launcher
echo   DrCodePT-Swarm Directory
echo ========================================
echo.

cd /d "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm"

if errorlevel 1 (
    echo ERROR: Could not navigate to project directory
    pause
    exit /b 1
)

echo Current directory: %cd%
echo.
echo Launching Codex CLI with sandbox bypass...
echo.

REM Launch Codex CLI in interactive (TUI) mode with sandbox bypass and search enabled
codex --dangerously-bypass-approvals-and-sandbox --search

endlocal
exit /b 0
