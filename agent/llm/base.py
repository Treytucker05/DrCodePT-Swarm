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
    1. Codex CLI (if available)
    2. OpenRouter (if OPENROUTER_API_KEY set)
    """
    import os

    primary = (os.getenv("TREYS_AGENT_LLM_PRIMARY") or os.getenv("AGENT_LLM_PRIMARY") or "").strip().lower()

    # Honor explicit primary preference
    if primary == "openrouter":
        if os.getenv("OPENROUTER_API_KEY"):
            from agent.llm.openrouter_client import OpenRouterClient
            return OpenRouterClient.from_env()
    
    # Priority: Codex first (no auth check gate - use if client creation succeeds)
    if primary == "codex" or not primary:
        try:
            from agent.llm.codex_cli_client import CodexCliClient
            codex = CodexCliClient.from_env()
            # Client creation succeeded - use it (don't gate on auth check)
            return codex
        except Exception:
            pass
    
    # Try Codex regardless of primary setting (Codex is always preferred)
    try:
        from agent.llm.codex_cli_client import CodexCliClient
        codex = CodexCliClient.from_env()
        # Client creation succeeded - use it (don't gate on auth check)
        return codex
    except Exception:
        pass

    # Only fall back to OpenRouter if Codex client creation failed entirely
    if os.getenv("OPENROUTER_API_KEY"):
        from agent.llm.openrouter_client import OpenRouterClient
        return OpenRouterClient.from_env()

    # Final fallback: try Codex one more time
    from agent.llm.codex_cli_client import CodexCliClient
    return CodexCliClient.from_env()


__all__ = ["LLMClient", "LLMClientType", "get_default_llm"]
