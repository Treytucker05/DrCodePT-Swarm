from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class AgentException(Exception):
    def __init__(self, message: str = "", *, cause: Optional[BaseException] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.cause = cause
        self.data = data or {}


class ToolExecutionError(AgentException):
    def __init__(self, tool_name: str, message: str = "", *, cause: Optional[BaseException] = None):
        detail = message or f"Tool execution failed: {tool_name}"
        super().__init__(detail, cause=cause, data={"tool_name": tool_name})
        self.tool_name = tool_name


class PlanningError(AgentException):
    pass


class MemoryError(AgentException):
    pass


class LLMError(AgentException):
    pass


class ConfigurationError(AgentException):
    pass


class DependencyError(AgentException):
    pass


class ReflectionError(AgentException):
    pass


class InteractionRequiredError(AgentException):
    def __init__(
        self,
        message: str = "Interaction required",
        *,
        questions: Optional[Iterable[str]] = None,
        cause: Optional[BaseException] = None,
    ):
        qs = [q for q in (questions or []) if isinstance(q, str) and q]
        super().__init__(message, cause=cause, data={"questions": qs})
        self.questions = qs
