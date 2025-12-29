"""
MCP Proxy - Adapter for calling MCP tools through the unified registry.

This module provides a thin wrapper around agent/mcp/client.py that:
1. Discovers available MCP tools at initialization
2. Exposes them as ToolSpec objects
3. Executes MCP tool calls and returns ToolResult objects
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .types import McpToolSpec, ToolResult, ToolSpec

logger = logging.getLogger(__name__)


# Known MCP tool definitions with their schemas
# These are used when we can't dynamically discover from the server
MCP_TOOL_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "google-calendar": {
        "list_calendars": {
            "description": "List all available calendars",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        "list_events": {
            "description": "List calendar events in a time range",
            "input_schema": {
                "type": "object",
                "properties": {
                    "timeMin": {"type": "string", "description": "Start time (ISO 8601)"},
                    "timeMax": {"type": "string", "description": "End time (ISO 8601)"},
                    "calendarId": {"type": "string", "description": "Calendar ID (default: primary)"},
                    "maxResults": {"type": "integer", "description": "Max events to return"},
                },
                "required": [],
            },
        },
        "create_event": {
            "description": "Create a new calendar event",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start": {"type": "object", "description": "Start time object"},
                    "end": {"type": "object", "description": "End time object"},
                    "description": {"type": "string", "description": "Event description"},
                    "location": {"type": "string", "description": "Event location"},
                },
                "required": ["summary", "start", "end"],
            },
        },
        "update_event": {
            "description": "Update an existing calendar event",
            "input_schema": {
                "type": "object",
                "properties": {
                    "eventId": {"type": "string", "description": "Event ID"},
                    "summary": {"type": "string", "description": "New title"},
                    "start": {"type": "object", "description": "New start time"},
                    "end": {"type": "object", "description": "New end time"},
                },
                "required": ["eventId"],
            },
        },
        "delete_event": {
            "description": "Delete a calendar event",
            "input_schema": {
                "type": "object",
                "properties": {
                    "eventId": {"type": "string", "description": "Event ID to delete"},
                },
                "required": ["eventId"],
            },
        },
        "find_free_slots": {
            "description": "Find free time slots in a date range",
            "input_schema": {
                "type": "object",
                "properties": {
                    "timeMin": {"type": "string", "description": "Start of range"},
                    "timeMax": {"type": "string", "description": "End of range"},
                    "duration": {"type": "integer", "description": "Slot duration in minutes"},
                },
                "required": ["timeMin", "timeMax"],
            },
        },
        "check_conflicts": {
            "description": "Check if a proposed time conflicts with existing events",
            "input_schema": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "Proposed start time"},
                    "end": {"type": "string", "description": "Proposed end time"},
                },
                "required": ["start", "end"],
            },
        },
    },
    "google-tasks": {
        "list_task_lists": {
            "description": "List all task lists",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        "list_tasks": {
            "description": "List tasks from a task list",
            "input_schema": {
                "type": "object",
                "properties": {
                    "taskListId": {"type": "string", "description": "Task list ID"},
                    "showCompleted": {"type": "boolean", "description": "Include completed tasks"},
                },
                "required": [],
            },
        },
        "create_task": {
            "description": "Create a new task",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "notes": {"type": "string", "description": "Task notes"},
                    "due": {"type": "string", "description": "Due date (ISO 8601)"},
                    "taskListId": {"type": "string", "description": "Task list ID"},
                },
                "required": ["title"],
            },
        },
        "update_task": {
            "description": "Update an existing task",
            "input_schema": {
                "type": "object",
                "properties": {
                    "taskId": {"type": "string", "description": "Task ID"},
                    "title": {"type": "string", "description": "New title"},
                    "notes": {"type": "string", "description": "New notes"},
                    "due": {"type": "string", "description": "New due date"},
                },
                "required": ["taskId"],
            },
        },
        "delete_task": {
            "description": "Delete a task",
            "input_schema": {
                "type": "object",
                "properties": {
                    "taskId": {"type": "string", "description": "Task ID to delete"},
                },
                "required": ["taskId"],
            },
        },
        "complete_task": {
            "description": "Mark a task as complete",
            "input_schema": {
                "type": "object",
                "properties": {
                    "taskId": {"type": "string", "description": "Task ID to complete"},
                },
                "required": ["taskId"],
            },
        },
        "search_tasks": {
            "description": "Search tasks by title or notes",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
    },
    "filesystem": {
        "read_file": {
            "description": "Read contents of a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"},
                },
                "required": ["path"],
            },
        },
        "write_file": {
            "description": "Write contents to a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
        "list_directory": {
            "description": "List contents of a directory",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                },
                "required": ["path"],
            },
        },
        "delete_file": {
            "description": "Delete a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to delete"},
                },
                "required": ["path"],
            },
        },
        "create_directory": {
            "description": "Create a directory",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to create"},
                },
                "required": ["path"],
            },
        },
    },
    "github": {
        "list_repos": {
            "description": "List repositories for a user or organization",
            "input_schema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Username or org name"},
                },
                "required": [],
            },
        },
        "get_repo": {
            "description": "Get details of a repository",
            "input_schema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                },
                "required": ["owner", "repo"],
            },
        },
        "list_issues": {
            "description": "List issues in a repository",
            "input_schema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "state": {"type": "string", "description": "Issue state (open, closed, all)"},
                },
                "required": ["owner", "repo"],
            },
        },
        "create_issue": {
            "description": "Create a new issue",
            "input_schema": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue body"},
                },
                "required": ["owner", "repo", "title"],
            },
        },
    },
    "memory": {
        "create_entity": {
            "description": "Create a memory entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name"},
                    "type": {"type": "string", "description": "Entity type"},
                    "data": {"type": "object", "description": "Entity data"},
                },
                "required": ["name", "type"],
            },
        },
        "search_nodes": {
            "description": "Search memory nodes",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
        "get_entity": {
            "description": "Get a memory entity by name",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name"},
                },
                "required": ["name"],
            },
        },
        "delete_entity": {
            "description": "Delete a memory entity",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name to delete"},
                },
                "required": ["name"],
            },
        },
    },
}


class McpProxy:
    """
    Proxy for accessing MCP tools through a unified interface.

    This class:
    1. Loads MCP server configurations
    2. Exposes available tools as ToolSpec objects
    3. Routes tool calls to the appropriate MCP server
    """

    def __init__(self):
        self._client = None
        self._tools: Dict[str, McpToolSpec] = {}
        self._initialized = False

    def _load_tool_specs(self) -> None:
        """Load tool specs from known definitions."""
        for server_name, tools in MCP_TOOL_DEFINITIONS.items():
            for tool_name, tool_def in tools.items():
                spec = McpToolSpec(
                    name=tool_name,
                    description=tool_def.get("description", ""),
                    input_schema=tool_def.get("input_schema", {}),
                    server_name=server_name,
                )
                full_name = f"{server_name}.{tool_name}"
                self._tools[full_name] = spec

    def initialize(self) -> None:
        """Initialize the proxy (synchronous version)."""
        if self._initialized:
            return

        # Load tool definitions
        self._load_tool_specs()

        # Try to import and initialize MCP client
        try:
            from agent.mcp.client import MCPClient
            self._client = MCPClient()
            logger.info(f"MCP client loaded with {len(self._client.servers)} server configs")
        except Exception as e:
            logger.warning(f"Could not initialize MCP client: {e}")
            self._client = None

        self._initialized = True
        logger.info(f"MCP proxy initialized with {len(self._tools)} tool specs")

    async def initialize_async(self, servers: Optional[List[str]] = None) -> None:
        """Initialize the proxy and connect to servers (async version)."""
        self.initialize()

        if self._client:
            try:
                await self._client.initialize(servers)
                # Update tool list from actual server discovery
                for tool_name, tool_info in self._client.available_tools.items():
                    if tool_name not in self._tools:
                        server = tool_info.get("server", "unknown")
                        self._tools[tool_name] = McpToolSpec(
                            name=tool_info.get("tool_name", tool_name),
                            description=tool_info.get("description", ""),
                            input_schema={},
                            server_name=server,
                        )
            except Exception as e:
                logger.error(f"Failed to initialize MCP servers: {e}")

    def get_tool_specs(self) -> List[ToolSpec]:
        """Get all available MCP tools as ToolSpec objects."""
        if not self._initialized:
            self.initialize()

        return [spec.to_tool_spec() for spec in self._tools.values()]

    def list_tools(self) -> List[str]:
        """List all available MCP tool names."""
        if not self._initialized:
            self.initialize()

        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is available."""
        if not self._initialized:
            self.initialize()

        return name in self._tools

    def get_tool(self, name: str) -> Optional[McpToolSpec]:
        """Get a specific tool spec by name."""
        if not self._initialized:
            self.initialize()

        return self._tools.get(name)

    def execute(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """
        Execute an MCP tool synchronously.

        Args:
            tool_name: Full tool name (e.g., "google-calendar.list_events")
            args: Tool arguments

        Returns:
            ToolResult with the execution outcome
        """
        if not self._initialized:
            self.initialize()

        if tool_name not in self._tools:
            return ToolResult.failure(f"MCP tool not found: {tool_name}")

        if self._client is None:
            return ToolResult.failure("MCP client not available")

        try:
            # Run async call in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._client.call_tool(tool_name, args)
                    )
                    result = future.result(timeout=60)
            else:
                result = loop.run_until_complete(
                    self._client.call_tool(tool_name, args)
                )

            if isinstance(result, dict):
                success = result.get("success", False)
                return ToolResult(
                    ok=success,
                    data=result.get("result"),
                    error=result.get("error") if not success else None,
                    metadata={"tool": tool_name, "args": args},
                )
            return ToolResult.success(data=result)

        except Exception as e:
            logger.error(f"MCP tool execution failed: {tool_name}: {e}")
            return ToolResult.failure(str(e), retryable=True)

    async def execute_async(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """
        Execute an MCP tool asynchronously.

        Args:
            tool_name: Full tool name (e.g., "google-calendar.list_events")
            args: Tool arguments

        Returns:
            ToolResult with the execution outcome
        """
        if not self._initialized:
            self.initialize()

        if tool_name not in self._tools:
            return ToolResult.failure(f"MCP tool not found: {tool_name}")

        if self._client is None:
            return ToolResult.failure("MCP client not available")

        try:
            result = await self._client.call_tool(tool_name, args)

            if isinstance(result, dict):
                success = result.get("success", False)
                return ToolResult(
                    ok=success,
                    data=result.get("result"),
                    error=result.get("error") if not success else None,
                    metadata={"tool": tool_name, "args": args},
                )
            return ToolResult.success(data=result)

        except Exception as e:
            logger.error(f"MCP tool execution failed: {tool_name}: {e}")
            return ToolResult.failure(str(e), retryable=True)


# Singleton instance
_proxy: Optional[McpProxy] = None


def get_mcp_proxy() -> McpProxy:
    """Get the singleton MCP proxy instance."""
    global _proxy
    if _proxy is None:
        _proxy = McpProxy()
    return _proxy


__all__ = ["McpProxy", "get_mcp_proxy", "MCP_TOOL_DEFINITIONS"]
