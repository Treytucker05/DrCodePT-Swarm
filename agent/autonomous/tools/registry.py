from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError

from ..config import AgentConfig, RunContext
from ..models import ToolResult


class ToolArgs(BaseModel):
    pass


ToolFn = Callable[[RunContext, Any], ToolResult]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    args_model: Type[BaseModel]
    fn: ToolFn
    description: str = ""
    dangerous: bool = False
    approval_required: bool = False


class ToolRegistry:
    def __init__(self, agent_cfg: AgentConfig):
        self._agent_cfg = agent_cfg
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def list_tools(self) -> List[ToolSpec]:
        return [self._tools[k] for k in sorted(self._tools.keys())]

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def tool_args_schema(self, name: str) -> Optional[Dict[str, Any]]:
        spec = self._tools.get(name)
        if spec is None:
            return None
        model = spec.args_model
        if hasattr(model, "model_json_schema"):
            return model.model_json_schema()  # type: ignore[attr-defined]
        if hasattr(model, "schema"):
            return model.schema()  # type: ignore[attr-defined]
        return None

    def call(self, name: str, args: Dict[str, Any], ctx: RunContext) -> ToolResult:
        if name not in self._tools:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        spec = self._tools[name]
        try:
            parsed = spec.args_model(**(args or {}))
        except ValidationError as exc:
            return ToolResult(success=False, error=f"Tool args validation failed: {exc}")
        return spec.fn(ctx, parsed)

    def requires_approval(self, name: str) -> bool:
        return False
