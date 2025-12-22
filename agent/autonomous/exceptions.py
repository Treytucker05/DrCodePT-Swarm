"""Custom exceptions for the autonomous agent framework.

This module defines a hierarchy of exceptions that provide semantic meaning
to different failure modes. Instead of catching broad Exception types,
code should catch specific exception types that indicate what went wrong.
"""

from typing import Optional, Dict, Any


class AgentException(Exception):
    """Base exception for all agent-related errors."""

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.original_exception = original_exception

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class ToolExecutionError(AgentException):
    """Raised when a tool fails to execute."""
    pass


class PlanningError(AgentException):
    """Raised when planning fails."""
    pass


class MemoryError(AgentException):
    """Raised when memory operations fail."""
    pass


class LLMError(AgentException):
    """Raised when LLM calls fail."""
    pass


class ConfigurationError(AgentException):
    """Raised when configuration is invalid."""
    pass


class DependencyError(AgentException):
    """Raised when optional dependencies are missing."""
    pass


class ReflectionError(AgentException):
    """Raised when reflection fails."""
    pass


class InteractionRequiredError(AgentException):
    """Raised when human interaction is required."""

    def __init__(
        self,
        message: str,
        questions: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.questions = questions or []
