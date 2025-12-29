"""
Codex CLI LLM Adapter.

Codex CLI is an optional provider specialized for code-related tasks.
It requires OAuth authentication and may not always be available.

Environment Variables:
    CODEX_EXE_PATH: Path to codex executable (optional, searches PATH)
    CODEX_CLI_PATH: Path to codex executable (optional, searches PATH)
    CODEX_BIN: Codex command name if on PATH (optional)
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .llm_client import (
    LLMClient,
    LLMResponse,
    LLMError,
    LLMAuthError,
    LLMTimeoutError,
    LLMErrorType,
    register_provider,
)

logger = logging.getLogger(__name__)


class CodexCLIAdapter(LLMClient):
    """
    Codex CLI adapter.

    Uses the Codex CLI subprocess for LLM calls.
    Best for code-related tasks but requires OAuth authentication.
    """

    def __init__(self, codex_path: Optional[str] = None):
        self._codex_path = (
            codex_path
            or os.environ.get("CODEX_EXE_PATH")
            or os.environ.get("CODEX_CLI_PATH")
            or os.environ.get("CODEX_BIN")
        )
        self._verified_path: Optional[str] = None
        self._auth_checked = False
        self._is_authenticated = False

    @property
    def provider_name(self) -> str:
        return "codex"

    def _find_codex(self) -> Optional[str]:
        """Find the Codex CLI executable."""
        if self._verified_path:
            return self._verified_path

        # Check explicit path or command override
        if self._codex_path:
            if os.path.exists(self._codex_path):
                self._verified_path = self._codex_path
                return self._verified_path
            resolved = shutil.which(self._codex_path)
            if resolved:
                self._verified_path = resolved
                return self._verified_path

        # Check PATH
        codex_in_path = shutil.which("codex")
        if codex_in_path:
            self._verified_path = codex_in_path
            return self._verified_path

        # Check common Windows locations
        common_paths = [
            os.path.expandvars(r"%APPDATA%\npm\codex.cmd"),
            os.path.expandvars(r"%APPDATA%\npm\node_modules\@openai\codex\vendor\x86_64-pc-windows-msvc\codex\codex.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\codex\codex.exe"),
        ]

        for path in common_paths:
            if os.path.exists(path):
                self._verified_path = path
                return self._verified_path

        return None

    def _check_auth(self) -> bool:
        """Check if Codex CLI is authenticated."""
        if self._auth_checked:
            return self._is_authenticated

        try:
            from agent.llm.codex_cli_client import CodexCliClient

            client = CodexCliClient.from_env()
            self._is_authenticated = client.check_auth()
            self._auth_checked = True
            return self._is_authenticated

        except Exception as e:
            logger.debug(f"Codex auth check failed: {e}")
            self._auth_checked = True
            self._is_authenticated = False
            return False

    def is_available(self) -> bool:
        """Check if Codex CLI is available and authenticated."""
        codex = self._find_codex()
        if not codex:
            return False

        # Only do expensive auth check if codex binary exists
        return self._check_auth()

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 60,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Send a chat message via Codex CLI."""
        codex = self._find_codex()
        if not codex:
            raise LLMError(
                "Codex CLI not found",
                error_type=LLMErrorType.AUTH,
                provider=self.provider_name,
            )

        # Build command
        cmd = [codex, "chat"]

        # Add message with optional system prompt
        full_message = message
        if system_prompt:
            full_message = f"System: {system_prompt}\n\nUser: {message}"

        cmd.extend(["-m", full_message])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )

            # Check for auth errors
            if "not authenticated" in result.stderr.lower():
                self._is_authenticated = False
                raise LLMAuthError(
                    "Codex CLI not authenticated. Run 'codex login' to authenticate.",
                    provider=self.provider_name,
                )

            if result.returncode != 0:
                raise LLMError(
                    f"Codex CLI error: {result.stderr or 'Unknown error'}",
                    error_type=LLMErrorType.TRANSIENT,
                    retryable=True,
                    provider=self.provider_name,
                )

            return LLMResponse(
                content=result.stdout.strip(),
                provider=self.provider_name,
                model="codex-cli",
                usage={},  # Codex CLI doesn't provide usage stats
            )

        except subprocess.TimeoutExpired:
            raise LLMTimeoutError(
                f"Codex CLI timed out after {timeout}s",
                provider=self.provider_name,
            )

        except Exception as e:
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                f"Codex CLI error: {e}",
                error_type=LLMErrorType.TRANSIENT,
                retryable=True,
                provider=self.provider_name,
                original_error=e,
            )

    def chat_json(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a chat message and get a JSON response via Codex CLI."""
        codex = self._find_codex()
        if not codex:
            raise LLMError(
                "Codex CLI not found",
                error_type=LLMErrorType.AUTH,
                provider=self.provider_name,
            )

        # Build JSON request prompt
        json_system = system_prompt or ""
        if schema:
            json_system += f"\n\nYou must respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        else:
            json_system += "\n\nYou must respond with valid JSON only. No other text."

        # Use reason_json if schema provided
        if schema:
            # Write schema to temp file
            schema_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False,
            )
            try:
                json.dump(schema, schema_file)
                schema_file.close()

                cmd = [
                    codex, "reason_json",
                    "-s", schema_file.name,
                    "-m", message,
                ]

                if system_prompt:
                    cmd = [
                        codex, "reason_json",
                        "-s", schema_file.name,
                        "-m", f"{system_prompt}\n\n{message}",
                    ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=os.getcwd(),
                )

            finally:
                try:
                    os.unlink(schema_file.name)
                except Exception:
                    pass

        else:
            # Use regular chat with JSON instruction
            full_message = f"{json_system}\n\n{message}"
            cmd = [codex, "chat", "-m", full_message]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd(),
            )

        # Check for errors
        if "not authenticated" in result.stderr.lower():
            self._is_authenticated = False
            raise LLMAuthError(
                "Codex CLI not authenticated",
                provider=self.provider_name,
            )

        if result.returncode != 0:
            raise LLMError(
                f"Codex CLI error: {result.stderr}",
                error_type=LLMErrorType.TRANSIENT,
                retryable=True,
                provider=self.provider_name,
            )

        # Parse JSON response
        content = result.stdout.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            raise LLMError(
                f"Failed to parse JSON from Codex response: {content[:200]}...",
                error_type=LLMErrorType.INVALID_INPUT,
                provider=self.provider_name,
            )


# Register the adapter
register_provider("codex", CodexCLIAdapter)
