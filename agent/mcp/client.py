"""
Enhanced MCP Client with multi-server support for Calendar, Tasks, and Memory.
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPServerConfig:
    """Configuration for a single MCP server."""

    def __init__(self, name: str, command: str, args: List[str], env: Dict[str, str]):
        self.name = name
        self.command = command
        self.args = args
        self.env = env


class MCPClient:
    """
    Multi-server MCP client supporting Calendar, Tasks, Memory, and Filesystem.

    Features:
    - Lazy initialization (servers start on first use)
    - Tool discovery and registration
    - Namespaced tool calls (e.g., "google-calendar.list_events")
    - Error handling and recovery
    - Structured logging
    """

    def __init__(self, config_path: Path = None):
        """
        Initialize MCP client.

        Args:
            config_path: Path to servers.json config file
        """
        self.config_path = config_path or Path(__file__).parent / "servers.json"
        self.servers: Dict[str, MCPServerConfig] = {}
        self.sessions: Dict[str, Any] = {}  # Active server sessions
        self.available_tools: Dict[str, Dict[str, Any]] = {}  # Namespaced tools
        self._load_config()

    def _load_config(self):
        """Load server configuration from JSON file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return

        try:
            with open(self.config_path) as f:
                config = json.load(f)

            for server_name, server_config in config.items():
                self.servers[server_name] = MCPServerConfig(
                    name=server_name,
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    env=server_config.get("env", {}),
                )

            logger.info(f"Loaded {len(self.servers)} MCP server configs")

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    async def initialize(self, servers: Optional[List[str]] = None):
        """
        Initialize specified MCP servers (or all if not specified).

        Args:
            servers: List of server names to initialize (e.g., ["google-calendar", "google-tasks"])
        """
        servers_to_init = servers or list(self.servers.keys())

        for server_name in servers_to_init:
            if server_name not in self.servers:
                logger.warning(f"Server {server_name} not found in config")
                continue

            try:
                await self._start_server(server_name)
            except Exception as e:
                logger.error(f"Failed to initialize {server_name}: {e}")

    async def _start_server(self, server_name: str):
        """Start a single MCP server and discover its tools."""
        if server_name in self.sessions:
            logger.debug(f"Server {server_name} already running")
            return

        config = self.servers[server_name]
        logger.info(f"Starting MCP server: {server_name}")

        try:
            # For now, we'll use a simple approach: store config for later use
            # In production, you'd use stdio transport to communicate with the server
            self.sessions[server_name] = {"config": config, "status": "initialized"}

            # Discover tools (this would normally call the server)
            # For now, we'll register known tools
            await self._discover_tools(server_name)

            logger.info(f"Server {server_name} initialized successfully")

        except Exception as e:
            logger.error(f"Error starting server {server_name}: {e}")
            raise

    async def _discover_tools(self, server_name: str):
        """Discover available tools from a server."""
        # This is a placeholder - in production, you'd call the server's list_tools
        # For now, we'll register known tools based on server type

        known_tools = {
            "google-calendar": [
                "list_calendars",
                "list_events",
                "create_event",
                "update_event",
                "delete_event",
                "find_free_slots",
                "check_conflicts",
                "get_event_details",
            ],
            "google-tasks": [
                "list_task_lists",
                "list_tasks",
                "create_task",
                "update_task",
                "delete_task",
                "complete_task",
                "search_tasks",
                "get_task_details",
            ],
            "memory": [
                "create_entity",
                "search_nodes",
                "create_relation",
                "get_entity",
                "delete_entity",
            ],
            "obsidian": [
                "read_note",
                "write_note",
                "list_notes",
                "search_notes",
                "create_note",
                "update_note",
                "delete_note",
            ],
            "filesystem": [
                "read_file",
                "write_file",
                "list_directory",
                "delete_file",
                "create_directory",
            ],
        }

        tools = known_tools.get(server_name, [])
        for tool_name in tools:
            full_name = f"{server_name}.{tool_name}"
            self.available_tools[full_name] = {
                "server": server_name,
                "tool_name": tool_name,
                "description": f"{tool_name} from {server_name}",
            }

        logger.info(f"Discovered {len(tools)} tools from {server_name}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool from any MCP server.

        Args:
            tool_name: Full tool name (e.g., "google-calendar.list_events")
            arguments: Tool arguments

        Returns:
            Tool result
        """
        # Extract server name from tool name (e.g., "google-calendar.list_events" -> "google-calendar")
        server_name = tool_name.split(".", 1)[0]
        
        # Initialize server if needed (this will discover tools)
        if server_name not in self.sessions:
            await self._start_server(server_name)
        
        # Now check if tool exists after server initialization
        if tool_name not in self.available_tools:
            raise ValueError(
                f"Tool {tool_name} not found. Available tools: {list(self.available_tools.keys())}"
            )

        tool_info = self.available_tools[tool_name]

        logger.info(f"Calling tool: {tool_name} with args: {arguments}")

        # In production, this would use stdio transport to communicate with the server
        # For now, return a placeholder
        return {
            "success": True,
            "tool": tool_name,
            "arguments": arguments,
            "result": "Tool execution placeholder",
        }

    def list_tools(self, server: Optional[str] = None) -> List[str]:
        """
        List available tools.

        Args:
            server: Filter by server name (optional)

        Returns:
            List of tool names
        """
        if server:
            return [
                name
                for name in self.available_tools.keys()
                if name.startswith(f"{server}.")
            ]
        return list(self.available_tools.keys())

    async def shutdown(self):
        """Shutdown all active server sessions."""
        for server_name in list(self.sessions.keys()):
            logger.info(f"Shutting down server: {server_name}")
            self.sessions.pop(server_name, None)


# Convenience functions for common operations


async def get_calendar_events(
    client: MCPClient, time_min: str, time_max: str
) -> Dict[str, Any]:
    """Get calendar events for a time range."""
    return await client.call_tool(
        "google-calendar.list_events",
        {"timeMin": time_min, "timeMax": time_max},
    )


async def create_calendar_event(
    client: MCPClient, title: str, start_time: str, end_time: str
) -> Dict[str, Any]:
    """Create a calendar event."""
    return await client.call_tool(
        "google-calendar.create_event",
        {"summary": title, "start": {"dateTime": start_time}, "end": {"dateTime": end_time}},
    )


async def list_tasks(client: MCPClient) -> Dict[str, Any]:
    """List all tasks."""
    return await client.call_tool("google-tasks.list_tasks", {})


async def create_task(
    client: MCPClient, title: str, due_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new task."""
    args = {"title": title}
    if due_date:
        args["due"] = due_date
    return await client.call_tool("google-tasks.create_task", args)
