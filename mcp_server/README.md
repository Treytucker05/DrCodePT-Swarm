# PT Brain + Google Calendar MCP Server (Python)

Minimal MCP server using the `mcp` FastMCP API. It now exposes:
- PT Study Brain helpers (list/read session logs, echo/ping, whitelisted files).
- Google Calendar helpers (list upcoming events, create/delete events, free/busy).

## Prereqs
- Python 3.10+ (tested with 3.11 on Windows)
- Install dependencies:
```powershell
cd mcp_server
python -m pip install -r requirements.txt
```

## Google Calendar OAuth setup (one-time)
1. In Google Cloud: enable **Google Calendar API**.
2. Create an OAuth client (Desktop or Web application is fine for the loopback flow).
3. Download the client JSON and place it as `mcp_server/google_client_secret.json`
   or set `GOOGLE_CLIENT_SECRET_JSON=C:\full\path\client_secret.json`.
4. First time you call any `gcal_*` tool, a browser window will open for consent; a token
   will be cached at `mcp_server/google_calendar_token.json` (override with `GOOGLE_CALENDAR_TOKEN_JSON`).

## Run locally
Streamable HTTP (best for ChatGPT/Codex connector):
```powershell
cd mcp_server
python main.py
# serves http://0.0.0.0:8765/mcp
```

Alternative stdio transport:
```powershell
$env:MCP_TRANSPORT="stdio"
python main.py
```

## Expose to ChatGPT/Codex
1. Tunnel (example with ngrok):
```powershell
ngrok http 8765
# copy the https URL, append /mcp  (e.g., https://abc123.ngrok.io/mcp)
```
2. In ChatGPT Dev Settings: Connectors -> Create -> paste the HTTPS `/mcp` URL. Save, then start a new chat and pick the connector.

## Tools (Google Calendar)
- `gcal_status()` – shows whether the token is present/valid and its expiry.
- `gcal_upcoming(limit=10, calendar_id="primary")` – list upcoming events.
- `gcal_create_event(summary, start_iso, end_iso, calendar_id="primary", timezone=None, description=None, location=None)` – create an event; supports all-day (`YYYY-MM-DD`) or timed ISO strings.
- `gcal_delete_event(event_id, calendar_id="primary")` – delete by event id.
- `gcal_freebusy(start_iso, end_iso, calendar_ids=None)` – free/busy ranges for one or more calendars.

## Tools (existing PT helpers)
- `ping()` – returns "pong"
- `list_session_logs(limit=10)` – newest Markdown files in `PT_BRAIN_LOG_DIR` (default: `C:\Users\treyt\OneDrive\Desktop\pt-study-sop\brain\session_logs`)
- `read_session_log(filename)` – contents of a log file (path-safe)
- `echo(payload)` – returns `{ "echo": payload }` for structured payload testing
- `relay_text(message)` – returns the exact string you send
- `read_whitelisted_file(name)` – read specific whitelisted files (currently `LAUNCH_CODEX.bat`)

## Config
- `PT_BRAIN_LOG_DIR` – override the session log directory.
- `MCP_TRANSPORT` – `streamable-http` (default) or `stdio`.
- `GOOGLE_CLIENT_SECRET_JSON` – path to OAuth client JSON.
- `GOOGLE_CALENDAR_TOKEN_JSON` – path to cached user token.

## Quick verify (without ChatGPT)
- `ping`:
```powershell
curl http://localhost:8765/mcp -H "Content-Type: application/json" -d '{"action":"ping"}'
```
- `gcal_status`:
```powershell
curl http://localhost:8765/mcp -H "Content-Type: application/json" -d '{"action":"gcal_status"}'
```
or use the Apps SDK inspector (`npx @modelcontextprotocol/inspector`).

