from __future__ import annotations

"""Base tool interface and shared result structure."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolAdapter:
    """Abstract adapter all tools must implement."""

    tool_name: str = "base"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:  # pragma: no cover - interface
        raise NotImplementedError


class ExecutionError(Exception):
    """Raised when a tool fails irrecoverably."""
