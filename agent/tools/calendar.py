"""
Calendar Tools - Stable wrappers for calendar MCP operations.

These tools wrap MCP calls into stable, well-documented tool interfaces:
- calendar_list_events
- calendar_create_event
- calendar_update_event
- calendar_delete_event
- calendar_find_free_slots

The agent can use these directly without knowing MCP internals.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models for Tool Arguments
# ============================================================================

class CalendarEventsArgs(BaseModel):
    """Arguments for listing calendar events via Google Calendar API."""
    start_date: str = Field(
        ...,
        description="Start date (YYYY-MM-DD) in local time",
    )
    end_date: str = Field(
        ...,
        description="End date (YYYY-MM-DD) in local time",
    )
    calendar_id: str = Field(
        default="primary",
        description="Calendar ID. Use 'primary' for main calendar",
    )
    max_results: int = Field(
        default=20,
        description="Maximum number of events to return",
    )


class ListEventsArgs(BaseModel):
    """Arguments for listing calendar events."""
    time_min: Optional[str] = Field(
        None,
        description="Start time (ISO 8601, e.g., '2024-01-15T00:00:00Z'). Default: now"
    )
    time_max: Optional[str] = Field(
        None,
        description="End time (ISO 8601). Default: 7 days from now"
    )
    calendar_id: str = Field(
        default="primary",
        description="Calendar ID. Use 'primary' for main calendar"
    )
    max_results: int = Field(
        default=10,
        description="Maximum number of events to return"
    )


class CreateEventArgs(BaseModel):
    """Arguments for creating a calendar event."""
    summary: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Start time (ISO 8601)")
    end_time: str = Field(..., description="End time (ISO 8601)")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    calendar_id: str = Field(default="primary", description="Calendar ID")


class UpdateEventArgs(BaseModel):
    """Arguments for updating a calendar event."""
    event_id: str = Field(..., description="ID of the event to update")
    summary: Optional[str] = Field(None, description="New title")
    start_time: Optional[str] = Field(None, description="New start time")
    end_time: Optional[str] = Field(None, description="New end time")
    description: Optional[str] = Field(None, description="New description")
    location: Optional[str] = Field(None, description="New location")
    calendar_id: str = Field(default="primary", description="Calendar ID")


class DeleteEventArgs(BaseModel):
    """Arguments for deleting a calendar event."""
    event_id: str = Field(..., description="ID of the event to delete")
    calendar_id: str = Field(default="primary", description="Calendar ID")


class FindFreeSlotsArgs(BaseModel):
    """Arguments for finding free time slots."""
    time_min: str = Field(..., description="Start of search range (ISO 8601)")
    time_max: str = Field(..., description="End of search range (ISO 8601)")
    duration_minutes: int = Field(
        default=60,
        description="Desired slot duration in minutes"
    )
    calendar_id: str = Field(default="primary", description="Calendar ID")


# ============================================================================
# Tool Implementations
# ============================================================================

def _get_mcp_proxy():
    """Get MCP proxy for calendar operations."""
    from agent.tools.mcp_proxy import get_mcp_proxy
    return get_mcp_proxy()


def _format_datetime(dt_str: Optional[str] = None, default_offset_days: int = 0) -> str:
    """Format datetime string, with defaults."""
    if dt_str:
        return dt_str
    dt = datetime.now() + timedelta(days=default_offset_days)
    return dt.isoformat() + "Z"


def _parse_local_date(value: str) -> datetime:
    """Parse a date or datetime string and return tz-aware datetime."""
    if not value:
        raise ValueError("Missing date value")
    dt = datetime.fromisoformat(value)
    local_tz = datetime.now().astimezone().tzinfo
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=local_tz)
    return dt


def get_calendar_events(ctx, args: CalendarEventsArgs) -> Dict[str, Any]:
    """
    List calendar events using the Google Calendar skill (read-only).

    Returns dict with success, events, and optional setup guide on auth errors.
    """
    try:
        from agent.skills.google_calendar import GoogleCalendarSkill
        from agent.skills.base import AuthStatus
    except Exception as exc:
        return {"success": False, "error": f"Calendar skill unavailable: {exc}"}

    skill = GoogleCalendarSkill()
    status = skill.auth_status()
    if status == AuthStatus.NOT_CONFIGURED:
        return {
            "success": False,
            "error": "Google Calendar credentials.json missing",
            "needs_auth": True,
            "setup_guide": skill.setup_guide(),
        }

    try:
        time_min = _parse_local_date(args.start_date)
        time_max = _parse_local_date(args.end_date)
    except Exception as exc:
        return {"success": False, "error": f"Invalid date range: {exc}"}

    result = skill.list_events(
        time_min=time_min,
        time_max=time_max,
        max_results=args.max_results,
        calendar_id=args.calendar_id,
    )

    if result.ok:
        return {
            "success": True,
            "events": result.data or [],
            "time_range": {"start": time_min.isoformat(), "end": time_max.isoformat()},
        }

    payload = {
        "success": False,
        "error": result.error or "Failed to list events",
        "needs_auth": result.needs_auth,
    }
    if result.needs_auth:
        payload["setup_guide"] = skill.setup_guide()
    return payload


def calendar_list_events(ctx, args: ListEventsArgs):
    """
    List calendar events in a time range.

    Returns list of events with id, summary, start, end.
    """
    from agent.autonomous.models import ToolResult

    try:
        proxy = _get_mcp_proxy()

        # Default time range: now to 7 days from now
        time_min = _format_datetime(args.time_min, 0)
        time_max = _format_datetime(args.time_max, 7)

        mcp_args = {
            "timeMin": time_min,
            "timeMax": time_max,
            "calendarId": args.calendar_id,
            "maxResults": args.max_results,
        }

        result = proxy.execute("google-calendar.list_events", mcp_args)

        if result.ok:
            return ToolResult(
                success=True,
                output={
                    "events": result.data,
                    "time_range": {"start": time_min, "end": time_max},
                },
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Failed to list events",
                retryable=True,
            )

    except Exception as e:
        logger.error(f"calendar_list_events failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


def calendar_create_event(ctx, args: CreateEventArgs):
    """
    Create a new calendar event.

    Returns the created event ID.
    """
    from agent.autonomous.models import ToolResult

    try:
        proxy = _get_mcp_proxy()

        mcp_args = {
            "summary": args.summary,
            "start": {"dateTime": args.start_time},
            "end": {"dateTime": args.end_time},
            "calendarId": args.calendar_id,
        }

        if args.description:
            mcp_args["description"] = args.description
        if args.location:
            mcp_args["location"] = args.location

        result = proxy.execute("google-calendar.create_event", mcp_args)

        if result.ok:
            return ToolResult(
                success=True,
                output={
                    "message": f"Created event: {args.summary}",
                    "event": result.data,
                },
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Failed to create event",
                retryable=True,
            )

    except Exception as e:
        logger.error(f"calendar_create_event failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


def calendar_update_event(ctx, args: UpdateEventArgs):
    """
    Update an existing calendar event.

    Only updates fields that are provided.
    """
    from agent.autonomous.models import ToolResult

    try:
        proxy = _get_mcp_proxy()

        mcp_args = {
            "eventId": args.event_id,
            "calendarId": args.calendar_id,
        }

        if args.summary:
            mcp_args["summary"] = args.summary
        if args.start_time:
            mcp_args["start"] = {"dateTime": args.start_time}
        if args.end_time:
            mcp_args["end"] = {"dateTime": args.end_time}
        if args.description:
            mcp_args["description"] = args.description
        if args.location:
            mcp_args["location"] = args.location

        result = proxy.execute("google-calendar.update_event", mcp_args)

        if result.ok:
            return ToolResult(
                success=True,
                output={
                    "message": f"Updated event: {args.event_id}",
                    "event": result.data,
                },
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Failed to update event",
                retryable=True,
            )

    except Exception as e:
        logger.error(f"calendar_update_event failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


def calendar_delete_event(ctx, args: DeleteEventArgs):
    """
    Delete a calendar event.
    """
    from agent.autonomous.models import ToolResult

    try:
        proxy = _get_mcp_proxy()

        mcp_args = {
            "eventId": args.event_id,
            "calendarId": args.calendar_id,
        }

        result = proxy.execute("google-calendar.delete_event", mcp_args)

        if result.ok:
            return ToolResult(
                success=True,
                output={"message": f"Deleted event: {args.event_id}"},
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Failed to delete event",
                retryable=False,  # Don't retry deletes
            )

    except Exception as e:
        logger.error(f"calendar_delete_event failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=False,
        )


def calendar_find_free_slots(ctx, args: FindFreeSlotsArgs):
    """
    Find free time slots in the calendar.

    Returns list of available time slots of the requested duration.
    """
    from agent.autonomous.models import ToolResult

    try:
        proxy = _get_mcp_proxy()

        mcp_args = {
            "timeMin": args.time_min,
            "timeMax": args.time_max,
            "duration": args.duration_minutes,
            "calendarId": args.calendar_id,
        }

        result = proxy.execute("google-calendar.find_free_slots", mcp_args)

        if result.ok:
            return ToolResult(
                success=True,
                output={
                    "free_slots": result.data,
                    "duration_minutes": args.duration_minutes,
                },
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Failed to find free slots",
                retryable=True,
            )

    except Exception as e:
        logger.error(f"calendar_find_free_slots failed: {e}")
        return ToolResult(
            success=False,
            error=str(e),
            retryable=True,
        )


# ============================================================================
# Tool Specs for Registry
# ============================================================================

CALENDAR_TOOL_SPECS = [
    {
        "name": "calendar_list_events",
        "args_model": ListEventsArgs,
        "fn": calendar_list_events,
        "description": "List calendar events in a time range (default: next 7 days)",
    },
    {
        "name": "calendar_create_event",
        "args_model": CreateEventArgs,
        "fn": calendar_create_event,
        "description": "Create a new calendar event",
    },
    {
        "name": "calendar_update_event",
        "args_model": UpdateEventArgs,
        "fn": calendar_update_event,
        "description": "Update an existing calendar event",
    },
    {
        "name": "calendar_delete_event",
        "args_model": DeleteEventArgs,
        "fn": calendar_delete_event,
        "description": "Delete a calendar event",
    },
    {
        "name": "calendar_find_free_slots",
        "args_model": FindFreeSlotsArgs,
        "fn": calendar_find_free_slots,
        "description": "Find free time slots in the calendar",
    },
]


def register_calendar_tools(registry) -> None:
    """Register all calendar tools with a ToolRegistry."""
    from agent.autonomous.tools.registry import ToolSpec

    for spec in CALENDAR_TOOL_SPECS:
        registry.register(ToolSpec(
            name=spec["name"],
            args_model=spec["args_model"],
            fn=spec["fn"],
            description=spec["description"],
        ))


__all__ = [
    "CalendarEventsArgs",
    "ListEventsArgs",
    "CreateEventArgs",
    "UpdateEventArgs",
    "DeleteEventArgs",
    "FindFreeSlotsArgs",
    "get_calendar_events",
    "calendar_list_events",
    "calendar_create_event",
    "calendar_update_event",
    "calendar_delete_event",
    "calendar_find_free_slots",
    "register_calendar_tools",
    "CALENDAR_TOOL_SPECS",
]
