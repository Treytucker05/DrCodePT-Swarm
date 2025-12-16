from __future__ import annotations

"""Python script execution tool."""

import subprocess
from typing import Any, Dict

from .base import ToolAdapter, ToolResult


class PythonExecTool(ToolAdapter):
    tool_name = "python"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        script = getattr(task, "script", None) or inputs.get("script")
        if not script:
            return ToolResult(False, error="No script provided for python task")

        try:
            proc = subprocess.run(
                ["python", "-c", script],
                capture_output=True,
                text=True,
                timeout=getattr(task, "timeout_seconds", None),
            )
            return ToolResult(
                success=proc.returncode == 0,
                output={"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode},
                error=None if proc.returncode == 0 else f"Exit code {proc.returncode}",
            )
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))

