"""
Minimal MCP server (FastMCP) exposing a few helper tools for PT Study Brain.

Transports:
- streamable-http on http://127.0.0.1:8765/mcp  (safe default; set MCP_HOST=0.0.0.0 to expose)
- stdio (for local CLI testing)
"""

from __future__ import annotations

import base64
import datetime as _dt
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.message import EmailMessage
from mcp.server.fastmcp import FastMCP

# ---- Settings -------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]

# Prefer a repo-relative default unless the user overrides it via env.
LOG_DIR = Path(os.environ.get("PT_BRAIN_LOG_DIR", str(ROOT_DIR / "session_logs")))

# Store OAuth secrets/tokens outside the repo by default.
_default_config_root = Path(
    os.environ.get("APPDATA")
    or os.environ.get("XDG_CONFIG_HOME")
    or str(Path.home() / ".config")
)
SECRETS_DIR = Path(os.environ.get("PT_BRAIN_SECRETS_DIR", str(_default_config_root / "pt-brain-mcp")))

# --- Google OAuth settings -------------------------------------------------
# Base OAuth client JSON (can be shared across Calendar/Gmail/Tasks).
CLIENT_SECRET_DEFAULT = Path(
    os.environ.get("GOOGLE_CLIENT_SECRET_JSON", str(SECRETS_DIR / "google_client_secret.json"))
)

# Calendar
GCAL_CLIENT_SECRET = Path(
    os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET_JSON", str(CLIENT_SECRET_DEFAULT))
)
GCAL_TOKEN_PATH = Path(
    os.environ.get("GOOGLE_CALENDAR_TOKEN_JSON", str(SECRETS_DIR / "google_calendar_token.json"))
)
GCAL_SCOPES = [
    # Full calendar event access (create/update/delete).
    "https://www.googleapis.com/auth/calendar.events",
]

# Gmail
GMAIL_CLIENT_SECRET = Path(
    os.environ.get("GOOGLE_GMAIL_CLIENT_SECRET_JSON", str(CLIENT_SECRET_DEFAULT))
)
GMAIL_TOKEN_PATH = Path(
    os.environ.get("GOOGLE_GMAIL_TOKEN_JSON", str(SECRETS_DIR / "google_gmail_token.json"))
)
GMAIL_SCOPES = [
    # Full Gmail access (read/modify/send). This scope may require verification for production use.
    "https://mail.google.com/",
]

# Google Tasks
TASKS_CLIENT_SECRET = Path(
    os.environ.get("GOOGLE_TASKS_CLIENT_SECRET_JSON", str(CLIENT_SECRET_DEFAULT))
)
TASKS_TOKEN_PATH = Path(
    os.environ.get("GOOGLE_TASKS_TOKEN_JSON", str(SECRETS_DIR / "google_tasks_token.json"))
)
TASKS_SCOPES = [
    # Full Google Tasks access (read/write/delete).
    "https://www.googleapis.com/auth/tasks",
]

# Whitelist specific files you want accessible from ChatGPT.
WHITELISTED_FILES = {
    "LAUNCH_CODEX.bat": ROOT_DIR / "LAUNCH_CODEX.bat",
}

server = FastMCP(
    name="PT Brain MCP",
    instructions="Helper tools for PT Study Brain (list and read session logs).",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8765")),
    streamable_http_path="/mcp",
)


# ---- Tools ---------------------------------------------------------------
def _load_google_service(
    *,
    service_name: str,
    version: str,
    client_secret_path: Path,
    token_path: Path,
    scopes: list[str],
    force_refresh: bool = False,
):
    """
    Returns a googleapiclient service, running the installed-app OAuth flow on first use.
    """
    if not client_secret_path.exists():
        raise FileNotFoundError(
            f"Missing Google OAuth client JSON at {client_secret_path}. "
            "Download it from Google Cloud -> Credentials (Web/Installed app)."
        )

    creds: Credentials | None = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if force_refresh and creds and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
            # Port 0 picks a free port and opens a local browser tab for consent.
            creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build(service_name, version, credentials=creds)


