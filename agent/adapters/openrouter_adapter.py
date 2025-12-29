"""
OpenRouter LLM Adapter.

OpenRouter is the primary/default LLM provider because:
1. Low cost with free tier available
2. Many model options
3. Simple API key auth (no OAuth)
4. Reliable uptime

Environment Variables:
    OPENROUTER_API_KEY: Your OpenRouter API key (required)
    OPENROUTER_MODEL: Override default model (optional)
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests

from .llm_client import (
    LLMClient,
    LLMResponse,
    LLMError,
    LLMAuthError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMErrorType,
    register_provider,
)

logger = logging.getLogger(__name__)

# Default models by use case
DEFAULT_MODELS = {
    "chat": "qwen/qwen3-coder:free",  # Free, good for general chat
    "reasoning": "anthropic/claude-3.5-sonnet",  # Best reasoning
    "code": "qwen/qwen3-coder:free",  # Free code model
    "fast": "meta-llama/llama-3.1-8b-instruct:free",  # Fast and free
}

# Models that support JSON mode
JSON_CAPABLE_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-pro-1.5",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.1-8b-instruct:free",
]


class OpenRouterAdapter(LLMClient):
    """
    OpenRouter API adapter.

    Uses direct HTTP requests to OpenRouter's OpenAI-compatible endpoint.
    """

    API_BASE = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        site_url: str = "https://github.com/Treytucker05/DrCodePT-Swarm",
        site_name: str = "DrCodePT-Swarm Agent",
    ):
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self._model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODELS["chat"])
        self._site_url = site_url
        self._site_name = site_name
        self._session = requests.Session()

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def is_available(self) -> bool:
        """Check if OpenRouter is configured."""
        return bool(self._api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._site_url,
            "X-Title": self._site_name,
        }

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a request to OpenRouter API."""
        url = f"{self.API_BASE}/chat/completions"

        payload = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            response = self._session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=timeout,
            )

            # Handle error responses
            if response.status_code == 401:
                raise LLMAuthError(
                    "Invalid OpenRouter API key",
                    provider=self.provider_name,
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise LLMRateLimitError(
                    "OpenRouter rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else 60,
                )

            if response.status_code >= 500:
                raise LLMError(
                    f"OpenRouter server error: {response.status_code}",
                    error_type=LLMErrorType.TRANSIENT,
                    retryable=True,
                    provider=self.provider_name,
                )

            if response.status_code >= 400:
                error_detail = response.json().get("error", {}).get("message", response.text)
                raise LLMError(
                    f"OpenRouter request failed: {error_detail}",
                    error_type=LLMErrorType.INVALID_INPUT,
                    retryable=False,
                    provider=self.provider_name,
                )

            return response.json()

        except requests.Timeout:
            raise LLMTimeoutError(
                f"OpenRouter request timed out after {timeout}s",
                provider=self.provider_name,
            )

        except requests.ConnectionError as e:
            raise LLMError(
                f"Failed to connect to OpenRouter: {e}",
                error_type=LLMErrorType.TRANSIENT,
                retryable=True,
                provider=self.provider_name,
                original_error=e,
            )

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Send a chat message and get a response."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": message})

        result = self._make_request(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        # Parse response
        choice = result.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = result.get("usage", {})

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=result.get("model", model or self._model),
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            raw_response=result,
        )

    def chat_json(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a chat message and get a JSON response."""
        # Build system prompt for JSON output
        json_system = system_prompt or ""
        if schema:
            json_system += f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        else:
            json_system += "\n\nYou must respond with valid JSON only. No other text."

        messages = [
            {"role": "system", "content": json_system},
            {"role": "user", "content": message},
        ]

        # Use JSON mode if model supports it
        use_model = model or self._model
        response_format = None
        if any(m in use_model for m in JSON_CAPABLE_MODELS):
            response_format = {"type": "json_object"}

        result = self._make_request(
            messages=messages,
            model=use_model,
            temperature=0.2,  # Lower temperature for JSON
            max_tokens=4096,
            timeout=timeout,
            response_format=response_format,
        )

        # Parse response
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Extract JSON from response
        try:
            # Try direct parse first
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Try to find JSON array
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            raise LLMError(
                f"Failed to parse JSON from response: {content[:200]}...",
                error_type=LLMErrorType.INVALID_INPUT,
                provider=self.provider_name,
            )

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models on OpenRouter."""
        url = f"{self.API_BASE}/models"
        try:
            response = self._session.get(
                url,
                headers=self._get_headers(),
                timeout=30,
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception as e:
            logger.warning(f"Failed to list OpenRouter models: {e}")
            return []


# Register the adapter
register_provider("openrouter", OpenRouterAdapter)
