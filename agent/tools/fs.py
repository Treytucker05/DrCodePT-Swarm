from __future__ import annotations

"""Filesystem tool with allowlist enforcement."""

import shutil
from pathlib import Path
from typing import Any, Dict, List

from .base import ToolAdapter, ToolResult
from agent.supervisor.hardening import snapshot_before_write


def _resolve_allowed_paths(base_dir: Path, allowed: List[str]) -> List[Path]:
    resolved = []
    for p in allowed or []:
        path_obj = Path(p)
        if not path_obj.is_absolute():
            path_obj = (base_dir / path_obj).resolve()
        else:
            path_obj = path_obj.resolve()
        resolved.append(path_obj)
    return resolved


def _is_allowed(target: Path, allowed: List[Path]) -> bool:
    target = target.resolve()
    for root in allowed:
        try:
            target.relative_to(root)
            return True
        except ValueError:
            continue
    return False


class FilesystemTool(ToolAdapter):
    tool_name = "fs"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        op = inputs.get("op", "read")
        path_value = inputs.get("path") or getattr(task, "path", None)
        if not path_value:
            return ToolResult(False, error="No path provided for fs operation")

        base_dir = Path(__file__).resolve().parents[1]
        allowed_roots = _resolve_allowed_paths(base_dir, getattr(task, "allowed_paths", []))
        target = Path(path_value)
        if not target.is_absolute():
            target = (base_dir / target).resolve()

        if not _is_allowed(target, allowed_roots):
            return ToolResult(False, error=f"Path {target} outside allowlist")

        run_path = inputs.get("run_path")

        try:
            if op == "read":
                content = target.read_text(encoding="utf-8")
                return ToolResult(True, output={"content": content})
            if op == "write":
                data = inputs.get("content", "")
                if run_path:
                    snapshot_before_write(Path(run_path), target)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(str(data), encoding="utf-8")
                return ToolResult(True, output={"bytes_written": len(str(data))})
            if op == "move":
                dest = inputs.get("dest")
                if not dest:
                    return ToolResult(False, error="Missing dest for move")
                dest_path = Path(dest)
                if not dest_path.is_absolute():
                    dest_path = (base_dir / dest_path).resolve()
                if not _is_allowed(dest_path, allowed_roots):
                    return ToolResult(False, error=f"Destination {dest_path} outside allowlist")
                if run_path:
                    snapshot_before_write(Path(run_path), target)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(target), str(dest_path))
                return ToolResult(True, output={"moved_to": str(dest_path)})
            if op == "search":
                pattern = inputs.get("pattern", "*")
                matches = [str(p) for p in target.rglob(pattern)]
                return ToolResult(True, output={"matches": matches})
            return ToolResult(False, error=f"Unsupported fs op '{op}'")
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))
