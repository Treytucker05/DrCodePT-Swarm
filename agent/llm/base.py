from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol


class LLMClient(Protocol):
    """
    Protocol for LLM clients.

    All LLM backends (OpenRouter, Codex CLI, Claude) should implement this interface.
    """
    provider: str

    def complete_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Return a JSON object conforming to the provided JSON Schema.

        Used for structured output like action decisions.
        """
        ...

    def reason_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Return a JSON object conforming to the provided JSON Schema using
        reasoning-only mode (no tool execution).

        Used for planning and decision-making.
        """
        ...

    def generate_text(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
    ) -> str:
        """
        Generate unstructured text response.

        Used for chat, summarization, explanations.
        """
        ...

    def generate_json(
        self,
        prompt: str,
        *,
        schema: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response.

        Args:
            prompt: The user prompt
            schema: Optional JSON Schema to validate against
            system: Optional system message

        Returns:
            Parsed JSON dict
        """
        ...


# Type alias for any LLM client
LLMClientType = LLMClient


def get_default_llm() -> LLMClient:
    """
    Get the default LLM client based on environment.

    Priority:
    1. OpenRouter (if OPENROUTER_API_KEY set)
    2. Codex CLI (if available)
    """
    import os

    if os.getenv("OPENROUTER_API_KEY"):
        from agent.llm.openrouter_client import OpenRouterClient
        return OpenRouterClient.from_env()

    from agent.llm.codex_cli_client import CodexCliClient
    return CodexCliClient.from_env()


__all__ = ["LLMClient", "LLMClientType", "get_default_llm"]
