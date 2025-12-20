from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from .base import LLMClient
from .errors import (
    CodexCliAuthError,
    CodexCliExecutionError,
    CodexCliNotFoundError,
    CodexCliOutputError,
)
from contextlib import nullcontext


def _snippet(text: str | None, *, limit: int = 500) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[:limit] + "…"


def _looks_like_auth_error(stdout: str, stderr: str) -> bool:
    combined = f"{stdout}\n{stderr}".lower()
    needles = [
        "not logged in",
        "login required",
        "please login",
        "codex login",
        "authentication",
        "unauthorized",
        "forbidden",
    ]
    return any(n in combined for n in needles)


@dataclass(frozen=True)
class CodexCliClient(LLMClient):
    """
    LLM backend that uses the locally authenticated Codex CLI (ChatGPT/Codex login).

    Invokes (mandatory flags), passing the prompt via STDIN to avoid Windows
    command-line length limits:
      codex --dangerously-bypass-approvals-and-sandbox --search exec \\
        --output-schema <schema.json> \\
        --output-last-message <tmp_output.json>

    Notes:
    - This is used strictly as an inference backend (structured JSON output), not for tool execution.
    - Uses your local Codex CLI login (run `codex login`).
    """

    codex_bin: str = "codex"
    model: str = ""
    timeout_seconds: int = 120

    provider: str = "codex_cli"

    @staticmethod
    def from_env() -> "CodexCliClient":
        return CodexCliClient(
            codex_bin=(os.getenv("CODEX_BIN") or "codex").strip(),
            model=(os.getenv("CODEX_MODEL") or "").strip(),
            timeout_seconds=int((os.getenv("CODEX_TIMEOUT_SECONDS") or "120").strip()),
        )

    def _resolve_bin(self) -> str:
        resolved = shutil.which(self.codex_bin)
        if not resolved:
            raise CodexCliNotFoundError(
                f"Codex CLI not found: {self.codex_bin}. Install Codex CLI and ensure it is on PATH."
            )
        return resolved

    def complete_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        codex = self._resolve_bin()
        schema_path = schema_path.resolve()
        if not schema_path.is_file():
            raise CodexCliExecutionError(f"JSON schema not found: {schema_path}")

        out_path = Path(tempfile.gettempdir()) / f"codex_last_message_{uuid4().hex}.json"

        cmd = [
            codex,
            "--dangerously-bypass-approvals-and-sandbox",
            "--search",
            "--disable",
            "rmcp_client",
            "--disable",
            "shell_tool",
            "exec",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(out_path),
        ]
        if self.model:
            cmd.extend(["--model", self.model])

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        try:
            try:
                from agent.ui.spinner import Spinner

                spinner_ctx = Spinner("CODEX") if sys.stdout.isatty() else nullcontext()
            except Exception:
                spinner_ctx = nullcontext()

            with spinner_ctx:
                proc = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    env=env,
                    timeout=timeout_seconds or self.timeout_seconds,
                )
        except FileNotFoundError as exc:
            raise CodexCliNotFoundError(
                f"Codex CLI not found: {self.codex_bin}. Install Codex CLI and ensure it is on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise CodexCliExecutionError(f"codex exec timed out after {timeout_seconds or self.timeout_seconds}s") from exc

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        if proc.returncode != 0:
            if _looks_like_auth_error(stdout, stderr):
                raise CodexCliAuthError(
                    "Codex CLI is not authenticated. Run `codex login` and try again.\n"
                    f"stdout: {_snippet(stdout)}\n"
                    f"stderr: {_snippet(stderr)}"
                )
            raise CodexCliExecutionError(
                f"codex exec failed (exit={proc.returncode}).\n"
                f"stdout: {_snippet(stdout)}\n"
                f"stderr: {_snippet(stderr)}"
            )

        if not out_path.is_file():
            raise CodexCliOutputError(
                "codex exec did not produce --output-last-message file.\n"
                f"stdout: {_snippet(stdout)}\n"
                f"stderr: {_snippet(stderr)}"
            )

        try:
            raw = out_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise CodexCliOutputError(
                "Failed to read codex --output-last-message file.\n"
                f"path: {out_path}\n"
                f"stdout: {_snippet(stdout)}\n"
                f"stderr: {_snippet(stderr)}"
            ) from exc
        finally:
            try:
                out_path.unlink(missing_ok=True)  # type: ignore[call-arg]
            except Exception:
                pass

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CodexCliOutputError(
                "codex exec returned invalid JSON in --output-last-message.\n"
                f"stdout: {_snippet(stdout)}\n"
                f"stderr: {_snippet(stderr)}\n"
                f"output_file_preview: {_snippet(raw)}"
            ) from exc
