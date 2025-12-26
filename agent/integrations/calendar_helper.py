"""
Google Calendar integration helper functions.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agent.mcp.client import MCPClient


class CalendarHelper:
    """Helper class for Google Calendar operations."""

    def __init__(self, mcp_client: MCPClient):
        self.client = mcp_client

    async def get_free_slots(
        self,
        duration_minutes: int = 60,
        days_ahead: int = 7,
    ) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        end = now + timedelta(days=days_ahead)
        result = await self.client.call_tool(
            "google-calendar.find_free_slots",
            {
                "timeMin": now.isoformat() + "Z",
                "timeMax": end.isoformat() + "Z",
                "duration": duration_minutes,
            },
        )
        return result.get("free_slots", [])

    async def check_conflicts(
        self,
        event_title: str,
        start_time: str,
        end_time: str,
    ) -> Dict[str, Any]:
        return await self.client.call_tool(
            "google-calendar.check_conflicts",
            {
                "summary": event_title,
                "start": {"dateTime": start_time},
                "end": {"dateTime": end_time},
            },
        )

    async def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        args: Dict[str, Any] = {
            "summary": title,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }
        if description:
            args["description"] = description
        if location:
            args["location"] = location
        return await self.client.call_tool("google-calendar.create_event", args)

    async def list_events(
        self,
        time_min: str,
        time_max: str,
        calendar_id: str = "primary",
    ) -> List[Dict[str, Any]]:
        result = await self.client.call_tool(
            "google-calendar.list_events",
            {
                "calendarId": calendar_id,
                "timeMin": time_min,
                "timeMax": time_max,
            },
        )
        return result.get("events", [])

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
        args: Dict[str, Any] = {"calendarId": calendar_id, "eventId": event_id}
        if title:
            args["summary"] = title
        if start_time:
            args["start"] = {"dateTime": start_time}
        if end_time:
            args["end"] = {"dateTime": end_time}
        if description:
            args["description"] = description
        if location:
            args["location"] = location
        return await self.client.call_tool("google-calendar.update_event", args)

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> Dict[str, Any]:
        return await self.client.call_tool(
            "google-calendar.delete_event",
            {"calendarId": calendar_id, "eventId": event_id},
        )
