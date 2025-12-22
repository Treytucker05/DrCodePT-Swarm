from __future__ import annotations

import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel, ValidationError

from ..config import AgentConfig, RunContext
from ..exceptions import InteractionRequiredError, ToolExecutionError
from ..models import ToolResult

logger = logging.getLogger(__name__)

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
    def __init__(self, agent_cfg: Optional[AgentConfig] = None, allow_interactive_tools: bool = True):
        self._agent_cfg = agent_cfg
        self.allow_interactive_tools = allow_interactive_tools
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def list_tools(self) -> List[ToolSpec]:
        return [self._tools[k] for k in sorted(self._tools.keys())]

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def get_tool_spec(self, name: str) -> Optional[ToolSpec]:
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

    def execute(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        run_dir: Optional[Path] = None,
    ) -> ToolResult:
        """Execute a tool, checking if interactive tools are allowed."""
        spec = self.get_tool_spec(tool_name)
        if not spec:
            if tool_name == "human_ask" and not self.allow_interactive_tools:
                logger.warning(
                    "Interactive tool blocked in non-interactive mode: %s",
                    tool_name,
                )
                return ToolResult(
                    success=False,
                    error="interaction_required",
                    metadata={
                        "error_type": "interaction_required",
                        "tool": tool_name,
                        "message": "This tool requires human interaction, which is not allowed in this mode",
                    },
                )
            return ToolResult(success=False, error=f"Tool not found: {tool_name}")
        if spec.dangerous and not self.allow_interactive_tools:
            logger.warning(
                "Interactive tool blocked in non-interactive mode: %s",
                tool_name,
            )
            return ToolResult(
                success=False,
                error="interaction_required",
                metadata={
                    "error_type": "interaction_required",
                    "tool": tool_name,
                    "message": "This tool requires human interaction, which is not allowed in this mode",
                },
            )
        if run_dir is None:
            return ToolResult(success=False, error="run_dir required for execute()")
        run_path = Path(run_dir)
        ctx = RunContext(
            run_id="manual",
            run_dir=run_path,
            workspace_dir=run_path,
            profile=getattr(self._agent_cfg, "profile", None) if self._agent_cfg else None,
            usage=None,
        )
        return self._execute_tool(tool_name, tool_args, ctx)

    def _execute_tool(self, name: str, args: Dict[str, Any], ctx: RunContext) -> ToolResult:
        spec = self._tools.get(name)
        if spec is None:
            return ToolResult(success=False, error=f"Unknown tool: {name}")
        if spec.dangerous and not self.allow_interactive_tools:
            logger.warning(
                "Interactive tool blocked in non-interactive mode: %s",
                name,
            )
            return ToolResult(
                success=False,
                error="interaction_required",
                metadata={
                    "error_type": "interaction_required",
                    "tool": name,
                    "message": "This tool requires human interaction, which is not allowed in this mode",
                },
            )
        try:
            parsed = spec.args_model(**(args or {}))
        except ValidationError as exc:
            return ToolResult(success=False, error=f"Tool args validation failed: {exc}")
        try:
            allow_human = True
            if self._agent_cfg is not None:
                allow_human = bool(self._agent_cfg.allow_human_ask)
            if name == "human_ask" and not allow_human:
                question = getattr(parsed, "question", None)
                questions = [question] if isinstance(question, str) and question else []
                raise InteractionRequiredError(
                    "Interactive tools are disabled for this run.",
                    questions=questions,
                )
            return spec.fn(ctx, parsed)
        except InteractionRequiredError as exc:
            questions = getattr(exc, "questions", None) or []
            return ToolResult(
                success=False,
                error="interaction_required",
                output={
                    "ok": False,
                    "status": "interaction_required",
                    "questions": questions,
                },
                metadata={
                    "interaction_required": True,
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                },
            )
        except Exception as exc:
            err = ToolExecutionError(
                f"Tool execution failed: {name}",
                context={"tool_name": name},
                original_exception=exc,
            )
            return ToolResult(
                success=False,
                error=str(err),
                metadata={
                    "error_type": err.__class__.__name__,
                    "tool_name": name,
                    "message": str(err),
                },
            )

    def call(self, name: str, args: Dict[str, Any], ctx: RunContext) -> ToolResult:
        return self._execute_tool(name, args, ctx)

    def requires_approval(self, name: str) -> bool:
        return False

