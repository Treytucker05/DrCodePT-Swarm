from __future__ import annotations

"""PowerShell runner tool."""

import subprocess
from typing import Any, Dict

from .base import ToolAdapter, ToolResult


class ShellTool(ToolAdapter):
    tool_name = "shell"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        command = getattr(task, "command", None) or inputs.get("command")
        if not command:
            return ToolResult(False, error="No command provided for shell task")

        try:
            proc = subprocess.run(
                ["powershell", "-Command", command],
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
