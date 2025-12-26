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
    """Tool implementations for calendar and tasks operations."""

    def __init__(self, calendar_helper: CalendarHelper, tasks_helper: TasksHelper):
        self.calendar = calendar_helper
        self.tasks = tasks_helper

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
            return ToolResult(
                success=True,
                output={
                    "has_conflicts": bool(conflicts.get("has_conflicts")),
                    "conflicting_events": conflicts.get("conflicts", []),
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
            tasks = _run_async(self.tasks.list_all_tasks(args.task_list_id))
            return ToolResult(success=True, output={"tasks": tasks, "count": len(tasks)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def create_task(self, ctx: RunContext, args: CreateTaskArgs) -> ToolResult:
        try:
            task = _run_async(
                self.tasks.create_task(args.title, args.due_date, args.notes, args.task_list_id)
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
            tasks = _run_async(self.tasks.search_tasks(args.query, args.task_list_id))
            return ToolResult(success=True, output={"tasks": tasks, "count": len(tasks)})
        except Exception as exc:
            return ToolResult(success=False, error=str(exc))

    def update_task(self, ctx: RunContext, args: UpdateTaskArgs) -> ToolResult:
        try:
            task = _run_async(
                self.tasks.update_task(
                    args.task_id,
                    args.title,
                    args.due_date,
                    args.notes,
                    args.task_list_id,
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
