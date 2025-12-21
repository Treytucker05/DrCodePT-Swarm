from __future__ import annotations

from typing import Optional

from agent.mcp.client import MCPClient
from agent.mcp.registry import get_server, list_servers
from agent.mcp.state import get_active_server, set_active_server


def connect(server_name: str) -> None:
    server = get_server(server_name)
    if server is None:
        print(f"[MCP] Unknown server: {server_name}")
        available = ", ".join(list_servers().keys())
        if available:
            print(f"[MCP] Available servers: {available}")
        return
    set_active_server(server_name)
    print(f"[MCP] Active server set to: {server_name}")


def mcp_list(server_name: Optional[str] = None) -> None:
    name = server_name or get_active_server()
    if not name:
        print("[MCP] No active server. Use Connect: <name> first.")
        return
    server = get_server(name)
    if server is None:
        print(f"[MCP] Unknown server: {name}")
        return
    client = MCPClient(server)
    resp = client.list_tools()
    if resp.error:
        print(f"[MCP] Error: {resp.error}")
        return
    tools = (resp.result or {}).get("tools") if isinstance(resp.result, dict) else None
    if not tools:
        print("[MCP] No tools returned.")
        return
    print(f"[MCP] Tools ({len(tools)}):")
    for tool in tools:
        name = tool.get("name") if isinstance(tool, dict) else None
        desc = tool.get("description") if isinstance(tool, dict) else None
        if name:
            print(f"- {name}" + (f": {desc}" if desc else ""))


__all__ = ["connect", "mcp_list"]
