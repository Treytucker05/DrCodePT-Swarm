"""
Tool wrappers for Google Calendar and Tasks integration.
These tools are registered with the agent's tool registry.
"""

import asyncio
import threading
from typing import Any, Dict, Optional

from pydantic import BaseModel

from agent.autonomous.config import RunContext
from agent.autonomous.models import ToolResult
from agent.integrations.calendar_helper import CalendarHelper
from agent.integrations.tasks_helper import TasksHelper


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: Dict[str, Any] = {}
    error: Dict[str, Any] = {}

    def _worker() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:  # pragma: no cover - fallback path
            error["exc"] = exc

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join()
    if error.get("exc"):
        raise error["exc"]
    return result.get("value")


class GetFreeTimeArgs(BaseModel):
    duration_minutes: int = 60
    days_ahead: int = 7


class CheckConflictsArgs(BaseModel):
    event_title: str
    start_time: str
    end_time: str


class CreateCalendarEventArgs(BaseModel):
    title: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None


class ListCalendarEventsArgs(BaseModel):
    time_min: str
    time_max: str
    calendar_id: str = "primary"


class UpdateCalendarEventArgs(BaseModel):
    event_id: str
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    calendar_id: str = "primary"


class DeleteCalendarEventArgs(BaseModel):
    event_id: str
    calendar_id: str = "primary"


class ListAllTasksArgs(BaseModel):
    task_list_id: str = "@default"


class CreateTaskArgs(BaseModel):
    title: str
    due_date: Optional[str] = None
    notes: Optional[str] = None
    task_list_id: str = "@default"


class CompleteTaskArgs(BaseModel):
    task_id: str
    task_list_id: str = "@default"


class SearchTasksArgs(BaseModel):
    query: str
    task_list_id: str = "@default"


class UpdateTaskArgs(BaseModel):
    task_id: str
    title: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    task_list_id: str = "@default"


class DeleteTaskArgs(BaseModel):
    task_id: str
    task_list_id: str = "@default"


class GetTaskDetailsArgs(BaseModel):
    task_id: str
    task_list_id: str = "@default"


