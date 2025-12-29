"""
Unified tool types for the agent system.

These types provide a consistent interface for both local tools and MCP tools.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel


@dataclass(frozen=True)
class ToolSpec:
    """
    Specification for a tool available to the agent.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description for the planner
        input_schema: JSON Schema for the tool's input parameters
        source: Where the tool comes from ("local", "mcp", "codex")
        dangerous: Whether this tool requires special approval
        namespace: Optional namespace prefix (e.g., "google-calendar")
    """
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    source: str = "local"
    dangerous: bool = False
    namespace: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Full namespaced name (e.g., 'google-calendar.list_events')."""
        if self.namespace:
            return f"{self.namespace}.{self.name}"
        return self.name

    def to_planner_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for the planner/LLM."""
        return {
            "name": self.full_name,
            "description": self.description,
            "input_schema": self.input_schema,
            "dangerous": self.dangerous,
            "source": self.source,
        }


@dataclass
class ToolResult:
    """
    Result from executing a tool.

    Attributes:
        ok: Whether the tool executed successfully
        data: The tool's output data (structured)
        error: Error message if ok=False
        artifacts: File paths or other artifacts produced
        raw: Raw output (for debugging)
        metadata: Additional metadata about the execution
        retryable: Whether this error can be retried
    """
    ok: bool
    data: Any = None
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    raw: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retryable: bool = False

    @classmethod
    def success(cls, data: Any = None, **kwargs) -> "ToolResult":
        """Create a successful result."""
        return cls(ok=True, data=data, **kwargs)

    @classmethod
    def failure(cls, error: str, retryable: bool = False, **kwargs) -> "ToolResult":
        """Create a failed result."""
        return cls(ok=False, error=error, retryable=retryable, **kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error,
            "artifacts": self.artifacts,
            "raw": self.raw,
            "metadata": self.metadata,
            "retryable": self.retryable,
        }


# Type alias for tool execution functions
ToolFunction = Callable[[Any, Any], ToolResult]


@dataclass
class LocalToolSpec:
    """
    Specification for a locally-implemented tool.

    This wraps a Pydantic args model and execution function.
    """
    name: str
    args_model: Type[BaseModel]
    fn: ToolFunction
    description: str = ""
    dangerous: bool = False
    approval_required: bool = False

    def to_tool_spec(self) -> ToolSpec:
        """Convert to unified ToolSpec."""
        # Get JSON schema from Pydantic model
        if hasattr(self.args_model, "model_json_schema"):
            schema = self.args_model.model_json_schema()
        elif hasattr(self.args_model, "schema"):
            schema = self.args_model.schema()
        else:
            schema = {}

        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema=schema,
            source="local",
            dangerous=self.dangerous,
        )


@dataclass
class McpToolSpec:
    """
    Specification for an MCP-provided tool.
    """
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str

    def to_tool_spec(self) -> ToolSpec:
        """Convert to unified ToolSpec."""
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            source="mcp",
            namespace=self.server_name,
        )


def convert_legacy_result(legacy_result) -> ToolResult:
    """
    Convert a legacy ToolResult to the new unified format.

    The old format uses: success, output, error, evidence, metadata, retryable
    The new format uses: ok, data, error, artifacts, raw, metadata, retryable
    """
    if isinstance(legacy_result, ToolResult):
        return legacy_result

    # Handle the old ToolResult from agent.tools.base
    return ToolResult(
        ok=getattr(legacy_result, "success", False),
        data=getattr(legacy_result, "output", None),
        error=getattr(legacy_result, "error", None),
        artifacts=list(getattr(legacy_result, "evidence", {}).keys()),
        metadata=getattr(legacy_result, "metadata", {}),
        retryable=getattr(legacy_result, "retryable", False),
    )


__all__ = [
    "ToolSpec",
    "ToolResult",
    "ToolFunction",
    "LocalToolSpec",
    "McpToolSpec",
    "convert_legacy_result",
]
