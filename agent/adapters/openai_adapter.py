"""
OpenAI LLM Adapter.

OpenAI is an optional high-quality LLM provider.

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key (optional)
    OPENAI_MODEL: Override default model (optional, default: gpt-4o-mini)
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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

# Models that support vision
VISION_CAPABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-vision-preview",
    "gpt-4-turbo",
]


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

    def _encode_image(self, image_input: Union[str, Path, Any]) -> str:
        """Encode an image to base64 string.
        
        Args:
            image_input: Can be a file path (str/Path) or PIL Image object
            
        Returns:
            Base64 encoded image string with data URI prefix
        """
        try:
            from PIL import Image
        except ImportError:
            raise LLMError(
                "PIL/Pillow is required for image processing. Install with: pip install Pillow",
                error_type=LLMErrorType.INVALID_INPUT,
                provider=self.provider_name,
            )
        
        # Handle PIL Image object
        if hasattr(image_input, 'save'):
            import io
            buffer = io.BytesIO()
            image_input.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
        # Handle file path
        elif isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.exists():
                raise LLMError(
                    f"Image file not found: {path}",
                    error_type=LLMErrorType.INVALID_INPUT,
                    provider=self.provider_name,
                )
            with open(path, 'rb') as f:
                image_bytes = f.read()
        else:
            raise LLMError(
                f"Unsupported image input type: {type(image_input)}",
                error_type=LLMErrorType.INVALID_INPUT,
                provider=self.provider_name,
            )
        
        # Encode to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:image/png;base64,{base64_image}"

    def chat_with_image(
        self,
        prompt: str,
        image_input: Union[str, Path, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,  # Lower temperature for vision tasks
        max_tokens: int = 2048,
        timeout: int = 90,  # Vision tasks take longer
        model: Optional[str] = None,
    ) -> str:
        """Send a chat message with an image and get a response.
        
        Args:
            prompt: Text prompt describing what to do with the image
            image_input: Image file path (str/Path) or PIL Image object
            system_prompt: Optional system prompt
            temperature: Sampling temperature (default 0.2 for accuracy)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            model: Model to use (defaults to vision-capable model if available)
            
        Returns:
            Response text from the model
        """
        # Select vision-capable model if not specified
        use_model = model or self._model
        if not any(vm in use_model for vm in VISION_CAPABLE_MODELS):
            # Default to gpt-4o if available, otherwise gpt-4o-mini
            use_model = "gpt-4o" if "gpt-4o" in str(self._model) else "gpt-4o-mini"
            logger.info(f"Using vision-capable model: {use_model}")
        
        # Encode image
        image_data_uri = self._encode_image(image_input)
        
        # Build messages with image
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Format message with image (OpenAI format)
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_uri
                    }
                }
            ]
        })
        
        result = self._make_request(
            messages=messages,
            model=use_model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        
        # Parse response
        choice = result.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        return content


# Register the adapter
register_provider("openai", OpenAIAdapter)
