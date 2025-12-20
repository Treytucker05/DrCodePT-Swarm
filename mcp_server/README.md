# PT Brain + Google Calendar MCP Server (Python)

Minimal MCP server using the `mcp` FastMCP API. It now exposes:
- PT Study Brain helpers (list/read session logs, echo/ping, whitelisted files).
- Google Calendar helpers (list upcoming events, create/delete events, free/busy).
- Gmail helpers (list/read/send/label/trash/delete).
- Google Tasks helpers (list/create/update/delete tasks and task lists).

## Prereqs
- Python 3.10+ (tested with 3.11 on Windows)
- Install dependencies:
```powershell
cd mcp_server
python -m pip install -r requirements.txt
```

## Google OAuth setup (one-time)
1. In Google Cloud: enable **Google Calendar API**, **Gmail API**, and **Google Tasks API**.
2. Create an OAuth client (Desktop or Web application is fine for the loopback flow).
3. Download the client JSON and place it as:
   - `GOOGLE_CLIENT_SECRET_JSON=C:\full\path\client_secret.json` (recommended), or
   - `mcp_server/google_client_secret.json` (default lookup).
4. First time you call any `gcal_*`, `gmail_*`, or `tasks_*` tool, a browser window will open for consent.
   Tokens will be cached under `%APPDATA%\pt-brain-mcp\` by default (override with env vars below).

Notes:
- Gmail full access uses the `https://mail.google.com/` scope. This may require verification
  for production apps. For personal/internal use, Google will show a warning screen.

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
- `gcal_status()` - shows whether the token is present/valid and its expiry.
- `gcal_upcoming(limit=10, calendar_id="primary")` - list upcoming events.
- `gcal_create_event(summary, start_iso, end_iso, calendar_id="primary", timezone=None, description=None, location=None)` - create an event; supports all-day (`YYYY-MM-DD`) or timed ISO strings.
- `gcal_delete_event(event_id, calendar_id="primary")` - delete by event id.
- `gcal_freebusy(start_iso, end_iso, calendar_ids=None)` - free/busy ranges for one or more calendars.

## Tools (Gmail)
- `gmail_status()` - shows whether the token is present/valid and its expiry.
- `gmail_list_labels(user_id="me")` - list Gmail labels.
- `gmail_list_messages(query=None, max_results=20, include_spam_trash=False, user_id="me")` - list message IDs.
- `gmail_get_message(message_id, user_id="me", include_body=False, prefer_html=False, max_body_bytes=20000)` - read headers/snippet and optional body.
- `gmail_send_message(to, subject, body, user_id="me", cc=None, bcc=None, body_html=None, reply_to=None, from_alias=None)` - send email.
- `gmail_modify_labels(message_id, add_labels=None, remove_labels=None, user_id="me")` - add/remove label IDs.
- `gmail_trash_message(message_id, user_id="me")` - move to trash.
- `gmail_delete_message(message_id, user_id="me")` - permanent delete.

## Tools (Google Tasks)
- `tasks_status()` - shows whether the token is present/valid and its expiry.
- `tasks_list_tasklists(limit=20)` - list task lists.
- `tasks_create_tasklist(title)` - create a task list.
- `tasks_delete_tasklist(tasklist_id)` - delete a task list.
- `tasks_list(tasklist_id="@default", max_results=100, show_completed=True, show_hidden=False, due_min=None, due_max=None)` - list tasks.
- `tasks_create(title, tasklist_id="@default", notes=None, due=None, status=None, parent=None, position=None)` - create a task.
- `tasks_update(task_id, tasklist_id="@default", title=None, notes=None, due=None, status=None, completed=None)` - update a task.
- `tasks_delete(task_id, tasklist_id="@default")` - delete a task.
- `tasks_clear_completed(tasklist_id="@default")` - clear completed tasks.

## Tools (existing PT helpers)
- `ping()` – returns "pong"
- `list_session_logs(limit=10)` – newest Markdown files in `PT_BRAIN_LOG_DIR` (default: `C:\Users\treyt\OneDrive\Desktop\pt-study-sop\brain\session_logs`)
- `read_session_log(filename)` – contents of a log file (path-safe)
- `echo(payload)` – returns `{ "echo": payload }` for structured payload testing
- `relay_text(message)` – returns the exact string you send
- `read_whitelisted_file(name)` – read specific whitelisted files (currently `LAUNCH_CODEX.bat`)

## Config
- `PT_BRAIN_LOG_DIR` - override the session log directory.
- `MCP_TRANSPORT` - `streamable-http` (default) or `stdio`.
- `GOOGLE_CLIENT_SECRET_JSON` - path to OAuth client JSON (shared default).
- `GOOGLE_CALENDAR_CLIENT_SECRET_JSON` - optional override for Calendar client JSON.
- `GOOGLE_GMAIL_CLIENT_SECRET_JSON` - optional override for Gmail client JSON.
- `GOOGLE_TASKS_CLIENT_SECRET_JSON` - optional override for Tasks client JSON.
- `GOOGLE_CALENDAR_TOKEN_JSON` - path to cached Calendar token.
- `GOOGLE_GMAIL_TOKEN_JSON` - path to cached Gmail token.
- `GOOGLE_TASKS_TOKEN_JSON` - path to cached Tasks token.

## Quick verify (without ChatGPT)
- `ping`:
```powershell
curl http://localhost:8765/mcp -H "Content-Type: application/json" -d '{"action":"ping"}'
```
- `gcal_status`:
```powershell
curl http://localhost:8765/mcp -H "Content-Type: application/json" -d '{"action":"gcal_status"}'
```
- `gmail_status`:
```powershell
curl http://localhost:8765/mcp -H "Content-Type: application/json" -d '{"action":"gmail_status"}'
```
- `tasks_status`:
```powershell
curl http://localhost:8765/mcp -H "Content-Type: application/json" -d '{"action":"tasks_status"}'
```
or use the Apps SDK inspector (`npx @modelcontextprotocol/inspector`).

