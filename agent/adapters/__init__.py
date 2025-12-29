"""
LLM Adapters - Provider-agnostic LLM client system.

This module provides a unified interface for LLM calls with multiple backend providers.
The system gracefully falls back between providers when one fails.

Priority order (configurable):
1. OpenRouter (default, cheap, reliable)
2. OpenAI (optional, high-quality)
3. CodexCLI (optional, specialized for code)

Usage:
    from agent.adapters import get_llm_client

    client = get_llm_client()
    response = client.chat("Hello, world!")
"""

from .llm_client import (
    LLMClient,
    LLMResponse,
    LLMError,
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError,
    get_llm_client,
    get_available_providers,
)

__all__ = [
    "LLMClient",
    "LLMResponse",
    "LLMError",
    "LLMAuthError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "get_llm_client",
    "get_available_providers",
]
