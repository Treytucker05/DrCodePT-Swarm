"""
Model Router - Routes LLM calls to the appropriate backend.

Task types and their routing:
- planner_decision: OpenRouter cheap model (fast, cheap)
- chat_response: OpenRouter cheap model
- summarize: OpenRouter cheap model
- codex_task: Codex CLI (code execution, audit)
- long_context_review: Claude (optional, for 100k+ context)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of tasks that can be routed."""
    PLANNER = "planner"           # Choose next action
    CHAT = "chat"                 # General chat
    SUMMARIZE = "summarize"       # Text summarization
    CODEX = "codex"               # Code execution/audit
    LONG_CONTEXT = "long_context" # 100k+ token review


class Backend(str, Enum):
    """Available LLM backends."""
    OPENROUTER = "openrouter"
    CODEX = "codex"
    CLAUDE = "claude"
    LOCAL = "local"  # Future: local models


# Keywords that indicate a task should go to Codex
CODEX_KEYWORDS = {
    "write code", "edit code", "fix bug", "implement", "refactor",
    "add feature", "create file", "modify file", "update code",
    "audit", "security review", "code review", "test",
    "run tests", "execute", "build", "compile",
}

# Keywords that indicate long context review
LONG_CONTEXT_KEYWORDS = {
    "review entire", "analyze codebase", "audit repository",
    "summarize repo", "full codebase",
}


@dataclass
class RoutingResult:
    """Result of routing decision."""
    backend: Backend
    model: Optional[str] = None
    reason: str = ""


