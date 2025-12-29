"""
OpenAI LLM Adapter.

OpenAI is an optional high-quality LLM provider.

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key (optional)
    OPENAI_MODEL: Override default model (optional, default: gpt-4o-mini)
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

DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIAdapter(LLMClient):
    """
    OpenAI API adapter.

    Uses direct HTTP requests to OpenAI's chat completions endpoint.
    """

    API_BASE = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        organization: Optional[str] = None,
    ):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._model = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
        self._organization = organization or os.environ.get("OPENAI_ORGANIZATION")
        self._session = requests.Session()

    @property
    def provider_name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self._api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._organization:
            headers["OpenAI-Organization"] = self._organization
        return headers

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make a request to OpenAI API."""
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
                    "Invalid OpenAI API key",
                    provider=self.provider_name,
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise LLMRateLimitError(
                    "OpenAI rate limit exceeded",
                    provider=self.provider_name,
                    retry_after=int(retry_after) if retry_after else 60,
                )

            if response.status_code >= 500:
                raise LLMError(
                    f"OpenAI server error: {response.status_code}",
                    error_type=LLMErrorType.TRANSIENT,
                    retryable=True,
                    provider=self.provider_name,
                )

            if response.status_code >= 400:
                error_detail = response.json().get("error", {}).get("message", response.text)
                raise LLMError(
                    f"OpenAI request failed: {error_detail}",
                    error_type=LLMErrorType.INVALID_INPUT,
                    retryable=False,
                    provider=self.provider_name,
                )

            return response.json()

        except requests.Timeout:
            raise LLMTimeoutError(
                f"OpenAI request timed out after {timeout}s",
                provider=self.provider_name,
            )

        except requests.ConnectionError as e:
            raise LLMError(
                f"Failed to connect to OpenAI: {e}",
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

        # Use JSON mode
        result = self._make_request(
            messages=messages,
            model=model,
            temperature=0.2,  # Lower temperature for JSON
            max_tokens=4096,
            timeout=timeout,
            response_format={"type": "json_object"},
        )

        # Parse response
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Extract JSON from response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', content)
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


# Register the adapter
register_provider("openai", OpenAIAdapter)
