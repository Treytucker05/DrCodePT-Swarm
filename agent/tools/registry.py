from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

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

