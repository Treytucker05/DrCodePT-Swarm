from __future__ import annotations

"""
Python execution tool.

Safe-by-default: execution is considered unsafe unless explicitly enabled by the supervisor.
"""

import subprocess
import sys
from typing import Any, Dict

from .base import ToolAdapter, ToolResult


class PythonExecTool(ToolAdapter):
    tool_name = "python"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        code = inputs.get("code") or inputs.get("script") or getattr(task, "script", None)
        if not code:
            return ToolResult(False, error="No script provided for python task")

        timeout_seconds = inputs.get("timeout_seconds") or getattr(task, "timeout_seconds", None) or 60
        cwd = inputs.get("cwd") or getattr(task, "cwd", None) or None

        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=int(timeout_seconds),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, error=f"python timeout after {timeout_seconds}s", retryable=True)
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))

        output = {"exit_code": proc.returncode, "stdout": proc.stdout or "", "stderr": proc.stderr or ""}
        if proc.returncode == 0:
            return ToolResult(True, output=output)
        return ToolResult(False, output=output, error=(proc.stderr.strip() or f"exit_code={proc.returncode}"))


PythonTool = PythonExecTool


__all__ = ["PythonExecTool", "PythonTool"]
