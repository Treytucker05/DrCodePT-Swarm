from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class McpServerSpec:
    name: str
    command: str
    args: list[str]
    env: Dict[str, str]


@dataclass
class McpToolInfo:
    """Information about an MCP tool."""
    name: str
    server: str
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.server}.{self.name}"


def _registry_path() -> Path:
    return Path(__file__).resolve().parent / "servers.json"


def load_registry() -> Dict[str, McpServerSpec]:
    path = _registry_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, McpServerSpec] = {}
    for name, spec in data.items():
        if not isinstance(spec, dict):
            continue
        cmd = str(spec.get("command") or "").strip()
        if not cmd:
            continue
        args = spec.get("args") or []
        env = spec.get("env") or {}
        if not isinstance(args, list):
            args = []
        if not isinstance(env, dict):
            env = {}
        out[name] = McpServerSpec(name=name, command=cmd, args=[str(a) for a in args], env={str(k): str(v) for k, v in env.items()})
    return out


def get_server(name: str) -> Optional[McpServerSpec]:
    return load_registry().get(name)


def list_servers() -> Dict[str, McpServerSpec]:
    return load_registry()


def list_available_tools() -> List[McpToolInfo]:
    """
    List all available MCP tools from configured servers.

    This provides tool metadata for the unified registry.
    """
    from agent.tools.mcp_proxy import MCP_TOOL_DEFINITIONS

    tools: List[McpToolInfo] = []
    servers = load_registry()

    for server_name in servers.keys():
        if server_name in MCP_TOOL_DEFINITIONS:
            for tool_name, tool_def in MCP_TOOL_DEFINITIONS[server_name].items():
                tools.append(McpToolInfo(
                    name=tool_name,
                    server=server_name,
                    description=tool_def.get("description", ""),
                    input_schema=tool_def.get("input_schema", {}),
                ))

    return tools


def get_tool_info(full_name: str) -> Optional[McpToolInfo]:
    """
    Get info for a specific MCP tool.

    Args:
        full_name: Full tool name like "google-calendar.list_events"
    """
    if "." not in full_name:
        return None

    server, tool_name = full_name.split(".", 1)
    for tool in list_available_tools():
        if tool.server == server and tool.name == tool_name:
            return tool

    return None
