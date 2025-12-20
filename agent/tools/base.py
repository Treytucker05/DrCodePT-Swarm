from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retryable: bool = False


class ToolAdapter:
    tool_name: str = ""

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:  # pragma: no cover
        raise NotImplementedError


__all__ = ["ToolAdapter", "ToolResult"]