def _load_calendar_service(force_refresh: bool = False):
    return _load_google_service(
        service_name="calendar",
        version="v3",
        client_secret_path=GCAL_CLIENT_SECRET,
        token_path=GCAL_TOKEN_PATH,
        scopes=GCAL_SCOPES,
        force_refresh=force_refresh,
    )


def _load_gmail_service(force_refresh: bool = False):
    return _load_google_service(
        service_name="gmail",
        version="v1",
        client_secret_path=GMAIL_CLIENT_SECRET,
        token_path=GMAIL_TOKEN_PATH,
        scopes=GMAIL_SCOPES,
        force_refresh=force_refresh,
    )


def _load_tasks_service(force_refresh: bool = False):
    return _load_google_service(
        service_name="tasks",
        version="v1",
        client_secret_path=TASKS_CLIENT_SECRET,
        token_path=TASKS_TOKEN_PATH,
        scopes=TASKS_SCOPES,
        force_refresh=force_refresh,
    )


def _normalize_time(value: str, timezone: str | None = None) -> dict[str, str]:
    """
    Accepts either an all-day date (YYYY-MM-DD) or an RFC3339 datetime string.
    """
    if len(value) == 10 and value.count("-") == 2:
        return {"date": value}
    return {"dateTime": value, "timeZone": timezone or "UTC"}


@server.tool(
    description="Check Google Calendar auth state. Returns whether token exists and expiry."
)
async def gcal_status() -> dict[str, Any]:
    info: dict[str, Any] = {
        "token_path": str(GCAL_TOKEN_PATH),
        "client_path": str(GCAL_CLIENT_SECRET),
        "token_exists": GCAL_TOKEN_PATH.exists(),
    }
    if not GCAL_TOKEN_PATH.exists():
        info["status"] = "missing_token"
        return info
    creds = Credentials.from_authorized_user_file(GCAL_TOKEN_PATH, GCAL_SCOPES)
    info["scopes"] = creds.scopes
    info["expired"] = creds.expired
    info["valid"] = creds.valid
    info["expiry"] = creds.expiry.isoformat() if creds.expiry else None
    return info


@server.tool(
    description="Check Gmail auth state. Returns whether token exists and expiry."
)
async def gmail_status() -> dict[str, Any]:
    info: dict[str, Any] = {
        "token_path": str(GMAIL_TOKEN_PATH),
        "client_path": str(GMAIL_CLIENT_SECRET),
        "token_exists": GMAIL_TOKEN_PATH.exists(),
    }
    if not GMAIL_TOKEN_PATH.exists():
        info["status"] = "missing_token"
        return info
    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, GMAIL_SCOPES)
    info["scopes"] = creds.scopes
    info["expired"] = creds.expired
    info["valid"] = creds.valid
    info["expiry"] = creds.expiry.isoformat() if creds.expiry else None
    return info


@server.tool(
    description="Check Google Tasks auth state. Returns whether token exists and expiry."
)
async def tasks_status() -> dict[str, Any]:
    info: dict[str, Any] = {
        "token_path": str(TASKS_TOKEN_PATH),
        "client_path": str(TASKS_CLIENT_SECRET),
        "token_exists": TASKS_TOKEN_PATH.exists(),
    }
    if not TASKS_TOKEN_PATH.exists():
        info["status"] = "missing_token"
        return info
    creds = Credentials.from_authorized_user_file(TASKS_TOKEN_PATH, TASKS_SCOPES)
    info["scopes"] = creds.scopes
    info["expired"] = creds.expired
    info["valid"] = creds.valid
    info["expiry"] = creds.expiry.isoformat() if creds.expiry else None
    return info


@server.tool(
    description="List upcoming Google Calendar events. Defaults to 'primary' calendar."
)
async def gcal_upcoming(
    limit: int = 10, calendar_id: str = "primary"
) -> list[dict[str, Any]]:
    service = _load_calendar_service()
    now = _dt.datetime.utcnow().isoformat() + "Z"
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max(1, limit),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    simplified = []
    for e in events:
        simplified.append(
            {
                "id": e.get("id"),
                "summary": e.get("summary"),
                "start": e.get("start", {}).get("dateTime")
                or e.get("start", {}).get("date"),
                "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
                "htmlLink": e.get("htmlLink"),
                "status": e.get("status"),
                "hangoutLink": e.get("hangoutLink"),
            }
        )
    return simplified


