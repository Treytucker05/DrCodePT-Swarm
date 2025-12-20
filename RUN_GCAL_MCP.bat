@echo off
setlocal

rem Launch the MCP server with Google Calendar support.
rem Creates a local venv (mcp_server\.venv), installs deps, then runs the server.

set "BASE=%~dp0"
cd /d "%BASE%mcp_server"

rem Use existing virtual env if present, otherwise create one.
if not exist ".venv" (
    echo [INFO] Creating venv at %BASE%mcp_server\.venv
    py -3 -m venv .venv
)
call ".venv\Scripts\activate.bat"

echo [INFO] Installing/refreshing Python dependencies...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

rem Paths for OAuth client and token; override by exporting env vars before running.
if not defined GOOGLE_CLIENT_SECRET_JSON (
    set "GOOGLE_CLIENT_SECRET_JSON=%BASE%mcp_server\google_client_secret.json"
)
if not defined GOOGLE_CALENDAR_TOKEN_JSON (
    set "GOOGLE_CALENDAR_TOKEN_JSON=%BASE%mcp_server\google_calendar_token.json"
)

if not exist "%GOOGLE_CLIENT_SECRET_JSON%" (
    echo [WARN] google_client_secret.json is missing at:
    echo        %GOOGLE_CLIENT_SECRET_JSON%
    echo Copy your OAuth client JSON here or set GOOGLE_CLIENT_SECRET_JSON before running.
)

set "MCP_TRANSPORT=streamable-http"

echo [INFO] Starting MCP server on http://0.0.0.0:8765/mcp  (Ctrl+C to stop)
python main.py

endlocal
