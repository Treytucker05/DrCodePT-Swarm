from __future__ import annotations

"""
Shell tool (PowerShell on Windows).

Safe-by-default: this tool is considered unsafe and should be gated by unsafe_mode at the supervisor/registry layer.
"""

import os
import subprocess
from typing import Any, Dict

from .base import ToolAdapter, ToolResult


def _powershell_exe() -> str:
    # Prefer Windows PowerShell for compatibility; fallback to pwsh if available.
    return os.getenv("POWERSHELL_EXE") or "powershell"


class ShellTool(ToolAdapter):
    tool_name = "shell"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        command = inputs.get("command") or getattr(task, "command", None)
        if not command:
            return ToolResult(False, error="No command provided for shell task")

        timeout_seconds = inputs.get("timeout_seconds") or getattr(task, "timeout_seconds", None) or 60
        cwd = inputs.get("cwd") or getattr(task, "cwd", None) or None

        try:
            proc = subprocess.run(
                [
                    _powershell_exe(),
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=int(timeout_seconds),
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, error=f"shell timeout after {timeout_seconds}s", retryable=True)
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))

        output = {"exit_code": proc.returncode, "stdout": proc.stdout or "", "stderr": proc.stderr or ""}
        if proc.returncode == 0:
            return ToolResult(True, output=output)
        return ToolResult(False, output=output, error=(proc.stderr.strip() or f"exit_code={proc.returncode}"))


__all__ = ["ShellTool"]

