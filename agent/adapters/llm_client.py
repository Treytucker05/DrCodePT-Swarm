"""
Provider-agnostic LLM Client.

This is the base module that defines the interface and factory for LLM clients.
It handles provider selection, failover, retries, and error classification.
"""
from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

logger = logging.getLogger(__name__)


# =============================================================================
# Error Types
# =============================================================================

class LLMErrorType(str, Enum):
    """Classification of LLM errors for handling decisions."""
    AUTH = "auth"           # Authentication failed - try another provider
    RATE_LIMIT = "rate_limit"  # Rate limited - retry with backoff
    TIMEOUT = "timeout"     # Request timed out - retry
    TRANSIENT = "transient" # Temporary error - retry
    FATAL = "fatal"         # Unrecoverable - surface to user
    INVALID_INPUT = "invalid_input"  # Bad request - don't retry


class LLMError(Exception):
    """Base exception for LLM errors."""

    def __init__(
        self,
        message: str,
        error_type: LLMErrorType = LLMErrorType.FATAL,
        retryable: bool = False,
        provider: str = "unknown",
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.retryable = retryable
        self.provider = provider
        self.original_error = original_error

    def __str__(self) -> str:
        return f"[{self.provider}] {self.error_type.value}: {self.message}"


class LLMAuthError(LLMError):
    """Authentication failed."""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(
            message,
            error_type=LLMErrorType.AUTH,
            retryable=False,
            provider=provider,
        )


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(self, message: str, provider: str = "unknown", retry_after: Optional[int] = None):
        super().__init__(
            message,
            error_type=LLMErrorType.RATE_LIMIT,
            retryable=True,
            provider=provider,
        )
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """Request timed out."""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(
            message,
            error_type=LLMErrorType.TIMEOUT,
            retryable=True,
            provider=provider,
        )


# =============================================================================
# Response Type
# =============================================================================

@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    provider: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

    @property
    def input_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)

    @property
    def output_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", self.input_tokens + self.output_tokens)


# =============================================================================
# Base Client Interface
# =============================================================================

class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    All providers must implement this interface.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'openrouter', 'openai', 'codex')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is configured and available."""
        pass

    @abstractmethod
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> LLMResponse:
        """
        Send a chat message and get a response.

        Args:
            message: The user message
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds

        Returns:
            LLMResponse with the model's response

        Raises:
            LLMError: On any failure
        """
        pass

    @abstractmethod
    def chat_json(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """
        Send a chat message and get a JSON response.

        Args:
            message: The user message
            system_prompt: Optional system prompt
            schema: Optional JSON schema for validation
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON response

        Raises:
            LLMError: On any failure
        """
        pass

    def complete_with_retry(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs,
    ) -> LLMResponse:
        """
        Chat with automatic retry on transient failures.

        Uses exponential backoff for retries.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return self.chat(message, system_prompt=system_prompt, **kwargs)
            except LLMError as e:
                last_error = e
                if not e.retryable:
                    raise

                delay = base_delay * (2 ** attempt)
                if hasattr(e, 'retry_after') and e.retry_after:
                    delay = max(delay, e.retry_after)

                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

        raise last_error or LLMError("Max retries exceeded", error_type=LLMErrorType.FATAL)


# =============================================================================
# Multi-Provider Client with Failover
# =============================================================================

