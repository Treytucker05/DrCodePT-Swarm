"""
Calendar Skill - First-class Google Calendar integration.

This skill provides high-level calendar operations:
- List upcoming events
- Get next event
- Create events
- Check free/busy times

Authentication is handled via Google OAuth2.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AuthStatus, Skill, SkillResult

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    id: str
    summary: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    html_link: Optional[str] = None

    @staticmethod
    def from_google_event(event: Dict[str, Any]) -> "CalendarEvent":
        """Parse Google Calendar API event response."""
        start_data = event.get("start", {})
        end_data = event.get("end", {})

        # Handle all-day events (date) vs time-specific events (dateTime)
        if "dateTime" in start_data:
            start = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
        else:
            start = datetime.fromisoformat(start_data.get("date", ""))

        if "dateTime" in end_data:
            end = datetime.fromisoformat(end_data["dateTime"].replace("Z", "+00:00"))
        else:
            end = datetime.fromisoformat(end_data.get("date", ""))

        return CalendarEvent(
            id=event.get("id", ""),
            summary=event.get("summary", "No title"),
            start=start,
            end=end,
            description=event.get("description"),
            location=event.get("location"),
            html_link=event.get("htmlLink"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "description": self.description,
            "location": self.location,
            "html_link": self.html_link,
        }


class CalendarSkill(Skill):
    """
    Google Calendar skill.

    Provides high-level calendar operations with proper OAuth handling.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]

    def __init__(self, credentials_path: Optional[Path] = None):
        """
        Initialize calendar skill.

        Args:
            credentials_path: Path to OAuth credentials file. If None,
                              will look in standard locations.
        """
        self._credentials_path = credentials_path
        self._creds = None
        self._service = None

    @property
    def name(self) -> str:
        return "calendar"

    @property
    def description(self) -> str:
        return "Google Calendar integration for viewing and managing calendar events"

    def get_capabilities(self) -> List[str]:
        return [
            "list_events",
            "next_event",
            "create_event",
            "today_events",
            "free_busy",
        ]

    def auth_status(self) -> AuthStatus:
        """Check if Google Calendar is authenticated."""
        try:
            creds = self._get_credentials()
            if creds is None:
                return AuthStatus.NOT_CONFIGURED

            if creds.expired:
                if creds.refresh_token:
                    return AuthStatus.AUTH_EXPIRED
                return AuthStatus.NEEDS_AUTH

            if creds.valid:
                return AuthStatus.AUTHENTICATED

            return AuthStatus.NEEDS_AUTH
        except Exception as e:
            logger.debug(f"Auth status check failed: {e}")
            return AuthStatus.NOT_CONFIGURED

    def _get_credentials(self):
        """Get or load Google credentials."""
        if self._creds is not None:
            return self._creds

        try:
            # Try to load from credential store
            from agent.memory.credentials import get_credential

            creds_data = get_credential("google_apis")
            if not creds_data:
                return None

            token_data = creds_data.get("token")
            if not token_data:
                return None

            from google.oauth2.credentials import Credentials

            self._creds = Credentials.from_authorized_user_info(
                json.loads(token_data), self.SCOPES
            )
            return self._creds
        except ImportError:
            logger.warning("Google API libraries not installed")
            return None
        except Exception as e:
            logger.debug(f"Failed to load credentials: {e}")
            return None

    def _get_service(self):
        """Get or create the Calendar API service."""
        if self._service is not None:
            return self._service

        creds = self._get_credentials()
        if creds is None:
            return None

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            try:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
                self._creds = creds

                # Save refreshed credentials
                from agent.memory.credentials import save_credential

                save_credential(
                    "google_apis",
                    "token",
                    json.dumps(
                        {
                            "token": creds.token,
                            "refresh_token": creds.refresh_token,
                            "token_uri": creds.token_uri,
                            "client_id": creds.client_id,
                            "client_secret": creds.client_secret,
                            "scopes": list(creds.scopes) if creds.scopes else [],
                        }
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                return None

        try:
            from googleapiclient.discovery import build

            self._service = build("calendar", "v3", credentials=creds)
            return self._service
        except Exception as e:
            logger.error(f"Failed to build calendar service: {e}")
            return None

    def begin_oauth(self) -> Optional[str]:
        """Start OAuth flow for Google Calendar."""
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow

            # Look for client secrets file
            secrets_paths = [
                Path("credentials.json"),
                Path("client_secrets.json"),
                Path.home() / ".config" / "drcodept" / "google_credentials.json",
            ]

            secrets_file = None
            for p in secrets_paths:
                if p.exists():
                    secrets_file = p
                    break

            if not secrets_file:
                logger.error("No Google OAuth credentials file found")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                str(secrets_file), self.SCOPES
            )
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(prompt="consent")
            return auth_url
        except Exception as e:
            logger.error(f"Failed to start OAuth: {e}")
            return None

    def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
        calendar_id: str = "primary",
    ) -> SkillResult:
        """
        List calendar events.

        Args:
            time_min: Start of time range (defaults to now)
            time_max: End of time range (defaults to 7 days from now)
            max_results: Maximum number of events to return
            calendar_id: Calendar ID (default: primary)

        Returns:
            SkillResult with list of CalendarEvent
        """
        service = self._get_service()
        if service is None:
            status = self.auth_status()
            if status == AuthStatus.NOT_CONFIGURED:
                return SkillResult(
                    ok=False,
                    error="Google Calendar not configured. Please set up OAuth credentials.",
                    needs_auth=True,
                    auth_url=self.begin_oauth(),
                )
            return SkillResult(
                ok=False,
                error="Calendar authentication required",
                needs_auth=True,
            )

        try:
            if time_min is None:
                time_min = datetime.utcnow()
            if time_max is None:
                time_max = time_min + timedelta(days=7)

            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = events_result.get("items", [])
            calendar_events = [CalendarEvent.from_google_event(e) for e in events]

            return SkillResult(
                ok=True,
                data=[e.to_dict() for e in calendar_events],
            )
        except Exception as e:
            logger.error(f"Failed to list events: {e}")
            return SkillResult(ok=False, error=str(e))

    def next_event(self, calendar_id: str = "primary") -> SkillResult:
        """
        Get the next upcoming calendar event.

        Args:
            calendar_id: Calendar ID (default: primary)

        Returns:
            SkillResult with next CalendarEvent or None
        """
        result = self.list_events(max_results=1, calendar_id=calendar_id)
        if not result.ok:
            return result

        events = result.data
        if not events:
            return SkillResult(ok=True, data=None)

        return SkillResult(ok=True, data=events[0])

    def today_events(self, calendar_id: str = "primary") -> SkillResult:
        """
        Get all events for today.

        Args:
            calendar_id: Calendar ID (default: primary)

        Returns:
            SkillResult with list of today's events
        """
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return self.list_events(
            time_min=start_of_day,
            time_max=end_of_day,
            max_results=50,
            calendar_id=calendar_id,
        )

    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> SkillResult:
        """
        Create a new calendar event.

        Args:
            summary: Event title
            start: Start time
            end: End time
            description: Optional description
            location: Optional location
            calendar_id: Calendar ID (default: primary)

        Returns:
            SkillResult with created event
        """
        service = self._get_service()
        if service is None:
            return SkillResult(
                ok=False,
                error="Calendar authentication required",
                needs_auth=True,
            )

        try:
            event_body = {
                "summary": summary,
                "start": {
                    "dateTime": start.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end.isoformat(),
                    "timeZone": "UTC",
                },
            }

            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location

            event = service.events().insert(
                calendarId=calendar_id, body=event_body
            ).execute()

            return SkillResult(
                ok=True,
                data=CalendarEvent.from_google_event(event).to_dict(),
            )
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return SkillResult(ok=False, error=str(e))

    def free_busy(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        calendar_id: str = "primary",
    ) -> SkillResult:
        """
        Get free/busy information for a time range.

        Args:
            time_min: Start of time range (defaults to now)
            time_max: End of time range (defaults to end of today)
            calendar_id: Calendar ID (default: primary)

        Returns:
            SkillResult with busy periods
        """
        service = self._get_service()
        if service is None:
            return SkillResult(
                ok=False,
                error="Calendar authentication required",
                needs_auth=True,
            )

        try:
            if time_min is None:
                time_min = datetime.utcnow()
            if time_max is None:
                time_max = time_min.replace(hour=23, minute=59, second=59)

            body = {
                "timeMin": time_min.isoformat() + "Z",
                "timeMax": time_max.isoformat() + "Z",
                "items": [{"id": calendar_id}],
            }

            result = service.freebusy().query(body=body).execute()
            calendars = result.get("calendars", {})
            calendar_data = calendars.get(calendar_id, {})
            busy_periods = calendar_data.get("busy", [])

            return SkillResult(ok=True, data=busy_periods)
        except Exception as e:
            logger.error(f"Failed to get free/busy: {e}")
            return SkillResult(ok=False, error=str(e))
