from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from .backend import RunConfig, RunResult
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


def _tail(text: str | None, *, limit: int = 2000) -> str:
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    return t[-limit:]


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


def _strip_disable_flags(cmd: list[str]) -> list[str]:
    cleaned: list[str] = []
    skip_next = False
    for token in cmd:
        if skip_next:
            skip_next = False
            continue
        if token == "--disable":
            skip_next = True
            continue
        cleaned.append(token)
    return cleaned


def _looks_like_unknown_feature_flag(stderr: str) -> bool:
    return "unknown feature flag" in (stderr or "").lower()


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
    profile_reason: str = "reason"
    profile_exec: str = "exec"
    workdir: Optional[Path] = None
    log_dir: Optional[Path] = None

    provider: str = "codex_cli"
    # TODO: Future MCP backend can be added here without changing swarm logic.

    @staticmethod
    def from_env(
        *,
        workdir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
    ) -> "CodexCliClient":
        return CodexCliClient(
            codex_bin=(os.getenv("CODEX_BIN") or "codex").strip(),
            model=(os.getenv("CODEX_MODEL") or "").strip(),
            timeout_seconds=int((os.getenv("CODEX_TIMEOUT_SECONDS") or "120").strip()),
            profile_reason=(os.getenv("CODEX_PROFILE_REASON") or "reason").strip(),
            profile_exec=(os.getenv("CODEX_PROFILE_EXEC") or "exec").strip(),
            workdir=workdir,
            log_dir=log_dir,
        )

    def _resolve_bin(self) -> str:
        resolved = shutil.which(self.codex_bin)
        if not resolved:
            raise CodexCliNotFoundError(
                f"Codex CLI not found: {self.codex_bin}. Install Codex CLI and ensure it is on PATH."
            )
        return resolved

    def _resolve_workdir(self) -> Path:
        if self.workdir:
            try:
                return Path(self.workdir).resolve()
            except Exception:
                return Path(self.workdir)
        try:
            return Path(__file__).resolve().parents[2]
        except Exception:
            return Path.cwd()

    def with_context(
        self,
        *,
        workdir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
    ) -> "CodexCliClient":
        return CodexCliClient(
            codex_bin=self.codex_bin,
            model=self.model,
            timeout_seconds=self.timeout_seconds,
            profile_reason=self.profile_reason,
            profile_exec=self.profile_exec,
            workdir=workdir or self.workdir,
            log_dir=log_dir or self.log_dir,
        )

    def run(
        self,
        *,
        prompt: str,
        workdir: Optional[Path],
        run_dir: Optional[Path],
        config: RunConfig,
    ) -> RunResult:
        """
        Backend-style entrypoint for structured runs. This preserves existing
        behavior by delegating to the same JSON-only helpers.
        """
        client = self
        if workdir or run_dir:
            client = self.with_context(workdir=workdir, log_dir=run_dir)
        profile = (config.profile or "reason").strip().lower()
        if profile == "exec":
            data = client.complete_json(
                prompt,
                schema_path=config.schema_path,
                timeout_seconds=config.timeout_seconds,
            )
        else:
            data = client.reason_json(
                prompt,
                schema_path=config.schema_path,
                timeout_seconds=config.timeout_seconds,
            )
        return RunResult(data=data, workdir=client._resolve_workdir())

    def _append_log(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", errors="ignore") as f:
            f.write(content)

    def _run_exec(
        self,
        *,
        prompt: str,
        schema_path: Path,
        timeout_seconds: Optional[int],
        profile: str,
    ) -> Dict[str, Any]:
        codex = self._resolve_bin()
        schema_path = schema_path.resolve()
        if not schema_path.is_file():
            raise CodexCliExecutionError(f"JSON schema not found: {schema_path}")
        workdir = self._resolve_workdir()

        out_path = Path(tempfile.gettempdir()) / f"codex_last_message_{uuid4().hex}.json"

        cmd = [
            codex,
            "--profile",
            profile,
            "--dangerously-bypass-approvals-and-sandbox",
            "-c",
            "mcp_servers.obsidian.enabled=false",
            "-c",
            "mcp_servers.playwright.enabled=false",
            "-c",
            "mcp_servers.desktop.enabled=false",
            "--disable",
            "shell_tool",
            "--disable",
            "web_search_request",
            "--disable",
            "unified_exec",
            "--disable",
            "shell_snapshot",
            "exec",
            "--skip-git-repo-check",
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

        def _run(cmd_args: list[str]) -> subprocess.CompletedProcess[str]:
            try:
                try:
                    from agent.ui.spinner import Spinner

                    spinner_ctx = Spinner("CODEX") if sys.stdout.isatty() else nullcontext()
                except Exception:
                    spinner_ctx = nullcontext()

                with spinner_ctx:
                    return subprocess.run(
                        cmd_args,
                        input=prompt,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="ignore",
                        env=env,
                        cwd=workdir,
                        timeout=timeout_seconds or self.timeout_seconds,
                    )
            except FileNotFoundError as exc:
                raise CodexCliNotFoundError(
                    f"Codex CLI not found: {self.codex_bin}. Install Codex CLI and ensure it is on PATH."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise CodexCliExecutionError(
                    f"codex exec timed out after {timeout_seconds or self.timeout_seconds}s"
                ) from exc

        proc = _run(cmd)
        if proc.returncode != 0 and _looks_like_unknown_feature_flag(proc.stderr or ""):
            cmd = _strip_disable_flags(cmd)
            proc = _run(cmd)

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        if self.log_dir:
            ts = datetime.now(timezone.utc).isoformat()
            header = (
                f"\n[{ts}] profile={profile} exit={proc.returncode} "
                f"cwd={workdir} schema={schema_path} prompt_chars={len(prompt)}\n"
                f"cmd: {' '.join(cmd)}\n"
            )
            try:
                self._append_log(Path(self.log_dir) / "stdout.log", header + stdout + "\n")
                self._append_log(Path(self.log_dir) / "stderr.log", header + stderr + "\n")
            except Exception:
                pass

        if proc.returncode != 0:
            stderr_tail = _tail(stderr)
            stdout_tail = _tail(stdout)
            if _looks_like_auth_error(stdout, stderr):
                exc = CodexCliAuthError(
                    "Codex CLI is not authenticated. Run `codex login` and try again.\n"
                    f"stdout: {_snippet(stdout)}\n"
                    f"stderr: {_snippet(stderr)}"
                )
                try:
                    exc.stdout_tail = stdout_tail
                    exc.stderr_tail = stderr_tail
                    exc.cwd = str(workdir)
                    exc.workdir = str(workdir)
                    exc.cmd = cmd
                except Exception:
                    pass
                raise exc
            exc = CodexCliExecutionError(
                f"codex exec failed (exit={proc.returncode}).\n"
                f"stdout: {_snippet(stdout)}\n"
                f"stderr: {_snippet(stderr)}\n"
                f"stderr_tail: {stderr_tail}"
            )
            try:
                exc.stdout_tail = stdout_tail
                exc.stderr_tail = stderr_tail
                exc.cwd = str(workdir)
                exc.workdir = str(workdir)
                exc.cmd = cmd
            except Exception:
                pass
            raise exc

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

    def complete_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute code using codex exec (execution profile) and return structured JSON.

        WARNING: This uses the execution profile and may run commands.
        Use reason_json() for planning/reflection.
        """
        return self._run_exec(
            prompt=prompt,
            schema_path=schema_path,
            timeout_seconds=timeout_seconds,
            profile=self.profile_exec or "exec",
        )

    def reason_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Use Codex exec non-interactively with the reasoning profile to produce
        structured JSON output. Tools are disabled and the prompt enforces
        JSON-only output.
        """
        schema_path = schema_path.resolve()
        if not schema_path.is_file():
            raise CodexCliExecutionError(f"JSON schema not found: {schema_path}")

        # Load schema to include in prompt
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as exc:
            raise CodexCliExecutionError(f"Failed to load schema: {schema_path}") from exc

        # Build reasoning prompt that enforces JSON-only output
        reasoning_prompt = f"""You are producing JSON for the agent's internal executor. Do NOT execute commands yourself; just output JSON.
It is OK to propose tool actions inside the JSON. Do not refer to an "external runner" in outputs.

Return ONLY valid JSON matching this exact schema:

{json.dumps(schema, indent=2)}

Task:
{prompt}

Output ONLY the JSON object. No explanations, no code, no commands."""
        return self._run_exec(
            prompt=reasoning_prompt,
            schema_path=schema_path,
            timeout_seconds=timeout_seconds,
            profile=self.profile_reason or "reason",
        )

    def complete_reasoning(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Use Codex exec non-interactively for pure reasoning and return structured JSON.

        This method builds a strict JSON-only prompt and runs Codex with tools disabled,
        avoiding interactive TTY requirements. No code is executed by tools.

        Use this for:
        - Planning and decision-making
        - Analyzing state and choosing actions
        - Generating structured responses

        Use complete_json() when you need the raw prompt sent without the reasoning wrapper.
        """
        schema_path = schema_path.resolve()
        if not schema_path.is_file():
            raise CodexCliExecutionError(f"JSON schema not found: {schema_path}")

        # Load the schema to show it to Codex
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as exc:
            raise CodexCliExecutionError(f"Failed to load schema: {exc}") from exc

        # Build a prompt that enforces JSON output
        reasoning_prompt = f"""You are a reasoning agent. Do NOT execute any code or commands.

Your task is to analyze the situation and respond with ONLY valid JSON matching this exact schema:

{json.dumps(schema, indent=2)}

CRITICAL RULES:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanations
2. Do NOT execute any shell commands or code
3. Do NOT use tools or MCP
4. Your entire response must be parseable as JSON

USER REQUEST:
{prompt}

Now respond with ONLY the JSON object:"""
        return self.reason_json(
            reasoning_prompt,
            schema_path=schema_path,
            timeout_seconds=timeout_seconds,
        )

    def complete_json_reasoning(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        return self.reason_json(
            prompt,
            schema_path=schema_path,
            timeout_seconds=timeout_seconds,
        )
