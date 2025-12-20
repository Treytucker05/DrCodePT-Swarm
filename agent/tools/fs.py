from __future__ import annotations

"""
Filesystem tool (read/write/append).

Safe-by-default: writes should be gated by unsafe_mode by the supervisor.
"""

from pathlib import Path
from typing import Any, Dict

from .base import ToolAdapter, ToolResult


class FsTool(ToolAdapter):
    tool_name = "fs"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        path = inputs.get("path") or getattr(task, "path", None)
        if not path:
            return ToolResult(False, error="fs requires path")

        mode = (inputs.get("mode") or getattr(task, "mode", None) or "").strip().lower()
        content = inputs.get("content") if "content" in inputs else getattr(task, "content", None)

        p = Path(path)

        if mode in {"read", ""} and content in (None, ""):
            if not p.exists():
                return ToolResult(False, error=f"File not found: {p}")
            data = p.read_text(encoding="utf-8", errors="replace")
            return ToolResult(True, output={"path": str(p), "content": data})

        if content is None:
            content = ""

        p.parent.mkdir(parents=True, exist_ok=True)
        if mode == "append":
            with p.open("a", encoding="utf-8", errors="replace", newline="\n") as f:
                f.write(str(content))
        else:
            p.write_text(str(content), encoding="utf-8", errors="replace")
        return ToolResult(True, output={"path": str(p), "bytes": len(str(content).encode("utf-8"))})


__all__ = ["FsTool"]

