"""
Google Tasks integration helper functions.
"""

from typing import Any, Dict, List, Optional

from agent.mcp.client import MCPClient


class TasksHelper:
    """Helper class for Google Tasks operations."""

    def __init__(self, mcp_client: MCPClient):
        self.client = mcp_client

    async def list_all_tasks(self, task_list_id: str = "@default") -> List[Dict[str, Any]]:
        result = await self.client.call_tool(
            "google-tasks.list_tasks",
            {"tasklist": task_list_id},
        )
        return result.get("tasks", [])

    async def create_task(
        self,
        title: str,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
        task_list_id: str = "@default",
    ) -> Dict[str, Any]:
        args: Dict[str, Any] = {
            "tasklist": task_list_id,
            "title": title,
        }
        if due_date:
            args["due"] = due_date
        if notes:
            args["notes"] = notes
        return await self.client.call_tool("google-tasks.create_task", args)

    async def complete_task(
        self,
        task_id: str,
        task_list_id: str = "@default",
    ) -> Dict[str, Any]:
        return await self.client.call_tool(
            "google-tasks.complete_task",
            {"tasklist": task_list_id, "task": task_id},
        )

    async def search_tasks(
        self,
        query: str,
        task_list_id: str = "@default",
    ) -> List[Dict[str, Any]]:
        result = await self.client.call_tool(
            "google-tasks.search_tasks",
            {"tasklist": task_list_id, "query": query},
        )
        return result.get("tasks", [])

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
        task_list_id: str = "@default",
    ) -> Dict[str, Any]:
        args: Dict[str, Any] = {"tasklist": task_list_id, "task": task_id}
        if title:
            args["title"] = title
        if due_date:
            args["due"] = due_date
        if notes:
            args["notes"] = notes
        return await self.client.call_tool("google-tasks.update_task", args)

    async def delete_task(
        self,
        task_id: str,
        task_list_id: str = "@default",
    ) -> Dict[str, Any]:
        result = await self.client.call_tool(
            "google-tasks.delete_task",
            {"tasklist": task_list_id, "task": task_id},
        )
        return result

    async def get_task_details(
        self,
        task_id: str,
        task_list_id: str = "@default",
    ) -> Dict[str, Any]:
        result = await self.client.call_tool(
            "google-tasks.get_task_details",
            {"tasklist": task_list_id, "task": task_id},
        )
        return result
