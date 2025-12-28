from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from .base import ToolAdapter


@dataclass(frozen=True)
class ToolSpec:
    adapter: ToolAdapter
    dangerous: bool = False


_TOOLS: Dict[str, ToolSpec] = {}


def _register(spec: ToolSpec) -> None:
    name = spec.adapter.tool_name
    if not name:
        raise ValueError("ToolAdapter.tool_name is required")
    _TOOLS[name] = spec


def _init_defaults() -> None:
    if _TOOLS:
        return

    # Local imports to keep import-time side effects minimal.
    from .api import ApiTool
    from .browser import BrowserTool
    from .code_review import CodeReviewTool
    from .desktop import DesktopTool
    from .fs import FsTool
    from .notify import NotifyTool
    from .python_exec import PythonTool
    from .research import ResearchTool
    from .screen_recorder import ScreenRecorderTool
    from .shell import ShellTool
    from .vision import VisionTool

    _register(ToolSpec(adapter=BrowserTool(), dangerous=True))
    _register(ToolSpec(adapter=ShellTool(), dangerous=True))
    _register(ToolSpec(adapter=PythonTool(), dangerous=True))
    _register(ToolSpec(adapter=FsTool(), dangerous=True))
    _register(ToolSpec(adapter=ApiTool(), dangerous=False))
    _register(ToolSpec(adapter=DesktopTool(), dangerous=True))
    _register(ToolSpec(adapter=VisionTool(), dangerous=True))
    _register(ToolSpec(adapter=ScreenRecorderTool(), dangerous=True))
    _register(ToolSpec(adapter=NotifyTool(), dangerous=False))
    _register(ToolSpec(adapter=CodeReviewTool(), dangerous=True))
    _register(ToolSpec(adapter=ResearchTool(), dangerous=False))


def get_tool(name: str) -> Optional[ToolSpec]:
    _init_defaults()
    return _TOOLS.get(name)


def list_tools() -> Dict[str, ToolSpec]:
    _init_defaults()
    return dict(_TOOLS)


__all__ = ["ToolSpec", "get_tool", "list_tools"]


def build_react_tool_map(
    *,
    run_dir: Path,
    unsafe_mode: bool = False,
    enable_web_gui: bool = False,
    enable_desktop: bool = False,
    memory_db_path: Optional[Path] = None,
) -> Tuple[Dict[str, Callable[..., Any]], Dict[str, str]]:
    """Build a callable tool map for the ReAct loop using the autonomous tool registry."""

    from agent.tools.react_wrappers import read_file, web_fetch, web_search, write_file

    from agent.autonomous.config import AgentConfig
    from agent.autonomous.tools.builtins import build_default_tool_registry
    from agent.autonomous.memory.sqlite_store import SqliteMemoryStore

    run_dir.mkdir(parents=True, exist_ok=True)

    tool_map: Dict[str, Callable[..., Any]] = {
        "web_search": web_search,
        "web_fetch": web_fetch,
        "read_file": read_file,
        "write_file": write_file,
    }
    tool_descriptions: Dict[str, str] = {}

    cfg = AgentConfig(
        unsafe_mode=unsafe_mode,
        enable_web_gui=enable_web_gui,
        enable_desktop=enable_desktop,
        allow_interactive_tools=True,
        allow_human_ask=True,
        memory_db_path=memory_db_path,
    )

    memory_store = SqliteMemoryStore(memory_db_path) if memory_db_path else None
    registry = build_default_tool_registry(cfg, run_dir, memory_store=memory_store)

    for spec in registry.list_tools():
        name = spec.name
        tool_descriptions[name] = spec.description or ""

        def _make_call(tool_name: str) -> Callable[..., Any]:
            def _call(**kwargs: Any) -> Any:
                return registry.execute(tool_name, kwargs, run_dir=run_dir)

            return _call

        tool_map[name] = _make_call(name)

    print(f"[TOOLS] Available: {list(tool_map.keys())}")

    return tool_map, tool_descriptions


__all__.append("build_react_tool_map")
