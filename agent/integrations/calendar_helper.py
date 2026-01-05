"""
Google Calendar integration helper functions.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from .google_auth import get_google_creds
import time
import hashlib
import json

class CalendarHelper:
    """Helper class for Google Calendar operations using real Google API."""

    def __init__(self, mcp_client=None):
        # We ignore mcp_client and use direct API since MCP is currently a placeholder
        self.creds = get_google_creds()
        self.service = None
        if self.creds:
            self.service = build('calendar', 'v3', credentials=self.creds)

        # Simple in-memory cache: {cache_key: (result, timestamp)}
        # Cache TTL: 60 seconds (reasonable for calendar queries)
        self._cache = {}
        self._cache_ttl = 60

    def _check_service(self):
        if not self.service:
            # Try to re-load
            self.creds = get_google_creds()
            if self.creds:
                self.service = build('calendar', 'v3', credentials=self.creds)
        if not self.service:
            raise RuntimeError("Google Calendar service not initialized. Run setup_google_calendar.py")

    @staticmethod
    def _parse_rfc3339(value: str) -> datetime:
        """Parse RFC3339 datetime string into timezone-aware datetime."""
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @staticmethod
    def _format_rfc3339(value: datetime) -> str:
        """Format datetime as RFC3339 string in UTC."""
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    async def get_free_slots(
        self,
        duration_minutes: int = 60,
        days_ahead: int = 7,
    ) -> List[Dict[str, Any]]:
        self._check_service()
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        cache_key = self._make_cache_key(
            "free_slots",
            time_min=self._format_rfc3339(now),
            time_max=self._format_rfc3339(end),
            duration_minutes=duration_minutes,
            calendar_id="primary",
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        body = {
            "timeMin": self._format_rfc3339(now),
            "timeMax": self._format_rfc3339(end),
            "items": [{"id": "primary"}],
        }
        response = self.service.freebusy().query(body=body).execute()
        busy = (
            response.get("calendars", {})
            .get("primary", {})
            .get("busy", [])
        )

        # Convert busy intervals to sorted datetime tuples
        busy_intervals = []
        for interval in busy:
            try:
                start = self._parse_rfc3339(interval["start"])
                end_dt = self._parse_rfc3339(interval["end"])
                busy_intervals.append((start, end_dt))
            except Exception:
                continue
        busy_intervals.sort(key=lambda x: x[0])

        # Merge overlapping busy intervals
        merged = []
        for start, end_dt in busy_intervals:
            if not merged:
                merged.append((start, end_dt))
                continue
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end_dt))
            else:
                merged.append((start, end_dt))

        # Compute free slots of given duration
        slots: List[Dict[str, Any]] = []
        cursor = now
        duration = timedelta(minutes=duration_minutes)

        for start, end_dt in merged:
            if start > cursor:
                window_end = start
                slot_start = cursor
                while slot_start + duration <= window_end:
                    slot_end = slot_start + duration
                    slots.append({
                        "start": self._format_rfc3339(slot_start),
                        "end": self._format_rfc3339(slot_end),
                    })
                    slot_start = slot_end
            cursor = max(cursor, end_dt)

        # Trailing free time until end
        if cursor < end:
            slot_start = cursor
            while slot_start + duration <= end:
                slot_end = slot_start + duration
                slots.append({
                    "start": self._format_rfc3339(slot_start),
                    "end": self._format_rfc3339(slot_end),
                })
                slot_start = slot_end

        self._set_cache(cache_key, slots)
        return slots

    async def check_conflicts(
        self,
        event_title: str,
        start_time: str,
        end_time: str,
    ) -> Dict[str, Any]:
        self._check_service()
        results = self.service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
        ).execute()
        events = results.get('items', [])
        return {"has_conflicts": bool(events), "conflicts": events}

    async def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._check_service()
        event = {
            'summary': title,
            'description': description,
            'location': location,
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
        }
        return self.service.events().insert(calendarId='primary', body=event).execute()

    def _make_cache_key(self, method: str, **kwargs) -> str:
        """Create cache key from method name and args."""
        payload = {"method": method, **kwargs}
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid."""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            # Expired - remove it
            del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, result: Any) -> None:
        """Store result in cache with current timestamp."""
        self._cache[cache_key] = (result, time.time())

    async def list_events(
        self,
        time_min: str,
        time_max: str,
        calendar_id: str = "primary",
    ) -> List[Dict[str, Any]]:
        # Check cache first
        cache_key = self._make_cache_key("list_events", time_min=time_min, time_max=time_max, calendar_id=calendar_id)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._check_service()
        results = self.service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = results.get('items', [])

        # Cache the result
        self._set_cache(cache_key, events)
        return events

    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = "primary",
    ) -> Dict[str, Any]:
        self._check_service()
        # First get the existing event
        event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        if title: event['summary'] = title
        if start_time: event['start'] = {'dateTime': start_time}
        if end_time: event['end'] = {'dateTime': end_time}
        if description: event['description'] = description
        if location: event['location'] = location
        
        return self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> Dict[str, Any]:
        self._check_service()
        self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"success": True}
