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

# Default models by use case
DEFAULT_MODELS = {
    "chat": "x-ai/grok-4.1-fast",
    "reasoning": "x-ai/grok-4.1-fast",
    "code": "x-ai/grok-4.1-fast",
    "fast": "x-ai/grok-4.1-fast",
}

# Models that support JSON mode
JSON_CAPABLE_MODELS = [
    "x-ai/grok-4.1-fast",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-pro-1.5",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.1-8b-instruct:free",
]

# Models that support vision
VISION_CAPABLE_MODELS = [
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4-vision-preview",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    "google/gemini-pro-vision",
    "google/gemini-pro-1.5",
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
            # Try to find a vision-capable model
            vision_models = [vm for vm in VISION_CAPABLE_MODELS if vm.startswith("openai/") or vm.startswith("anthropic/")]
            if vision_models:
                use_model = vision_models[0]  # Prefer OpenAI or Anthropic
                logger.info(f"Using vision-capable model: {use_model}")
        
        # Encode image
        image_data_uri = self._encode_image(image_input)
        
        # Build messages with image
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Format message with image (OpenAI/OpenRouter format)
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
register_provider("openrouter", OpenRouterAdapter)