class MultiProviderClient(LLMClient):
    """
    LLM client that tries multiple providers in order.

    If one provider fails with an auth error, it falls back to the next.
    """

    def __init__(self, providers: List[LLMClient]):
        self._providers = providers
        self._current_index = 0

    @property
    def provider_name(self) -> str:
        return "multi"

    def is_available(self) -> bool:
        return any(p.is_available() for p in self._providers)

    @property
    def current_provider(self) -> Optional[LLMClient]:
        """Get the currently active provider."""
        available = [p for p in self._providers if p.is_available()]
        if not available:
            return None
        return available[min(self._current_index, len(available) - 1)]

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
    ) -> LLMResponse:
        """Try each provider in order until one succeeds."""
        available = [p for p in self._providers if p.is_available()]

        if not available:
            raise LLMError(
                "No LLM providers available. Please configure at least one of: "
                "OPENROUTER_API_KEY, OPENAI_API_KEY, or install Codex CLI.",
                error_type=LLMErrorType.AUTH,
            )

        errors = []
        for i, provider in enumerate(available):
            try:
                logger.debug(f"Trying provider: {provider.provider_name}")
                response = provider.chat(
                    message,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
                try:
                    logger.info(
                        f"[LLM] provider={response.provider} model={response.model}"
                    )
                except Exception:
                    logger.info(f"[LLM] provider={provider.provider_name}")
                self._current_index = i  # Remember successful provider
                return response

            except LLMAuthError as e:
                logger.warning(f"Provider {provider.provider_name} auth failed: {e}")
                errors.append(e)
                continue  # Try next provider

            except LLMRateLimitError as e:
                logger.warning(f"Provider {provider.provider_name} rate limited: {e}")
                errors.append(e)
                continue  # Try next provider

            except LLMError as e:
                logger.error(f"Provider {provider.provider_name} error: {e}")
                errors.append(e)
                if not e.retryable:
                    raise  # Fatal error, don't try other providers

        # All providers failed
        error_summary = "; ".join(str(e) for e in errors)
        raise LLMError(
            f"All LLM providers failed: {error_summary}",
            error_type=LLMErrorType.FATAL,
        )

    def chat_json(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """Try each provider in order until one succeeds."""
        available = [p for p in self._providers if p.is_available()]

        if not available:
            raise LLMError(
                "No LLM providers available",
                error_type=LLMErrorType.AUTH,
            )

        errors = []
        for provider in available:
            try:
                result = provider.chat_json(
                    message,
                    system_prompt=system_prompt,
                    schema=schema,
                    timeout=timeout,
                )
                model = getattr(provider, "model", "unknown")
                logger.info(f"[LLM] provider={provider.provider_name} model={model}")
                return result
            except LLMAuthError as e:
                errors.append(e)
                continue
            except LLMError as e:
                errors.append(e)
                if not e.retryable:
                    raise

        error_summary = "; ".join(str(e) for e in errors)
        raise LLMError(
            f"All LLM providers failed: {error_summary}",
            error_type=LLMErrorType.FATAL,
        )


# =============================================================================
# Factory Functions
# =============================================================================

# Provider registry
_PROVIDERS: Dict[str, Type[LLMClient]] = {}


def register_provider(name: str, provider_class: Type[LLMClient]) -> None:
    """Register a provider class."""
    _PROVIDERS[name] = provider_class


def get_available_providers() -> List[str]:
    """Get list of configured provider names."""
    # Import providers to register them first
    try:
        from . import openrouter_adapter, openai_adapter, codex_adapter
    except ImportError:
        pass

    available = []
    for name, cls in _PROVIDERS.items():
        try:
            instance = cls()
            if instance.is_available():
                available.append(name)
        except Exception:
            pass
    return available


def get_llm_client(
    preferred_provider: Optional[str] = None,
    fallback: bool = True,
) -> LLMClient:
    """
    Get an LLM client with optional failover.

    Args:
        preferred_provider: Name of preferred provider (openrouter, openai, codex)
        fallback: If True, create multi-provider client with failover

    Returns:
        LLMClient instance

    Raises:
        LLMError: If no providers are available
    """
    # Import providers to register them
    from . import openrouter_adapter, openai_adapter, codex_adapter

    if preferred_provider and preferred_provider in _PROVIDERS:
        provider = _PROVIDERS[preferred_provider]()
        if provider.is_available():
            if fallback:
                # Create multi-provider with preferred first
                others = [
                    cls() for name, cls in _PROVIDERS.items()
                    if name != preferred_provider
                ]
                all_providers = [provider] + [p for p in others if p.is_available()]
                return MultiProviderClient(all_providers)
            return provider

    # Create multi-provider with default order
    # Priority: Codex (primary) -> OpenRouter (fallback) -> OpenAI (optional)
    priority = ["codex", "openrouter", "openai"]
    providers = []

    for name in priority:
        if name in _PROVIDERS:
            try:
                instance = _PROVIDERS[name]()
                if instance.is_available():
                    providers.append(instance)
            except Exception as e:
                logger.debug(f"Provider {name} not available: {e}")

    if not providers:
        raise LLMError(
            "No LLM providers available. Please set at least one of:\n"
            "  - OPENROUTER_API_KEY (recommended)\n"
            "  - OPENAI_API_KEY\n"
            "  - Install and authenticate Codex CLI",
            error_type=LLMErrorType.AUTH,
        )

    if len(providers) == 1:
        return providers[0]

    return MultiProviderClient(providers)


def get_provider(name: str) -> Optional[LLMClient]:
    """Get a specific provider by name, or None if not available."""
    if name not in _PROVIDERS:
        return None
    try:
        instance = _PROVIDERS[name]()
        return instance if instance.is_available() else None
    except Exception:
        return None
