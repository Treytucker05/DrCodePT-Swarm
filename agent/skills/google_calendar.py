from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AuthStatus, Skill, SkillResult

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_DIR = Path.home() / ".drcodept_swarm" / "google_calendar"
DEFAULT_CREDENTIALS_PATH = DEFAULT_BASE_DIR / "credentials.json"
DEFAULT_TOKEN_PATH = DEFAULT_BASE_DIR / "token.json"

ENV_CREDENTIALS = "GOOGLE_CALENDAR_CREDENTIALS"
ENV_TOKEN = "GOOGLE_CALENDAR_TOKEN"


class GoogleCalendarSkill(Skill):
    """Google Calendar skill using the official API client."""

    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(
        self,
        credentials_path: Optional[Path] = None,
        token_path: Optional[Path] = None,
    ) -> None:
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._creds = None
        self._service = None

    @property
    def name(self) -> str:
        return "calendar"

    @property
    def description(self) -> str:
        return "Google Calendar integration (read-only events listing)"

    def get_capabilities(self) -> List[str]:
        return ["list_events", "list_tomorrow_events"]

    def auth_status(self) -> AuthStatus:
        credentials_file = self._find_credentials_file()
        if not credentials_file:
            return AuthStatus.NOT_CONFIGURED

        token_file = self._resolve_token_path()
        if not token_file.exists():
            return AuthStatus.NEEDS_AUTH

        creds = self._load_credentials()
        if not creds:
            return AuthStatus.NEEDS_AUTH
        if getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            return AuthStatus.AUTH_EXPIRED
        if getattr(creds, "valid", False):
            return AuthStatus.AUTHENTICATED
        return AuthStatus.NEEDS_AUTH

    def begin_oauth(self) -> Optional[str]:
        credentials_file = self._find_credentials_file()
        if not credentials_file:
            logger.error("Google Calendar credentials.json not found")
            return None
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file),
                self.SCOPES,
            )
            auth_url, _ = flow.authorization_url(prompt="consent")
            creds = flow.run_local_server(port=0, prompt="consent", open_browser=True)
            self._save_credentials(creds)
            return auth_url
        except Exception as exc:
            logger.error(f"Google OAuth failed: {exc}")
            return None

    def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 20,
        calendar_id: str = "primary",
    ) -> SkillResult:
        service = self._get_service()
        if service is None:
            status = self.auth_status()
            if status == AuthStatus.NOT_CONFIGURED:
                return SkillResult(
                    ok=False,
                    error="Google Calendar credentials.json missing",
                    needs_auth=True,
                )
            if status in {AuthStatus.NEEDS_AUTH, AuthStatus.AUTH_EXPIRED}:
                auth_url = self.begin_oauth()
                if not auth_url:
                    return SkillResult(
                        ok=False,
                        error="Google Calendar OAuth required",
                        needs_auth=True,
                    )
                service = self._get_service()
            if service is None:
                return SkillResult(
                    ok=False,
                    error="Google Calendar authentication required",
                    needs_auth=True,
                )

        if time_min is None:
            time_min = datetime.now().astimezone()
        if time_max is None:
            time_max = time_min + timedelta(days=7)

        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            items = events_result.get("items", [])
            events = [self._normalize_event(e) for e in items]
            return SkillResult(ok=True, data=events)
        except Exception as exc:
            logger.error(f"Failed to list calendar events: {exc}")
            return SkillResult(ok=False, error=str(exc))

    def list_tomorrow_events(self, max_results: int = 20) -> SkillResult:
        now = datetime.now().astimezone()
        tomorrow = (now + timedelta(days=1)).date()
        start = datetime.combine(tomorrow, datetime.min.time(), tzinfo=now.tzinfo)
        end = start + timedelta(days=1)
        return self.list_events(time_min=start, time_max=end, max_results=max_results)

    def setup_guide(self) -> str:
        credentials_path = DEFAULT_CREDENTIALS_PATH
        return (
            "Google Calendar setup (one-time):\n"
            f"1. Create OAuth credentials in Google Cloud Console (Desktop app)\n"
            f"2. Enable Google Calendar API for the project\n"
            f"3. Download the credentials JSON and save it to:\n"
            f"   {credentials_path}\n"
            f"4. Re-run the request so the browser OAuth flow can finish\n"
            f"(Optional) Set {ENV_CREDENTIALS} to a custom credentials.json path."
        )

    def _ensure_base_dir(self) -> None:
        try:
            DEFAULT_BASE_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _resolve_credentials_path(self) -> Optional[Path]:
        if self._credentials_path:
            return Path(self._credentials_path)
        env_path = (os.getenv(ENV_CREDENTIALS) or "").strip()
        if env_path:
            return Path(os.path.expanduser(env_path))
        return DEFAULT_CREDENTIALS_PATH

    def _resolve_token_path(self) -> Path:
        if self._token_path:
            return Path(self._token_path)
        env_path = (os.getenv(ENV_TOKEN) or "").strip()
        if env_path:
            return Path(os.path.expanduser(env_path))
        return DEFAULT_TOKEN_PATH

    def _find_credentials_file(self) -> Optional[Path]:
        candidate = self._resolve_credentials_path()
        if candidate and candidate.exists():
            return candidate

        repo_candidates = [
            Path.cwd() / "credentials.json",
            Path.cwd() / "client_secrets.json",
            REPO_ROOT / "agent" / "memory" / "google_client_secret.json",
        ]
        for path in repo_candidates:
            if path.exists():
                return path
        return None

    def _load_credentials(self):
        token_file = self._resolve_token_path()
        if not token_file.exists():
            return None
        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)
        except Exception as exc:
            logger.debug(f"Failed to load Google credentials: {exc}")
            return None

        if getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            try:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
                self._save_credentials(creds)
            except Exception as exc:
                logger.error(f"Failed to refresh Google credentials: {exc}")
                return None

        self._creds = creds
        return creds

    def _save_credentials(self, creds) -> None:
        try:
            self._ensure_base_dir()
            token_file = self._resolve_token_path()
            token_file.write_text(creds.to_json(), encoding="utf-8")
        except Exception as exc:
            logger.error(f"Failed to save Google token: {exc}")

    def _get_service(self):
        if self._service is not None:
            return self._service

        creds = self._load_credentials()
        if creds is None:
            return None

        try:
            from googleapiclient.discovery import build

            self._service = build("calendar", "v3", credentials=creds)
            return self._service
        except Exception as exc:
            logger.error(f"Failed to build Google Calendar service: {exc}")
            return None

    def _normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": event.get("id", ""),
            "summary": event.get("summary", "No title"),
            "start": event.get("start", {}),
            "end": event.get("end", {}),
            "location": event.get("location"),
            "description": event.get("description"),
            "htmlLink": event.get("htmlLink"),
        }


__all__ = ["GoogleCalendarSkill", "DEFAULT_CREDENTIALS_PATH", "DEFAULT_TOKEN_PATH"]