@server.tool(description="Create a Google Calendar event on the given calendar.")
async def gcal_create_event(
    summary: str,
    start_iso: str,
    end_iso: str,
    calendar_id: str = "primary",
    timezone: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    service = _load_calendar_service()
    body: dict[str, Any] = {
        "summary": summary,
        "start": _normalize_time(start_iso, timezone),
        "end": _normalize_time(end_iso, timezone),
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    event = service.events().insert(calendarId=calendar_id, body=body).execute()
    return {
        "id": event.get("id"),
        "htmlLink": event.get("htmlLink"),
        "status": event.get("status"),
    }


@server.tool(description="Delete a Google Calendar event by event ID.")
async def gcal_delete_event(event_id: str, calendar_id: str = "primary") -> str:
    service = _load_calendar_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return "deleted"


@server.tool(
    description="Free/busy query for one or more calendars. Returns busy ranges."
)
async def gcal_freebusy(
    start_iso: str,
    end_iso: str,
    calendar_ids: list[str] | None = None,
) -> dict[str, list[dict[str, str]]]:
    service = _load_calendar_service()
    items = [{"id": cid} for cid in (calendar_ids or ["primary"])]
    body = {"timeMin": start_iso, "timeMax": end_iso, "items": items}
    result = service.freebusy().query(body=body).execute()
    cal_busy = {}
    for cal_id, data in result.get("calendars", {}).items():
        cal_busy[cal_id] = data.get("busy", [])
    return cal_busy


def _headers_to_dict(headers: list[dict[str, Any]]) -> dict[str, str]:
    return {h.get("name", "").lower(): h.get("value", "") for h in headers or [] if h.get("name")}


def _extract_message_text(payload: dict[str, Any], *, prefer_html: bool = False, max_bytes: int = 20000) -> tuple[str | None, str | None]:
    if not payload:
        return None, None

    parts: list[tuple[str, str]] = []

    def walk(part: dict[str, Any]) -> None:
        body = part.get("body") or {}
        data = body.get("data")
        if data and part.get("mimeType"):
            parts.append((part.get("mimeType"), data))
        for child in part.get("parts") or []:
            walk(child)

    walk(payload)
    if payload.get("body", {}).get("data") and payload.get("mimeType"):
        parts.append((payload.get("mimeType"), payload.get("body", {}).get("data")))

    preferred = ["text/html", "text/plain"] if prefer_html else ["text/plain", "text/html"]
    for mime in preferred:
        for part_mime, data in parts:
            if part_mime == mime:
                try:
                    raw = base64.urlsafe_b64decode(data.encode("utf-8", errors="ignore"))
                    return raw[:max_bytes].decode("utf-8", errors="replace"), mime
                except Exception:
                    return None, None
    return None, None


@server.tool(description="List Gmail labels.")
async def gmail_list_labels(user_id: str = "me") -> list[dict[str, Any]]:
    service = _load_gmail_service()
    result = service.users().labels().list(userId=user_id).execute()
    labels = result.get("labels", [])
    return [{"id": l.get("id"), "name": l.get("name"), "type": l.get("type")} for l in labels]


@server.tool(description="List Gmail message IDs matching an optional search query.")
async def gmail_list_messages(
    query: str | None = None,
    max_results: int = 20,
    include_spam_trash: bool = False,
    user_id: str = "me",
) -> list[dict[str, Any]]:
    service = _load_gmail_service()
    result = (
        service.users()
        .messages()
        .list(
            userId=user_id,
            q=query or "",
            maxResults=max(1, max_results),
            includeSpamTrash=include_spam_trash,
        )
        .execute()
    )
    messages = result.get("messages", [])
    return [{"id": m.get("id"), "threadId": m.get("threadId")} for m in messages]


@server.tool(description="Get a Gmail message with headers/snippet and optional body text.")
async def gmail_get_message(
    message_id: str,
    user_id: str = "me",
    include_body: bool = False,
    prefer_html: bool = False,
    max_body_bytes: int = 20000,
) -> dict[str, Any]:
    service = _load_gmail_service()
    fmt = "full" if include_body else "metadata"
    msg = service.users().messages().get(userId=user_id, id=message_id, format=fmt).execute()
    payload = msg.get("payload", {})
    headers = _headers_to_dict(payload.get("headers", []))

    body_text = None
    body_mime = None
    if include_body:
        body_text, body_mime = _extract_message_text(payload, prefer_html=prefer_html, max_bytes=max_body_bytes)

    return {
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "labelIds": msg.get("labelIds", []),
        "snippet": msg.get("snippet"),
        "headers": headers,
        "body_text": body_text,
        "body_mime": body_mime,
    }


@server.tool(description="Send a Gmail message.")
async def gmail_send_message(
    to: str,
    subject: str,
    body: str,
    user_id: str = "me",
    cc: str | None = None,
    bcc: str | None = None,
    body_html: str | None = None,
    reply_to: str | None = None,
    from_alias: str | None = None,
) -> dict[str, Any]:
    service = _load_gmail_service()
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    if reply_to:
        msg["Reply-To"] = reply_to
    if from_alias:
        msg["From"] = from_alias

    msg.set_content(body)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    sent = service.users().messages().send(userId=user_id, body={"raw": raw}).execute()
    return {"id": sent.get("id"), "threadId": sent.get("threadId"), "labelIds": sent.get("labelIds", [])}


@server.tool(description="Modify Gmail message labels (add/remove label IDs).")
async def gmail_modify_labels(
    message_id: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    user_id: str = "me",
) -> dict[str, Any]:
    service = _load_gmail_service()
    body = {"addLabelIds": add_labels or [], "removeLabelIds": remove_labels or []}
    msg = service.users().messages().modify(userId=user_id, id=message_id, body=body).execute()
    return {"id": msg.get("id"), "labelIds": msg.get("labelIds", [])}


@server.tool(description="Move a Gmail message to trash.")
async def gmail_trash_message(message_id: str, user_id: str = "me") -> dict[str, Any]:
    service = _load_gmail_service()
    msg = service.users().messages().trash(userId=user_id, id=message_id).execute()
    return {"id": msg.get("id"), "labelIds": msg.get("labelIds", [])}


@server.tool(description="Delete a Gmail message permanently.")
async def gmail_delete_message(message_id: str, user_id: str = "me") -> str:
    service = _load_gmail_service()
    service.users().messages().delete(userId=user_id, id=message_id).execute()
    return "deleted"


@server.tool(description="List Google Task lists.")
async def tasks_list_tasklists(limit: int = 20) -> list[dict[str, Any]]:
    service = _load_tasks_service()
    result = service.tasklists().list(maxResults=max(1, limit)).execute()
    items = result.get("items", [])
    return [{"id": t.get("id"), "title": t.get("title"), "updated": t.get("updated")} for t in items]


@server.tool(description="Create a Google Task list.")
async def tasks_create_tasklist(title: str) -> dict[str, Any]:
    service = _load_tasks_service()
    created = service.tasklists().insert(body={"title": title}).execute()
    return {"id": created.get("id"), "title": created.get("title")}


@server.tool(description="Delete a Google Task list by id.")
async def tasks_delete_tasklist(tasklist_id: str) -> str:
    service = _load_tasks_service()
    service.tasklists().delete(tasklist=tasklist_id).execute()
    return "deleted"


@server.tool(description="List tasks in a task list.")
async def tasks_list(
    tasklist_id: str = "@default",
    max_results: int = 100,
    show_completed: bool = True,
    show_hidden: bool = False,
    due_min: str | None = None,
    due_max: str | None = None,
) -> list[dict[str, Any]]:
    service = _load_tasks_service()
    kwargs: dict[str, Any] = {
        "tasklist": tasklist_id,
        "maxResults": max(1, max_results),
        "showCompleted": show_completed,
        "showHidden": show_hidden,
    }
    if due_min:
        kwargs["dueMin"] = due_min
    if due_max:
        kwargs["dueMax"] = due_max
    result = service.tasks().list(**kwargs).execute()
    items = result.get("items", [])
    return [
        {
            "id": t.get("id"),
            "title": t.get("title"),
            "status": t.get("status"),
            "due": t.get("due"),
            "completed": t.get("completed"),
            "notes": t.get("notes"),
            "parent": t.get("parent"),
            "position": t.get("position"),
        }
        for t in items
    ]


@server.tool(description="Create a task in a task list.")
async def tasks_create(
    title: str,
    tasklist_id: str = "@default",
    notes: str | None = None,
    due: str | None = None,
    status: str | None = None,
    parent: str | None = None,
    position: str | None = None,
) -> dict[str, Any]:
    service = _load_tasks_service()
    body: dict[str, Any] = {"title": title}
    if notes is not None:
        body["notes"] = notes
    if due is not None:
        body["due"] = due
    if status is not None:
        body["status"] = status
    if parent is not None:
        body["parent"] = parent
    if position is not None:
        body["position"] = position

    created = service.tasks().insert(tasklist=tasklist_id, body=body).execute()
    return {
        "id": created.get("id"),
        "title": created.get("title"),
        "status": created.get("status"),
        "due": created.get("due"),
    }


@server.tool(description="Update a task (patch).")
async def tasks_update(
    task_id: str,
    tasklist_id: str = "@default",
    title: str | None = None,
    notes: str | None = None,
    due: str | None = None,
    status: str | None = None,
    completed: str | None = None,
) -> dict[str, Any]:
    service = _load_tasks_service()
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if notes is not None:
        body["notes"] = notes
    if due is not None:
        body["due"] = due
    if status is not None:
        body["status"] = status
    if completed is not None:
        body["completed"] = completed

    updated = service.tasks().patch(tasklist=tasklist_id, task=task_id, body=body).execute()
    return {
        "id": updated.get("id"),
        "title": updated.get("title"),
        "status": updated.get("status"),
        "due": updated.get("due"),
        "completed": updated.get("completed"),
    }


@server.tool(description="Delete a task by id.")
async def tasks_delete(task_id: str, tasklist_id: str = "@default") -> str:
    service = _load_tasks_service()
    service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
    return "deleted"


@server.tool(description="Clear completed tasks from a task list.")
async def tasks_clear_completed(tasklist_id: str = "@default") -> str:
    service = _load_tasks_service()
    service.tasks().clear(tasklist=tasklist_id).execute()
    return "cleared"


@server.tool(description="Health check; returns 'pong'.")
async def ping() -> str:
    return "pong"


@server.tool(description="List recent session log filenames.")
async def list_session_logs(limit: int = 10) -> list[str]:
    """
    Return up to `limit` most recently modified Markdown logs.
    """
    if not LOG_DIR.exists():
        return []
    files = sorted(
        [p for p in LOG_DIR.glob("*.md") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [p.name for p in files[: max(1, limit)]]


@server.tool(description="Read a session log by filename (must exist in LOG_DIR).")
async def read_session_log(filename: str) -> str:
    """
    Returns the text content of a Markdown log. Prevents path traversal.
    """
    target = (LOG_DIR / filename).resolve()
    if LOG_DIR not in target.parents:
        raise ValueError("Invalid path.")
    if not target.exists():
        raise FileNotFoundError(f"Not found: {filename}")
    return target.read_text(encoding="utf-8")


@server.tool(description="Echo back arguments to verify structured payloads.")
async def echo(payload: dict[str, Any]) -> dict[str, Any]:
    return {"echo": payload}


@server.tool(description="Relay arbitrary text; returns exactly what you send.")
async def relay_text(message: str) -> str:
    """
    Useful when you want ChatGPT to pass raw text straight through this connector
    to Codex without extra formatting.
    """
    return message


@server.tool(
    description="Read a whitelisted file by key (e.g., LAUNCH_CODEX.bat). Returns text content."
)
async def read_whitelisted_file(name: str) -> str:
    """
    Only serves files registered in WHITELISTED_FILES.
    """
    if name not in WHITELISTED_FILES:
        raise ValueError(f"Not allowed or not found: {name}")
    path = WHITELISTED_FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"File missing on disk: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


# ---- Entrypoint ----------------------------------------------------------
if __name__ == "__main__":
    # Choose transport via env, default to streamable-http so it is connector-ready.
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    server.run(transport=transport)