class CalendarTasksTools:
    """Tool implementations for calendar and tasks operations.

    Provides two APIs:
    1) Methods used by the agent tool registry that accept a RunContext and typed args (ToolResult).
    2) Async convenience methods used in tests and higher-level code which accept simple kwargs and return dicts.
    """

    def __init__(self, calendar_helper: CalendarHelper, tasks_helper: TasksHelper):
        self.calendar = calendar_helper
        self.tasks = tasks_helper

    # --- Registry-style methods (Synchronous for the ToolRegistry) ---
    
    def get_free_time(self, ctx: RunContext, args: GetFreeTimeArgs) -> ToolResult:
        try:
            slots = _run_async(self.calendar.get_free_slots(args.duration_minutes, args.days_ahead))
            return ToolResult(success=True, output={"free_slots": slots, "count": len(slots)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def check_calendar_conflicts(self, ctx: RunContext, args: CheckConflictsArgs) -> ToolResult:
        try:
            conflicts = _run_async(
                self.calendar.check_conflicts(args.event_title, args.start_time, args.end_time)
            )
            events = conflicts.get("conflicts")
            if isinstance(events, bool):
                has_conflicts = events
                events = conflicts.get("events", [])
            else:
                if events is None:
                    events = conflicts.get("events", [])
                has_conflicts = conflicts.get("has_conflicts")
                if has_conflicts is None:
                    has_conflicts = bool(events)
            return ToolResult(
                success=True,
                output={
                    "has_conflicts": bool(has_conflicts),
                    "conflicting_events": events,
                },
            )
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def create_calendar_event(self, ctx: RunContext, args: CreateCalendarEventArgs) -> ToolResult:
        try:
            event = _run_async(
                self.calendar.create_event(
                    args.title,
                    args.start_time,
                    args.end_time,
                    args.description,
                    args.location,
                )
            )
            return ToolResult(success=True, output={"event": event, "event_id": event.get("id")})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def list_calendar_events(self, ctx: RunContext, args: ListCalendarEventsArgs) -> ToolResult:
        try:
            events = _run_async(
                self.calendar.list_events(args.time_min, args.time_max, args.calendar_id)
            )
            return ToolResult(success=True, output={"events": events, "count": len(events)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def update_calendar_event(self, ctx: RunContext, args: UpdateCalendarEventArgs) -> ToolResult:
        try:
            event = _run_async(
                self.calendar.update_event(
                    args.event_id,
                    args.title,
                    args.start_time,
                    args.end_time,
                    args.description,
                    args.location,
                    args.calendar_id,
                )
            )
            return ToolResult(success=True, output={"event": event})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def delete_calendar_event(self, ctx: RunContext, args: DeleteCalendarEventArgs) -> ToolResult:
        try:
            result = _run_async(self.calendar.delete_event(args.event_id, args.calendar_id))
            return ToolResult(success=True, output={"result": result})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def list_all_tasks(self, ctx: RunContext, args: ListAllTasksArgs) -> ToolResult:
        try:
            tasks = _run_async(self.tasks.list_all_tasks(tasklist_id=args.task_list_id))
            return ToolResult(success=True, output={"tasks": tasks, "count": len(tasks)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def create_task(self, ctx: RunContext, args: CreateTaskArgs) -> ToolResult:
        try:
            task = _run_async(
                self.tasks.create_task(
                    title=args.title,
                    tasklist_id=args.task_list_id,
                    notes=args.notes,
                    due=args.due_date,
                )
            )
            return ToolResult(success=True, output={"task": task, "task_id": task.get("id")})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def complete_task(self, ctx: RunContext, args: CompleteTaskArgs) -> ToolResult:
        try:
            task = _run_async(self.tasks.complete_task(args.task_id, args.task_list_id))
            return ToolResult(success=True, output={"task": task})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def search_tasks(self, ctx: RunContext, args: SearchTasksArgs) -> ToolResult:
        try:
            tasks = _run_async(self.tasks.search_tasks(query=args.query, tasklist_id=args.task_list_id))
            return ToolResult(success=True, output={"tasks": tasks, "count": len(tasks)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def update_task(self, ctx: RunContext, args: UpdateTaskArgs) -> ToolResult:
        try:
            task = _run_async(
                self.tasks.update_task(
                    task_id=args.task_id,
                    title=args.title,
                    notes=args.notes,
                    due=args.due_date,
                    tasklist_id=args.task_list_id,
                )
            )
            return ToolResult(success=True, output={"task": task})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def delete_task(self, ctx: RunContext, args: DeleteTaskArgs) -> ToolResult:
        try:
            result = _run_async(self.tasks.delete_task(args.task_id, args.task_list_id))
            return ToolResult(success=True, output={"result": result})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def get_task_details(self, ctx: RunContext, args: GetTaskDetailsArgs) -> ToolResult:
        try:
            task = _run_async(self.tasks.get_task_details(args.task_id, args.task_list_id))
            return ToolResult(success=True, output={"task": task})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    # --- Async convenience wrappers for direct use / tests (keeping these renamed to avoid collisions) ---

    async def get_free_time_async(self, duration_minutes: int = 60, days_ahead: int = 7) -> Dict[str, Any]:
        try:
            slots = await self.calendar.get_free_slots(duration_minutes, days_ahead)
            return {"success": True, "output": {"free_slots": slots, "count": len(slots)}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def check_calendar_conflicts_async(self, event_title: str, start_time: str, end_time: str) -> Dict[str, Any]:
        try:
            conflicts = await self.calendar.check_conflicts(event_title, start_time, end_time)
            events = conflicts.get("conflicts")
            if isinstance(events, bool):
                has_conflicts = events
                events = conflicts.get("events", [])
            else:
                if events is None:
                    events = conflicts.get("events", [])
                has_conflicts = conflicts.get("has_conflicts")
                if has_conflicts is None:
                    has_conflicts = bool(events)
            return {"success": True, "output": {"has_conflicts": bool(has_conflicts), "conflicting_events": events}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def create_calendar_event_async(self, title: str, start_time: str, end_time: str, description: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        try:
            event = await self.calendar.create_event(title, start_time, end_time, description, location)
            return {"success": True, "output": {"event": event, "event_id": event.get("id")}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def list_calendar_events_async(self, time_min: str, time_max: str, calendar_id: str = "primary") -> Dict[str, Any]:
        try:
            events = await self.calendar.list_events(time_min, time_max, calendar_id)
            return {"success": True, "output": {"events": events, "count": len(events)}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def list_all_tasks_async(self, task_list_id: str = "@default") -> Dict[str, Any]:
        try:
            tasks = await self.tasks.list_all_tasks(tasklist_id=task_list_id)
            return {"success": True, "output": {"tasks": tasks, "count": len(tasks)}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def create_task_async(self, title: str, notes: Optional[str] = None, due_date: Optional[str] = None, task_list_id: str = "@default") -> Dict[str, Any]:
        try:
            task = await self.tasks.create_task(
                title=title,
                tasklist_id=task_list_id,
                notes=notes,
                due=due_date,
            )
            return {"success": True, "output": {"task": task, "task_id": task.get("id")}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def search_tasks_async(self, query: str, task_list_id: str = "@default") -> Dict[str, Any]:
        try:
            tasks = await self.tasks.search_tasks(query=query, tasklist_id=task_list_id)
            return {"success": True, "output": {"tasks": tasks, "count": len(tasks)}}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
