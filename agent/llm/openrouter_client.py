"""
OpenRouter API Client - Cheap planner for routing/planning/chat.

This client is used for:
- Planner decisions (choose next action)
- Chat responses
- Summarization
- Any task that doesn't require Codex's code execution

OpenRouter provides access to multiple models through a single API.
Default to a cheap, fast model for planning decisions.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .base import LLMClient

logger = logging.getLogger(__name__)

# Default OpenRouter models (fast + general purpose).
# Updated Jan 2026 - Moonshot Kimi K2 Thinking primary.
DEFAULT_MODELS = {
    "planner": "moonshotai/kimi-k2-thinking",
    "chat": "moonshotai/kimi-k2-thinking",
    "summarize": "moonshotai/kimi-k2-thinking",
    "reason": "moonshotai/kimi-k2-thinking",
}

# Allow per-task model overrides via environment variables
for key in list(DEFAULT_MODELS.keys()):
    env_key = f"OPENROUTER_MODEL_{key.upper()}"
    env_val = os.getenv(env_key, "").strip()
    if env_val:
        DEFAULT_MODELS[key] = env_val

# Fallback models if primary ones are rate-limited or unavailable
# Free models for fallback
FALLBACK_MODELS = {
    "planner": "qwen/qwen3-coder:free",  # Fast code-focused model
    "chat": "qwen/qwen3-coder:free",     # Code-focused for chat
    "summarize": "qwen/qwen3-coder:free",  # Fast for summaries
    "reason": "deepseek/deepseek-r1-0528:free",  # Advanced reasoning model
}

for key in list(FALLBACK_MODELS.keys()):
    env_key = f"OPENROUTER_FALLBACK_{key.upper()}"
    env_val = os.getenv(env_key, "").strip()
    if env_val:
        FALLBACK_MODELS[key] = env_val

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


@dataclass
class OpenRouterClient(LLMClient):
    """
    OpenAI-compatible client for OpenRouter API.

    Uses cheap models by default for planning/routing decisions.
    """
    api_key: str = ""
    model: str = "moonshotai/kimi-k2-thinking"
    timeout_seconds: int = 60
    max_tokens: int = 4096
    temperature: float = 0.7
    site_url: str = "https://drcodept.local"
    app_name: str = "DrCodePT-Agent"

    provider: str = "openrouter"

    @staticmethod
    def from_env() -> "OpenRouterClient":
        """Create client from environment variables."""
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Get one at https://openrouter.ai/keys"
            )

        # Default to Moonshot Kimi K2 unless explicitly overridden
        default_model = os.getenv("OPENROUTER_MODEL", "").strip()
        if not default_model:
            default_model = "moonshotai/kimi-k2-thinking"  # Use Kimi K2 Thinking as default
        
        return OpenRouterClient(
            api_key=api_key,
            model=default_model,
            timeout_seconds=int(os.getenv("OPENROUTER_TIMEOUT", "60").strip()),
            max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "4096").strip()),
            temperature=float(os.getenv("OPENROUTER_TEMPERATURE", "0.7").strip()),
        )

    def _make_request(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        retry_with_fallback: bool = True,
    ) -> Dict[str, Any]:
        """Make a request to OpenRouter API with automatic fallback."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        requested_model = model or self.model
        
        # Log the actual model being used (for debugging)
        if model and model != self.model:
            logger.debug(f"Using model override: {model} (instance default: {self.model})")

        payload: Dict[str, Any] = {
            "model": requested_model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": self.temperature,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            # Try fallback model on 429 (rate limit), 500 (server error), 404 (model not found)
            if retry_with_fallback and e.response.status_code in (429, 500, 404):
                # Determine which fallback to use based on requested model
                fallback = None
                # Check if requested model matches any default model, use corresponding fallback
                for task_type, default_model in DEFAULT_MODELS.items():
                    if requested_model == default_model:
                        fallback = FALLBACK_MODELS.get(task_type)
                        break
                
                # If no match found, use reason fallback for JSON/reasoning tasks
                if not fallback:
                    fallback = FALLBACK_MODELS.get("reason", FALLBACK_MODELS.get("planner"))

                if fallback and fallback != requested_model:
                    logger.warning(f"Model {requested_model} failed ({e.response.status_code}), trying fallback: {fallback}")
                    payload["model"] = fallback
                    try:
                        response = requests.post(
                            OPENROUTER_API_URL,
                            headers=headers,
                            json=payload,
                            timeout=self.timeout_seconds,
                        )
                        response.raise_for_status()
                        return response.json()
                    except Exception as fallback_error:
                        logger.error(f"Fallback model also failed: {fallback_error}")
            raise

        except requests.exceptions.Timeout:
            logger.error("OpenRouter request timed out")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter request failed: {e}")
            raise

    def generate_text(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate text response."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._make_request(messages, model=model)
        return response["choices"][0]["message"]["content"]

    def generate_json(
        self,
        prompt: str,
        *,
        schema: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response.

        Args:
            prompt: The user prompt
            schema: Optional JSON Schema to validate against
            system: Optional system message
            model: Optional model override

        Returns:
            Parsed JSON dict
        """
        # Build system message that enforces JSON output
        json_system = system or ""
        if schema:
            json_system += f"\n\nRespond with ONLY valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        else:
            json_system += "\n\nRespond with ONLY valid JSON. No markdown, no explanation."

        messages = [
            {"role": "system", "content": json_system.strip()},
            {"role": "user", "content": prompt},
        ]

        response = self._make_request(
            messages,
            model=model,
            response_format={"type": "json_object"},
        )

        content = response["choices"][0]["message"]["content"]

        # Parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw content: {content[:500]}")
            # Try to extract JSON from response
            if "{" in content and "}" in content:
                start = content.index("{")
                end = content.rindex("}") + 1
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
            raise

    def complete_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        LLMClient interface: Generate JSON matching schema.

        This is the standard interface used by the agent.
        Uses the reason model for JSON tasks (structured reasoning).
        """
        # Load schema
        schema = json.loads(schema_path.read_text())

        # Use Kimi K2 Thinking for JSON tasks (strong reasoning)
        # This ensures consistent behavior regardless of env var overrides
        return self.generate_json(
            prompt,
            schema=schema,
            model="moonshotai/kimi-k2-thinking",
        )

    def reason_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        LLMClient interface: Reason and return JSON.

        For OpenRouter, this is the same as complete_json but with
        a more capable model.
        """
        schema = json.loads(schema_path.read_text())

        # Use Kimi K2 Thinking for reasoning tasks (strong reasoning)
        # This ensures consistent behavior regardless of env var overrides
        return self.generate_json(
            prompt,
            schema=schema,
            model="moonshotai/kimi-k2-thinking",
        )

    def plan_next_action(
        self,
        context: str,
        *,
        tools: List[Dict[str, Any]],
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        High-level planner method for agent loop.

        Args:
            context: Current agent context (goal, history, observations)
            tools: Available tool specifications
            schema: Expected output schema

        Returns:
            Parsed decision dict with action, action_input, reasoning
        """
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t.get('description', '')}"
            for t in tools
        )

        system = f"""You are a planning agent. Choose the next action to accomplish the goal.

Available tools:
{tool_descriptions}

Special actions:
- finish: Call when the goal is complete. Include a summary.

Rules:
1. Choose ONE action per response
2. Be specific with action_input
3. If stuck, try a different approach
4. Call finish when done"""

        return self.generate_json(
            context,
            schema=schema,
            system=system,
        )

    def summarize(self, text: str, max_length: int = 500) -> str:
        """Summarize text."""
        return self.generate_text(
            f"Summarize the following in {max_length} characters or less:\n\n{text}",
            system="You are a concise summarizer. Be brief and factual.",
            model=DEFAULT_MODELS.get("summarize", self.model),
        )

    def chat(self, message: str, *, system: Optional[str] = None) -> str:
        """Simple chat response."""
        return self.generate_text(
            message,
            system=system,
            model=DEFAULT_MODELS.get("chat", self.model),
        )


# Convenience function
def get_openrouter_client() -> OpenRouterClient:
    """Get OpenRouter client from environment."""
    return OpenRouterClient.from_env()


__all__ = ["OpenRouterClient", "get_openrouter_client", "DEFAULT_MODELS"]
