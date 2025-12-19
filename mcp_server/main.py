"""
Minimal MCP server (FastMCP) exposing a few helper tools for PT Study Brain.

Transports:
- streamable-http on http://127.0.0.1:8765/mcp  (safe default; set MCP_HOST=0.0.0.0 to expose)
- stdio (for local CLI testing)
"""

from __future__ import annotations

import os
import datetime as _dt
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
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

# --- Google Calendar OAuth settings ---------------------------------------
# Path to your OAuth client JSON from Google Cloud.
GCAL_CLIENT_SECRET = Path(
    os.environ.get("GOOGLE_CLIENT_SECRET_JSON", str(SECRETS_DIR / "google_client_secret.json"))
)
# Where the user token will be cached after the first consent flow.
GCAL_TOKEN_PATH = Path(
    os.environ.get("GOOGLE_CALENDAR_TOKEN_JSON", str(SECRETS_DIR / "google_calendar_token.json"))
)
GCAL_SCOPES = [
    # Change to the minimal scopes you need; this allows create/update/delete.
    "https://www.googleapis.com/auth/calendar.events",
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
def _load_calendar_service(force_refresh: bool = False):
    """
    Returns a googleapiclient Calendar service, running the installed-app OAuth
    flow on first use. The consent screen will open a browser window locally.
    """
    if not GCAL_CLIENT_SECRET.exists():
        raise FileNotFoundError(
            f"Missing Google OAuth client JSON at {GCAL_CLIENT_SECRET}. "
            "Download it from Google Cloud -> Credentials (Web/Installed app)."
        )

    creds: Credentials | None = None
    if GCAL_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(GCAL_TOKEN_PATH, GCAL_SCOPES)

    if force_refresh and creds and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GCAL_CLIENT_SECRET, GCAL_SCOPES
            )
            # Port 0 picks a free port and opens a local browser tab for consent.
            creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        GCAL_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        GCAL_TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds)


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

