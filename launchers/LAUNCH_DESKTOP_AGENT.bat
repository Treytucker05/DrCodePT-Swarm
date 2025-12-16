@echo off
setlocal enabledelayedexpansion

rem Launch Codex with PyAutoGUI desktop control MCP + Playwright MCP + web search.

set "BASE=%~dp0"
cd /d "%BASE%"

set "CONFIG=%BASE%codex.desktop.toml"

if not exist "%CONFIG%" (
    echo [INFO] Creating per-project Codex config at %CONFIG%
    > "%CONFIG%" (
        echo sandbox_mode = "danger-full-access"
        echo.
        echo [features]
        echo rmcp_client = true
        echo web_search_request = true
        echo.
        echo [mcp_servers.desktop]
        echo command = "python"
        echo args = ["%BASE%desktop_mcp_wrapper.py"]
        echo startup_timeout_sec = 90
        echo tool_timeout_sec = 60
        echo.
        echo [mcp_servers.playwright]
        echo command = "npx"
        echo args = ["-y", "mcp-playwright"]
        echo startup_timeout_sec = 90
        echo tool_timeout_sec = 60
    )
) else (
    echo [INFO] Using existing config: %CONFIG%
)

rem --- Ensure Python MCP server deps ---
set "PY_DEPS=realtimex-pyautogui-server"
for %%P in (%PY_DEPS%) do (
    python -m pip show %%P >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Installing %%P ...
        python -m pip install --upgrade %%P
        if errorlevel 1 (
            echo [ERROR] Failed to install %%P. Is Python/pip on PATH?
            pause
            exit /b 1
        )
    ) else (
        echo [INFO] %%P already installed.
    )
)

rem --- Ensure Node/Playwright MCP deps ---
where npm >nul 2>&1
if errorlevel 1 (
    echo [WARN] npm not found; Playwright MCP will not start. Install Node.js and rerun.
) else (
    call npm ls -g mcp-playwright >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Installing global mcp-playwright ...
        call npm install -g mcp-playwright
    ) else (
        echo [INFO] mcp-playwright already installed globally.
    )
    rem Install browsers (safe if already present)
    call npx -y playwright install chromium >nul 2>&1
)

set "CODEX_CONFIG=%CONFIG%"
echo [INFO] Launching Codex with desktop MCP + web search...
rem Launch Codex in a dedicated console so stdin is a TTY and the window stays open.
start "" cmd /k "set CODEX_CONFIG=%CODEX_CONFIG% && codex --dangerously-bypass-approvals-and-sandbox --search"

endlocal
exit /b %ERRORLEVEL%