@dataclass
class ModelRouter:
    """
    Routes LLM requests to the appropriate backend.

    Priority:
    1. Codex for all tasks (fast model for easy tasks, higher reasoning for hard)
    2. OpenRouter fallback if Codex unavailable
    3. Claude optional fallback for long context
    """

    # Backend availability
    openrouter_available: bool = False
    codex_available: bool = False
    claude_available: bool = False

    # Clients (lazy loaded)
    _openrouter_client: Any = field(default=None, repr=False)
    _codex_fast_client: Any = field(default=None, repr=False)
    _codex_reason_client: Any = field(default=None, repr=False)
    _codex_fast_model: str = ""
    _codex_reason_model: str = ""
    _codex_fast_effort: str = ""
    _codex_reason_effort: str = ""

    def __post_init__(self):
        """Check which backends are available."""
        self._load_codex_preferences()
        self._check_backends()

    def _load_codex_preferences(self) -> None:
        """Load Codex model/effort preferences from environment."""
        self._codex_fast_model = (
            os.getenv("CODEX_MODEL_FAST")
            or os.getenv("CODEX_MODEL")
            or ""
        ).strip()
        self._codex_reason_model = (
            os.getenv("CODEX_MODEL_REASON")
            or os.getenv("CODEX_MODEL")
            or ""
        ).strip()
        self._codex_fast_effort = (
            os.getenv("CODEX_REASONING_EFFORT_FAST")
            or os.getenv("CODEX_REASONING_EFFORT")
            or "low"
        ).strip()
        self._codex_reason_effort = (
            os.getenv("CODEX_REASONING_EFFORT_REASON")
            or os.getenv("CODEX_REASONING_EFFORT")
            or "high"
        ).strip()

    def _check_backends(self) -> None:
        """Check which backends are configured and available."""
        # Check OpenRouter
        if os.getenv("OPENROUTER_API_KEY"):
            self.openrouter_available = True
            logger.debug("OpenRouter backend available")

        # Check Codex CLI
        try:
            from agent.llm.codex_cli_client import CodexCliClient
            client = CodexCliClient.from_env()
            self.codex_available = client.check_auth()
            if self.codex_available:
                logger.debug("Codex CLI backend available")
            else:
                logger.debug("Codex CLI auth check failed")
        except Exception as e:
            logger.debug(f"Codex CLI not available: {e}")

        # Check Claude (Anthropic API)
        if os.getenv("ANTHROPIC_API_KEY"):
            self.claude_available = True
            logger.debug("Claude backend available")

    def route_for_task(self, task_description: str) -> str:
        """
        Determine which backend to use for a task.

        Args:
            task_description: Description of the task

        Returns:
            Backend name as string
        """
        result = self._route(task_description)
        return result.backend.value

    def _route(self, task_description: str) -> RoutingResult:
        """Internal routing logic."""
        task_lower = task_description.lower()

        # Prefer Codex for all tasks if available
        if self.codex_available:
            return RoutingResult(
                backend=Backend.CODEX,
                reason="Codex available (primary)",
            )

        # Claude fallback for long-context if available
        if any(kw in task_lower for kw in LONG_CONTEXT_KEYWORDS) and self.claude_available:
            return RoutingResult(
                backend=Backend.CLAUDE,
                reason="Long context review task",
            )

        # OpenRouter fallback
        if self.openrouter_available:
            return RoutingResult(
                backend=Backend.OPENROUTER,
                reason="Fallback to OpenRouter (Codex unavailable)",
            )

        raise RuntimeError("No LLM backend available")

    def get_llm_for_task(self, task_type: Union[str, TaskType]) -> Any:
        """
        Get the appropriate LLM client for a task type.

        Args:
            task_type: Type of task (planner, chat, codex, etc.)

        Returns:
            LLM client instance
        """
        if isinstance(task_type, str):
            task_type = TaskType(task_type) if task_type in TaskType._value2member_map_ else TaskType.PLANNER

        if task_type == TaskType.CODEX:
            return self._get_codex_client(kind="reason") or self._get_openrouter_client()
        if task_type == TaskType.LONG_CONTEXT:
            return self._get_codex_client(kind="reason") or self._get_claude_client() or self._get_openrouter_client()
        # Planner/chat/summarize -> Codex fast first
        return self._get_codex_client(kind="fast") or self._get_openrouter_client()

    def _get_openrouter_client(self) -> Optional[Any]:
        """Get or create OpenRouter client."""
        if self._openrouter_client:
            return self._openrouter_client

        if not self.openrouter_available:
            return None

        try:
            from agent.llm.openrouter_client import OpenRouterClient
            self._openrouter_client = OpenRouterClient.from_env()
            return self._openrouter_client
        except Exception as e:
            logger.error(f"Failed to create OpenRouter client: {e}")
            return None

    def _get_codex_client(self, *, kind: str = "fast") -> Optional[Any]:
        """Get or create Codex CLI client (fast or reasoning)."""
        if kind == "reason":
            if self._codex_reason_client:
                return self._codex_reason_client
        else:
            if self._codex_fast_client:
                return self._codex_fast_client

        if not self.codex_available:
            return None

        try:
            from agent.llm.codex_cli_client import CodexCliClient

            if kind == "reason":
                client = CodexCliClient.from_env(
                    model_override=self._codex_reason_model,
                    reasoning_effort=self._codex_reason_effort,
                )
                self._codex_reason_client = client
                return client

            client = CodexCliClient.from_env(
                model_override=self._codex_fast_model,
                reasoning_effort=self._codex_fast_effort,
            )
            self._codex_fast_client = client
            return client
        except Exception as e:
            logger.error(f"Failed to create Codex client: {e}")
            return None

    def _get_claude_client(self) -> Optional[Any]:
        """Get or create Claude client (future)."""
        # TODO: Implement Anthropic client
        return None

    def planner_decision(
        self,
        context: str,
        *,
        tools: List[Dict[str, Any]],
        schema_path: Path,
    ) -> Dict[str, Any]:
        """
        Get next action decision from planner.

        Uses OpenRouter (cheap model) for fast planning.
        """
        client = self.get_llm_for_task(TaskType.PLANNER)

        if hasattr(client, "plan_next_action"):
            # OpenRouter has a dedicated method
            schema = json.loads(schema_path.read_text())
            return client.plan_next_action(context, tools=tools, schema=schema)
        else:
            # Codex CLI fallback
            return client.reason_json(context, schema_path=schema_path)

    def chat_response(self, message: str, *, system: Optional[str] = None) -> str:
        """Get chat response using cheap model."""
        client = self.get_llm_for_task(TaskType.CHAT)

        if hasattr(client, "chat"):
            return client.chat(message, system=system) or ""
        elif hasattr(client, "generate_text"):
            return client.generate_text(message, system=system)
        else:
            # Fallback: use JSON method and extract
            result = client.call_codex(message, timeout_seconds=30)
            return result.get("result", str(result))

    def summarize(self, text: str, max_length: int = 500) -> str:
        """Summarize text using cheap model."""
        client = self.get_llm_for_task(TaskType.SUMMARIZE)

        if hasattr(client, "summarize"):
            return client.summarize(text, max_length=max_length)
        else:
            prompt = f"Summarize in {max_length} chars: {text}"
            return self.chat_response(prompt)

    def codex_task(
        self,
        task: str,
        *,
        schema_path: Optional[Path] = None,
        timeout_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Execute a code task using Codex CLI.

        Args:
            task: Task description
            schema_path: Optional schema for structured output
            timeout_seconds: Timeout for execution

        Returns:
            Result dict with output/error
        """
        client = self._get_codex_client()
        if not client:
            return {"error": "Codex CLI not available"}

        if schema_path:
            return client.complete_json(
                task,
                schema_path=schema_path,
                timeout_seconds=timeout_seconds,
            )
        else:
            return client.call_codex(task, timeout_seconds=timeout_seconds)


# Singleton instance
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get singleton model router instance."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


__all__ = [
    "ModelRouter",
    "TaskType",
    "Backend",
    "RoutingResult",
    "get_model_router",
]
