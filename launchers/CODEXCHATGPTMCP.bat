@echo off
REM Launch the MCP server for ChatGPT (streamable HTTP on port 8765) and start ngrok tunnel.
REM Requirements: Python deps installed; ngrok available on PATH (https://ngrok.com/download).

setlocal
cd /d "%~dp0mcp_server"

REM Allow overriding transport if needed (default: streamable-http).
if not defined MCP_TRANSPORT set MCP_TRANSPORT=streamable-http

REM Start ngrok tunnel in a new window (only if ngrok is available).
where ngrok >nul 2>&1
if %errorlevel%==0 (
    echo Launching ngrok tunnel on port 8765...
    start "ngrok_mcp" ngrok http 8765
) else (
    echo WARNING: ngrok not found on PATH. Install from https://ngrok.com/download and re-run to expose publicly.
)

echo Starting MCP server on http://0.0.0.0:8765/mcp  (transport=%MCP_TRANSPORT%)
python main.py

endlocal
