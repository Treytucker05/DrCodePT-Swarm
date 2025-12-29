"""
Unified Tool Registry - Single registry for all tools (local + MCP).

This is the central registry that the agent loop uses to:
1. List all available tools for planning
2. Execute any tool by name
3. Get tool schemas for LLM function calling
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel

from .types import LocalToolSpec, ToolResult, ToolSpec

logger = logging.getLogger(__name__)


def _register_codex_tools(registry: "UnifiedRegistry") -> int:
    """Register Codex task tools."""
    try:
        from agent.tools.codex_task import CodexTaskArgs, codex_task_tool

        spec = LocalToolSpec(
            name="codex_task",
            args_model=CodexTaskArgs,
            fn=codex_task_tool,
            description="Execute code tasks using Codex CLI (write/edit code, fix bugs, refactor)",
            dangerous=True,  # Can modify files
            approval_required=True,
        )
        registry._local_tools["codex_task"] = spec
        logger.info("Registered codex_task tool")
        return 1
    except ImportError as e:
        logger.warning(f"Could not load codex_task tool: {e}")
        return 0


def _register_calendar_tools(registry: "UnifiedRegistry") -> int:
    """Register calendar tools."""
    try:
        from agent.tools.calendar import CALENDAR_TOOL_SPECS

        count = 0
        for spec_dict in CALENDAR_TOOL_SPECS:
            local_spec = LocalToolSpec(
                name=spec_dict["name"],
                args_model=spec_dict["args_model"],
                fn=spec_dict["fn"],
                description=spec_dict["description"],
                dangerous=False,
                approval_required=False,
            )
            registry._local_tools[spec_dict["name"]] = local_spec
            count += 1

        logger.info(f"Registered {count} calendar tools")
        return count
    except ImportError as e:
        logger.warning(f"Could not load calendar tools: {e}")
        return 0


def _register_memory_tools(registry: "UnifiedRegistry") -> int:
    """Register memory tools."""
    try:
        from agent.tools.memory import MEMORY_TOOL_SPECS

        count = 0
        for spec_dict in MEMORY_TOOL_SPECS:
            local_spec = LocalToolSpec(
                name=spec_dict["name"],
                args_model=spec_dict["args_model"],
                fn=spec_dict["fn"],
                description=spec_dict["description"],
                dangerous=False,
                approval_required=False,
            )
            registry._local_tools[spec_dict["name"]] = local_spec
            count += 1

        logger.info(f"Registered {count} memory tools")
        return count
    except ImportError as e:
        logger.warning(f"Could not load memory tools: {e}")
        return 0


def _register_google_setup_tools(registry: "UnifiedRegistry") -> int:
    """Register Google API setup tools."""
    count = 0

    # Register basic setup tools
    try:
        from agent.tools.google_setup import GOOGLE_SETUP_TOOL_SPECS

        for spec_dict in GOOGLE_SETUP_TOOL_SPECS:
            local_spec = LocalToolSpec(
                name=spec_dict["name"],
                args_model=spec_dict["args_model"],
                fn=spec_dict["fn"],
                description=spec_dict["description"],
                dangerous=False,
                approval_required=True,
            )
            registry._local_tools[spec_dict["name"]] = local_spec
            count += 1
    except ImportError as e:
        logger.debug(f"Could not load google_setup tools: {e}")

    # Register desktop commander setup tools
    try:
        from agent.tools.google_cloud_setup import GOOGLE_CLOUD_SETUP_SPECS

        for spec_dict in GOOGLE_CLOUD_SETUP_SPECS:
            local_spec = LocalToolSpec(
                name=spec_dict["name"],
                args_model=spec_dict["args_model"],
                fn=spec_dict["fn"],
                description=spec_dict["description"],
                dangerous=True,  # Controls desktop
                approval_required=True,
            )
            registry._local_tools[spec_dict["name"]] = local_spec
            count += 1
    except ImportError as e:
        logger.debug(f"Could not load google_cloud_setup tools: {e}")

    if count > 0:
        logger.info(f"Registered {count} Google setup tools")
    return count


class UnifiedRegistry:
    """
    Unified registry that exposes both local and MCP tools through one interface.

    Usage:
        registry = UnifiedRegistry()
        registry.initialize(agent_cfg, run_dir)

        # For the planner
        specs = registry.get_tool_specs()

        # For execution
        result = registry.execute("file_read", {"path": "/some/path"})
        result = registry.execute("google-calendar.list_events", {"timeMin": "..."})
    """

    def __init__(self):
        self._local_tools: Dict[str, LocalToolSpec] = {}
        self._local_registry = None  # The autonomous ToolRegistry
        self._mcp_proxy = None
        self._agent_cfg = None
        self._run_dir: Optional[Path] = None
        self._initialized = False

    def initialize(
        self,
        agent_cfg=None,
        run_dir: Optional[Path] = None,
        memory_store=None,
        load_mcp: bool = True,
    ) -> None:
        """
        Initialize the registry with local and MCP tools.

        Args:
            agent_cfg: AgentConfig for local tools
            run_dir: Working directory for the agent run
            memory_store: Optional SqliteMemoryStore
            load_mcp: Whether to load MCP tools
        """
        if self._initialized:
            return

        self._agent_cfg = agent_cfg
        self._run_dir = run_dir or Path.cwd()

        # Load local tools from autonomous registry
        try:
            from agent.autonomous.config import AgentConfig
            from agent.autonomous.tools.builtins import build_default_tool_registry
            from agent.autonomous.tools.registry import ToolRegistry as AutonomousRegistry

            if agent_cfg is None:
                agent_cfg = AgentConfig()

            self._local_registry = build_default_tool_registry(
                agent_cfg, self._run_dir, memory_store=memory_store
            )

            # Index local tools
            for spec in self._local_registry.list_tools():
                local_spec = LocalToolSpec(
                    name=spec.name,
                    args_model=spec.args_model,
                    fn=spec.fn,
                    description=spec.description,
                    dangerous=spec.dangerous,
                    approval_required=spec.approval_required,
                )
                self._local_tools[spec.name] = local_spec

            logger.info(f"Loaded {len(self._local_tools)} local tools")

        except Exception as e:
            logger.error(f"Failed to load local tools: {e}")

        # Register additional tools (codex, calendar, memory, google setup, etc.)
        extra_tools = 0
        extra_tools += _register_codex_tools(self)
        extra_tools += _register_calendar_tools(self)
        extra_tools += _register_memory_tools(self)
        extra_tools += _register_google_setup_tools(self)
        if extra_tools > 0:
            logger.info(f"Registered {extra_tools} additional tools")

        # Load MCP tools
        if load_mcp:
            try:
                from .mcp_proxy import get_mcp_proxy

                self._mcp_proxy = get_mcp_proxy()
                self._mcp_proxy.initialize()

                mcp_tools = self._mcp_proxy.list_tools()
                logger.info(f"Loaded {len(mcp_tools)} MCP tools")

            except Exception as e:
                logger.warning(f"Failed to load MCP tools: {e}")
                self._mcp_proxy = None

        self._initialized = True
        logger.info(
            f"Unified registry initialized: {len(self._local_tools)} local, "
            f"{len(self._mcp_proxy.list_tools()) if self._mcp_proxy else 0} MCP"
        )

    def get_tool_specs(self) -> List[ToolSpec]:
        """
        Get all available tools as ToolSpec objects.

        This is what the planner uses to know what tools are available.
        """
        if not self._initialized:
            self.initialize()

        specs: List[ToolSpec] = []

        # Add local tools
        for name, local_spec in self._local_tools.items():
            specs.append(local_spec.to_tool_spec())

        # Add MCP tools
        if self._mcp_proxy:
            specs.extend(self._mcp_proxy.get_tool_specs())

        return specs

    def get_tool_names(self) -> List[str]:
        """Get list of all available tool names."""
        if not self._initialized:
            self.initialize()

        names = list(self._local_tools.keys())

        if self._mcp_proxy:
            names.extend(self._mcp_proxy.list_tools())

        return sorted(set(names))

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists."""
        if not self._initialized:
            self.initialize()

        # Check local tools
        if name in self._local_tools:
            return True

        # Check MCP tools
        if self._mcp_proxy and self._mcp_proxy.has_tool(name):
            return True

        return False

    def get_tool_spec(self, name: str) -> Optional[ToolSpec]:
        """Get the spec for a specific tool."""
        if not self._initialized:
            self.initialize()

        # Check local tools
        if name in self._local_tools:
            return self._local_tools[name].to_tool_spec()

        # Check MCP tools
        if self._mcp_proxy:
            mcp_spec = self._mcp_proxy.get_tool(name)
            if mcp_spec:
                return mcp_spec.to_tool_spec()

        return None

    def execute(self, name: str, args: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            name: Tool name (e.g., "file_read" or "google-calendar.list_events")
            args: Tool arguments

        Returns:
            ToolResult with execution outcome
        """
        if not self._initialized:
            self.initialize()

        # Check if it's an MCP tool (has namespace prefix like "server.tool")
        if "." in name and self._mcp_proxy and self._mcp_proxy.has_tool(name):
            return self._mcp_proxy.execute(name, args)

        # Try local tools
        if name in self._local_tools and self._local_registry:
            try:
                # Build context for local tool execution
                from agent.autonomous.config import RunContext

                ctx = RunContext(
                    run_id="unified",
                    run_dir=self._run_dir or Path.cwd(),
                    workspace_dir=self._run_dir or Path.cwd(),
                    profile=getattr(self._agent_cfg, "profile", None) if self._agent_cfg else None,
                    usage=None,
                )

                # Execute through the autonomous registry
                legacy_result = self._local_registry.call(name, args, ctx)

                # Convert to unified ToolResult
                return ToolResult(
                    ok=legacy_result.success,
                    data=legacy_result.output,
                    error=legacy_result.error,
                    metadata=legacy_result.metadata or {},
                    retryable=legacy_result.retryable,
                )

            except Exception as e:
                logger.error(f"Local tool execution failed: {name}: {e}")
                return ToolResult.failure(str(e), retryable=True)

        # Check MCP tools without namespace (fallback)
        if self._mcp_proxy:
            for mcp_name in self._mcp_proxy.list_tools():
                if mcp_name.endswith(f".{name}"):
                    return self._mcp_proxy.execute(mcp_name, args)

        return ToolResult.failure(f"Tool not found: {name}")

    def get_planner_catalog(self) -> List[Dict[str, Any]]:
        """
        Get tool catalog in format suitable for LLM planners.

        Returns list of dicts with: name, description, args_schema, dangerous
        """
        return [spec.to_planner_dict() for spec in self.get_tool_specs()]

    def print_tools(self) -> None:
        """Print all available tools (for debugging)."""
        if not self._initialized:
            self.initialize()

        print("\n" + "=" * 60)
        print("UNIFIED TOOL REGISTRY")
        print("=" * 60)

        print(f"\nLocal Tools ({len(self._local_tools)}):")
        print("-" * 40)
        for name in sorted(self._local_tools.keys()):
            spec = self._local_tools[name]
            danger = " [DANGEROUS]" if spec.dangerous else ""
            print(f"  {name}{danger}")
            if spec.description:
                print(f"    -> {spec.description[:60]}...")

        if self._mcp_proxy:
            mcp_tools = self._mcp_proxy.list_tools()
            print(f"\nMCP Tools ({len(mcp_tools)}):")
            print("-" * 40)

            # Group by server
            by_server: Dict[str, List[str]] = {}
            for tool_name in mcp_tools:
                if "." in tool_name:
                    server, tool = tool_name.split(".", 1)
                else:
                    server, tool = "unknown", tool_name
                by_server.setdefault(server, []).append(tool)

            for server, tools in sorted(by_server.items()):
                print(f"  [{server}]")
                for tool in sorted(tools):
                    print(f"    - {tool}")

        print("\n" + "=" * 60)
        total = len(self._local_tools) + (len(self._mcp_proxy.list_tools()) if self._mcp_proxy else 0)
        print(f"Total: {total} tools available")
        print("=" * 60 + "\n")


# Singleton instance
_registry: Optional[UnifiedRegistry] = None


def get_unified_registry() -> UnifiedRegistry:
    """Get the singleton unified registry instance."""
    global _registry
    if _registry is None:
        _registry = UnifiedRegistry()
    return _registry


__all__ = ["UnifiedRegistry", "get_unified_registry"]
