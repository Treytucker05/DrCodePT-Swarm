
import logging
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional
from agent.llm.base import LLMClient
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ServerClient(LLMClient):
    """
    LLM Client that talks to the persistent local server.
    """
    base_url: str = "http://127.0.0.1:8000"
    timeout_seconds: int = 120
    
    def complete_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        return self._post(
            "complete_json",
            prompt,
            schema_path=schema_path,
            timeout=timeout_seconds,
            agent="Executor"
        )

    def reason_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        return self._post(
            "complete_json", 
            prompt,
            schema_path=schema_path,
            timeout=timeout_seconds,
            agent="Reasoning"
        )

    def chat(self, prompt: str, timeout_seconds: int = 30) -> Optional[str]:
        """Call the /chat endpoint for raw text response."""
        resp = self._post_raw(
            "chat",
            prompt,
            timeout=timeout_seconds
        )
        return resp.get("result")
        
    def _post_raw(
        self,
        endpoint: str,
        prompt: str,
        timeout: Optional[int] = None,
        agent: str = "Main"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        payload = {
            "prompt": prompt,
            "timeout": timeout or self.timeout_seconds,
            "agent": agent
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=(timeout or self.timeout_seconds) + 5)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                return data # Caller handles errors
            return data
        except requests.RequestException as e:
            logger.error(f"LLM Server Error: {e}")
            return {"error": "connection_failed", "detail": str(e)}
        
    def _post(
        self,
        endpoint: str,
        prompt: str,
        schema_path: Path,
        timeout: Optional[int] = None,
        agent: str = "Main"
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        payload = {
            "prompt": prompt,
            "schema_path": str(schema_path),
            "timeout": timeout or self.timeout_seconds,
            "agent": agent
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=(timeout or self.timeout_seconds) + 5)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                error = data["error"]
                detail = data.get("detail", "")
                if error == "auth_error":
                    # Import dynamically to avoid circular imports if necessary
                    from agent.llm.codex_cli_client import CodexCliAuthError
                    raise CodexCliAuthError(f"Authentication failed: {detail}")
                elif error == "timeout":
                    from agent.autonomous.exceptions import LLMError
                    raise LLMError(f"LLM Timed out: {detail}")
                else:
                    from agent.autonomous.exceptions import LLMError
                    raise LLMError(f"LLM Server Error: {error} - {detail}")
            return data
        except requests.RequestException as e:
            logger.error(f"LLM Server Error: {e}")
            from agent.autonomous.exceptions import LLMError
            if hasattr(e, 'response') and e.response is not None:
                raise LLMError(f"Server communication failed: {e.response.text}")
            raise LLMError(f"Connection error: {e}")

    @staticmethod
    def from_env(**kwargs) -> "ServerClient":
        return ServerClient()
