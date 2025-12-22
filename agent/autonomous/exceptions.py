from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class AgentException(Exception):
    """Base exception for agent failures.

    Attributes:
        message: Human-readable error message.
        context: Optional contextual metadata.
        original_exception: The underlying exception, if any.

    Example:
        >>> raise AgentException("failed", context={"step": "plan"}, original_exception=RuntimeError("boom"))
    """

    def __init__(
        self,
        message: str = "",
        *,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[BaseException] = None,
        data: Optional[Dict[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ):
        super().__init__(message)
        self.context = context or {}
        self.original_exception = original_exception or cause
        self.data = data or {}
        self.cause = cause or original_exception


class ToolExecutionError(AgentException):
    """Raised when a tool call fails.

    Example:
        >>> raise ToolExecutionError("file_read", "permission denied")
    """

    def __init__(
        self,
        tool_name: str,
        message: str = "",
        *,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[BaseException] = None,
        cause: Optional[BaseException] = None,
    ):
        detail = message or f"Tool execution failed: {tool_name}"
        payload = {"tool_name": tool_name}
        if context:
            payload.update(context)
        super().__init__(
            detail,
            context=context,
            original_exception=original_exception,
            cause=cause,
            data=payload,
        )
        self.tool_name = tool_name


class PlanningError(AgentException):
    """Raised when planning fails.

    Example:
        >>> raise PlanningError("no plan could be generated")
    """


class MemoryError(AgentException):
    """Raised when memory storage/retrieval fails.

    Example:
        >>> raise MemoryError("memory store unavailable")
    """


class LLMError(AgentException):
    """Raised for LLM call failures.

    Example:
        >>> raise LLMError("LLM timed out")
    """


class ConfigurationError(AgentException):
    """Raised for invalid configuration values.

    Example:
        >>> raise ConfigurationError("timeout_seconds must be > 0")
    """


class DependencyError(AgentException):
    """Raised when optional dependencies are missing.

    Example:
        >>> raise DependencyError("faiss not installed")
    """


class ReflectionError(AgentException):
    """Raised when reflection step fails unexpectedly.

    Example:
        >>> raise ReflectionError("reflection JSON invalid")
    """


class InteractionRequiredError(AgentException):
    """Raised when a human interaction is required but disallowed.

    Example:
        >>> raise InteractionRequiredError(questions=["Which file?"])
    """

    def __init__(
        self,
        message: str = "Interaction required",
        *,
        questions: Optional[Iterable[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[BaseException] = None,
        cause: Optional[BaseException] = None,
    ):
        qs = [q for q in (questions or []) if isinstance(q, str) and q]
        payload = {"questions": qs}
        if context:
            payload.update(context)
        super().__init__(
            message,
            context=context,
            original_exception=original_exception,
            cause=cause,
            data=payload,
        )
        self.questions = qs
