from __future__ import annotations

import json
import logging
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
from time import perf_counter

from .backend import RunConfig, RunResult
from .base import LLMClient
from .errors import (
    CodexCliAuthError,
    CodexCliExecutionError,
    CodexCliNotFoundError,
    CodexCliOutputError,
)
from contextlib import nullcontext


def _is_quiet() -> bool:
    """Check if we should suppress debug output."""
    return os.environ.get("AGENT_QUIET", "0") == "1"


def _debug_print(*args, **kwargs) -> None:
    """Print debug info only if not in quiet mode."""
    if not _is_quiet():
        print(*args, **kwargs)


PROFILE_MAP = {
    "Fingerprint": "reason",
    "Static": "reason",
    "Dynamic": "reason",
    "Research": "reason",
    "Supervisor": "reason",
    "Critic": "reason",
    "Synthesis": "reason",
    "Main": "chat",
    "ReActQuick": "quick",
    "ReActReason": "reason",
    "ReAct": "react",
}

DEFAULT_CODEX_EXE_PATHS = [
    Path(
        r"C:\Users\treyt\AppData\Roaming\npm\node_modules\@openai\codex\vendor\x86_64-pc-windows-msvc\codex\codex.exe"
    ),
    Path(
        r"C:\Users\treyt\AppData\Roaming\npm\node_modules\@openai\codex\vendor\aarch64-pc-windows-msvc\codex\codex.exe"
    ),
]


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


def _profile_for_agent(agent_name: str, default_profile: str) -> str:
    if not agent_name:
        return default_profile
    base = agent_name.split("-", 1)[0].strip()
    return PROFILE_MAP.get(base, default_profile)


_SWARM_REASONING_AGENTS = {
    "Fingerprint",
    "ProblemModel",
    "Static",
    "Dynamic",
    "Research",
    "Supervisor",
    "Critic",
    "Synthesis",
}


def _should_wrap_reasoning(agent_name: str) -> bool:
    if not agent_name:
        return False
    base = agent_name.split("-", 1)[0].strip()
    if base in _SWARM_REASONING_AGENTS:
        return True
    lowered = agent_name.strip().lower()
    return lowered.startswith("swarm") or lowered.startswith("swarm_simple")


def build_codex_command(
    *,
    codex_bin: str,
    agent_name: str,
    profile: str,
    schema_path: Optional[str] = None,
    out_path: Optional[str] = None,
    enable_search: bool = False,
    model: str = "",
    use_profile: bool = False,  # Default to False - profiles force slower models
) -> list[str]:
    """
    Build optimized Codex CLI command.

    Note: By default, we don't use --profile because it forces slower models
    (e.g., gpt-5 instead of gpt-5.2-codex). The default model with low reasoning
    effort is much faster for most tasks.
    """
    cmd = [
        codex_bin,
        "--dangerously-bypass-approvals-and-sandbox",
        "-c",
        "sandbox_mode=danger-full-access",
        "-c",
        "approval_policy=never",
    ]
    # Only add profile if explicitly requested (profiles force slower models)
    if use_profile:
        resolved_profile = _profile_for_agent(agent_name, profile)
        cmd += ["--profile", resolved_profile]
    if model:
        cmd += ["--model", model]
    cmd += [
        "exec",
        "--skip-git-repo-check",
    ]
    if schema_path:
        cmd += ["--output-schema", schema_path]
    if out_path:
        cmd += ["--output-last-message", out_path]
    if enable_search:
        cmd.append("--search")
    cmd.append("-")
    return cmd


def call_codex(
    *,
    prompt: str,
    agent: str = "Main",
    schema_path: Optional[str] = None,
    timeout: int = 120,
    enable_search: bool = False,
) -> Dict[str, Any]:
    """
    Execute Codex CLI with optimized settings.
    """
    env_bin = (os.getenv("CODEX_BIN") or "").strip()
    env_exe = (os.getenv("CODEX_EXE_PATH") or os.getenv("CODEX_CLI_PATH") or "").strip()
    if env_exe and Path(env_exe).is_file():
        codex_bin = env_exe
    else:
        preferred = next((str(p) for p in DEFAULT_CODEX_EXE_PATHS if p.is_file()), None)
        if preferred:
            codex_bin = preferred
        elif env_bin:
            codex_bin = shutil.which(env_bin) or env_bin
        else:
            codex_bin = shutil.which("codex") or "codex"
    env_search = (os.getenv("CODEX_ENABLE_WEB_SEARCH") or "").strip().lower()
    enable_search = enable_search or env_search in {"1", "true", "yes", "y", "on"}
    resolved_profile = _profile_for_agent(agent, "reason")
    cmd = build_codex_command(
        codex_bin=codex_bin,
        agent_name=agent,
        profile="reason",
        schema_path=schema_path,
        enable_search=enable_search,
    )
    cwd = os.getcwd()
    timeout_seconds = timeout
    _debug_print(f"[DEBUG] Codex command: {' '.join(cmd)}")
    _debug_print(f"[DEBUG] Profile: {resolved_profile}")
    _debug_print(f"[DEBUG] Working dir: {cwd}")
    _debug_print(f"[DEBUG] Timeout: {timeout_seconds}s")
    try:
        t0 = perf_counter()
        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            cwd=cwd,
            env=os.environ.copy(),
            encoding="utf-8",
        )
        dur = perf_counter() - t0
        _debug_print(f"[PERF] Codex subprocess duration: {dur:.3f}s")
        _debug_print(f"[DEBUG] Return code: {result.returncode}")
        _debug_print(f"[DEBUG] Stderr: {(result.stderr or '')[:500]}")
        if "429" in (result.stderr or "") or "rate limit" in (result.stderr or "").lower():
            logging.warning("[%s] Hit rate limit - quota exhausted", agent)
            return {
                "error": "rate_limit",
                "message": "ChatGPT Pro quota exhausted",
                "suggestion": "Wait for quota refresh or reduce usage",
            }
        if result.returncode != 0:
            logging.error("[%s] Codex error: %s", agent, result.stderr)
            return {
                "error": "execution_failed",
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        output = (result.stdout or "").strip()
        if schema_path:
            try:
                return json.loads(output)
            except json.JSONDecodeError as exc:
                logging.error("[%s] JSON parse error: %s", agent, exc)
                return {"error": "invalid_json", "raw_output": output}
        return {"result": output}
    except subprocess.TimeoutExpired:
        logging.error("[%s] Timeout after %ss", agent, timeout)
        return {"error": "timeout", "timeout_seconds": timeout}
    except Exception as exc:
        logging.error("[%s] Unexpected error: %s", agent, exc)
        return {"error": "unknown", "exception": str(exc)}


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
    reasoning_effort: str = ""
    timeout_seconds: int = 120
    profile_reason: str = "reason"
    profile_exec: str = "playbook"
    workdir: Optional[Path] = None
    log_dir: Optional[Path] = None

    provider: str = "codex_cli"
    # TODO: Future MCP backend can be added here without changing swarm logic.

    @staticmethod
    def from_env(
        *,
        workdir: Optional[Path] = None,
        log_dir: Optional[Path] = None,
        model_override: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
    ) -> "CodexCliClient":
        return CodexCliClient(
            codex_bin=(
                os.getenv("CODEX_EXE_PATH")
                or os.getenv("CODEX_CLI_PATH")
                or os.getenv("CODEX_BIN")
                or "codex"
            ).strip(),
            model=(
                model_override
                if model_override is not None
                else (os.getenv("CODEX_MODEL") or os.getenv("CODEX_MODEL_FAST") or "")
            ).strip(),
            reasoning_effort=(
                reasoning_effort
                if reasoning_effort is not None
                else (
                    os.getenv("CODEX_REASONING_EFFORT")
                    or os.getenv("CODEX_REASONING_EFFORT_FAST")
                    or ""
                )
            ).strip(),
            timeout_seconds=int((os.getenv("CODEX_TIMEOUT_SECONDS") or "120").strip()),
            profile_reason=(os.getenv("CODEX_PROFILE_REASON") or "reason").strip(),
            profile_exec=(os.getenv("CODEX_PROFILE_EXEC") or "playbook").strip(),
            workdir=workdir,
            log_dir=log_dir,
        )

    def _resolve_bin(self) -> str:
        env_bin = (os.getenv("CODEX_BIN") or "").strip()
        env_exe = (os.getenv("CODEX_EXE_PATH") or os.getenv("CODEX_CLI_PATH") or "").strip()
        if env_exe and Path(env_exe).is_file():
            return env_exe
        for path in DEFAULT_CODEX_EXE_PATHS:
            if path.is_file():
                return str(path)
        if env_bin:
            resolved = shutil.which(env_bin) or env_bin
            if Path(resolved).is_file():
                return resolved
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

    def check_auth(self, timeout_seconds: int = 15) -> bool:
        """Check Codex CLI auth using the same exec invocation as runtime."""
        schema_path = Path(tempfile.gettempdir()) / f"codex_auth_{uuid4().hex}.json"
        schema = {
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"],
            "additionalProperties": False,
        }
        try:
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            self.reason_json(
                "Return a JSON object {\"ok\": true}.",
                schema_path=schema_path,
                timeout_seconds=timeout_seconds,
            )
            return True
        except CodexCliAuthError:
            return False
        except Exception:
            return False
        finally:
            try:
                schema_path.unlink()
            except Exception:
                pass

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

        agent_name = (os.getenv("CODEX_AGENT_NAME") or "").strip()
        search_flag = (os.getenv("CODEX_ENABLE_WEB_SEARCH") or "").strip().lower()
        enable_search = search_flag in {"1", "true", "yes", "y", "on"}
        cmd = build_codex_command(
            codex_bin=codex,
            agent_name=agent_name,
            profile=profile,
            schema_path=str(schema_path),
            out_path=str(out_path),
            enable_search=enable_search,
            model=self.model,
        )
        try:
            exec_index = cmd.index("exec")
        except ValueError:
            exec_index = len(cmd)
        if "mcp.enabled=false" not in cmd:
            cmd[exec_index:exec_index] = ["-c", "mcp.enabled=false", "-c", "features.mcp=false"]
        reasoning_effort = (
            self.reasoning_effort
            or (os.getenv("CODEX_REASONING_EFFORT") or "")
        ).strip()
        if reasoning_effort:
            try:
                exec_index = cmd.index("exec")
            except ValueError:
                exec_index = len(cmd)
            cmd[exec_index:exec_index] = ["-c", f'model_reasoning_effort="{reasoning_effort}"']
        # build_codex_command includes schema/out paths and model if provided

        env = os.environ.copy()
        if not env.get("USERPROFILE"):
            env["USERPROFILE"] = os.path.expanduser("~")
        if not env.get("CODEX_HOME"):
            env["CODEX_HOME"] = os.path.join(env.get("USERPROFILE", ""), ".codex")
        if not env.get("HOME"):
            env["HOME"] = env.get("USERPROFILE", "")
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        def _run(cmd_args: list[str]) -> subprocess.CompletedProcess[str]:
            try:
                try:
                    from agent.ui.spinner import Spinner

                    # Only show spinner if not in quiet mode
                    spinner_ctx = Spinner("CODEX") if sys.stdout.isatty() and not _is_quiet() else nullcontext()
                except Exception:
                    spinner_ctx = nullcontext()

                with spinner_ctx:
                    if os.environ.get("DEBUG"):
                        _debug_print(f"[DEBUG] CODEX_HOME: {env.get('CODEX_HOME')}")
                        _debug_print(f"[DEBUG] Command: {' '.join(cmd_args)}")
                        print(
                            "[DEBUG] Auth file exists: "
                            f"{os.path.exists(os.path.join(env['CODEX_HOME'], 'auth.json'))}"
                        )
                    _debug_print(f"\n[DEBUG] Codex command: {' '.join(cmd_args)}", file=sys.stderr)
                    _debug_print(f"[DEBUG] Working dir: {os.getcwd()}", file=sys.stderr)
                    _debug_print(f"[DEBUG] Env CODEX_HOME: {env.get('CODEX_HOME', 'NOT SET')}", file=sys.stderr)
                    sys.stderr.flush()
                    result = subprocess.run(
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
                    if os.environ.get("DEBUG"):
                        stdout = result.stdout or ""
                        stderr = result.stderr or ""
                        _debug_print(f"\n[DEBUG] Codex returncode: {result.returncode}")
                        _debug_print(f"[DEBUG] Codex stdout length: {len(stdout)}")
                        _debug_print(f"[DEBUG] Codex stderr length: {len(stderr)}")
                        if stdout:
                            _debug_print(f"[DEBUG] Stdout preview: {stdout[:500]}")
                        if stderr:
                            _debug_print(f"[DEBUG] Stderr preview: {stderr[:500]}")
                    return result
            except FileNotFoundError as exc:
                raise CodexCliNotFoundError(
                    f"Codex CLI not found: {self.codex_bin}. Install Codex CLI and ensure it is on PATH."
                ) from exc
            except subprocess.TimeoutExpired as exc:
                if os.environ.get("DEBUG"):
                    def _coerce_text(value: object) -> str:
                        if value is None:
                            return ""
                        if isinstance(value, bytes):
                            return value.decode("utf-8", errors="ignore")
                        return str(value)

                    stdout = _coerce_text(exc.stdout)
                    stderr = _coerce_text(exc.stderr)
                    print(
                        f"\n[DEBUG] TIMEOUT after {timeout_seconds or self.timeout_seconds}s"
                    )
                    _debug_print(f"[DEBUG] Partial stdout length: {len(stdout)}")
                    _debug_print(f"[DEBUG] Partial stderr length: {len(stderr)}")
                    if stdout:
                        _debug_print(f"[DEBUG] Partial stdout: {stdout[:2000]}")
                    if stderr:
                        _debug_print(f"[DEBUG] Partial stderr: {stderr[:2000]}")
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
            profile=self.profile_exec or "playbook",
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
        structured JSON output. The strict JSON-only wrapper is applied only
        for swarm reasoning agents; chat/playbook calls use the raw prompt.
        """
        schema_path = schema_path.resolve()
        if not schema_path.is_file():
            raise CodexCliExecutionError(f"JSON schema not found: {schema_path}")

        agent_name = (os.getenv("CODEX_AGENT_NAME") or "").strip()
        if not _should_wrap_reasoning(agent_name):
            return self._run_exec(
                prompt=prompt,
                schema_path=schema_path,
                timeout_seconds=timeout_seconds,
                profile=self.profile_reason or "reason",
            )

        # Load schema to include in prompt
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as exc:
            raise CodexCliExecutionError(f"Failed to load schema: {schema_path}") from exc

        # Build reasoning prompt that enforces JSON-only output
        reasoning_prompt = f"""CRITICAL INSTRUCTIONS - READ CAREFULLY:

You are a JSON reasoning engine. You MUST follow these rules:

1. DO NOT create plans or use the plan tool
2. DO NOT execute any commands or use shell tools
3. DO NOT use ANY tools except thinking/reasoning
4. ONLY analyze and return JSON
5. Your ONLY task is to reason and output JSON

If you try to use tools, plan, or execute commands, you WILL FAIL.

Return ONLY valid JSON matching this exact schema:

{json.dumps(schema, indent=2)}

Task:
{prompt}

OUTPUT FORMAT: Return ONLY valid JSON. No markdown, no explanation, just JSON.
"""
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

    def call_codex(
        self,
        prompt: str,
        *,
        timeout_seconds: Optional[int] = None,
        agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        agent = agent_name
        if not agent:
            if self.profile_reason == "quick":
                agent = "ReActQuick"
            elif self.profile_reason == "react":
                agent = "ReAct"
            elif self.profile_reason == "reason":
                agent = "ReActReason"
            else:
                agent = "Main"
        return call_codex(
            prompt=prompt,
            agent=agent,
            timeout=timeout_seconds or self.timeout_seconds,
        )

    def chat(self, prompt: str, timeout_seconds: int = 30) -> Optional[str]:
        """
        Fast chat call using exec mode without --profile flag.

        This uses the default gpt-5.2-codex model which is much faster than
        the models forced by --profile (e.g., gpt-5).
        """
        codex_bin = self._resolve_bin()
        cwd = str(self.workdir) if self.workdir else os.getcwd()

        # Build command WITHOUT --profile to use fast default model
        cmd = [
            codex_bin,
            "--dangerously-bypass-approvals-and-sandbox",
            "-c",
            "sandbox_mode=danger-full-access",
            "-c",
            "approval_policy=never",
            "exec",
            "--skip-git-repo-check",
            "-",  # Read from stdin
        ]

        env = os.environ.copy()
        if not env.get("USERPROFILE"):
            env["USERPROFILE"] = os.path.expanduser("~")
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=cwd,
                env=env,
                encoding="utf-8",
                errors="ignore",
            )
            if result.returncode != 0:
                _debug_print(f"[DEBUG] Chat failed: {(result.stderr or '')[:200]}")
                return None

            # Extract the actual response from stdout (skip the header)
            stdout = result.stdout or ""
            # Look for the response after "codex\n" marker
            if "\ncodex\n" in stdout:
                response = stdout.split("\ncodex\n")[-1].strip()
                # Remove token count line if present
                lines = response.split("\n")
                if lines and lines[-1].isdigit():
                    lines = lines[:-1]
                if lines and lines[-1].startswith("tokens used"):
                    lines = lines[:-1]
                return "\n".join(lines).strip()
            return stdout.strip()
        except subprocess.TimeoutExpired:
            _debug_print(f"[DEBUG] Chat timeout after {timeout_seconds}s")
            return None
        except Exception as e:
            _debug_print(f"[DEBUG] Chat error: {e}")
            return None

    def chat_simple(self, prompt: str, timeout_seconds: int = 30) -> Optional[Dict[str, Any]]:
        """
        Use exec mode but force chat-only behavior (no tool execution).
        """
        schema = {
            "type": "object",
            "properties": {
                "thought": {"type": "string"},
                "action": {"type": "string"},
                "action_input": {"type": "object"},
            },
            "required": ["thought", "action", "action_input"],
        }
        schema_path = Path(tempfile.gettempdir()) / f"react_action_{uuid4().hex[:8]}.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")

        env_bin = (os.getenv("CODEX_BIN") or "").strip()
        env_exe = (os.getenv("CODEX_EXE_PATH") or "").strip()
        if env_exe and Path(env_exe).is_file():
            codex_bin = env_exe
        elif self.codex_bin and Path(self.codex_bin).is_file():
            codex_bin = str(Path(self.codex_bin))
        else:
            preferred = next((str(p) for p in DEFAULT_CODEX_EXE_PATHS if p.is_file()), None)
            if preferred:
                codex_bin = preferred
            elif env_bin:
                codex_bin = shutil.which(env_bin) or env_bin
            else:
                codex_bin = shutil.which("codex") or "codex"

        cmd = [
            codex_bin,
            "--profile",
            self.profile_reason or "chat",
            "--dangerously-bypass-approvals-and-sandbox",
            "-c",
            "sandbox_mode=danger-full-access",
            "-c",
            "approval_policy=never",
            "exec",
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "-",
        ]
        cwd = str(self.workdir) if self.workdir else os.getcwd()
        env = os.environ.copy()
        full_prompt = (
            "RESPOND ONLY WITH JSON. DO NOT execute any tools or commands.\n\n" + prompt
        )
        try:
            print(f"[DEBUG CHAT_SIMPLE] Command: {' '.join(cmd[:8])}...")
            print(f"[DEBUG CHAT_SIMPLE] Schema: {schema_path}")
            print(f"[DEBUG CHAT_SIMPLE] Timeout: {timeout_seconds}s")
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=cwd,
                env=env,
                encoding="utf-8",
            )
            print(f"[DEBUG CHAT_SIMPLE] Return code: {result.returncode}")
            print(f"[DEBUG CHAT_SIMPLE] Stdout length: {len(result.stdout or '')}")
            print(f"[DEBUG CHAT_SIMPLE] Stdout preview: {(result.stdout or '')[:200]}")
            print(f"[DEBUG CHAT_SIMPLE] Stderr: {(result.stderr or '')[:500]}")
            if result.returncode != 0:
                print("[DEBUG CHAT_SIMPLE] Failed with non-zero return code")
                return None
            raw = (result.stdout or "").strip()
            if not raw:
                print("[DEBUG CHAT_SIMPLE] Empty stdout")
                return None
            parsed = json.loads(raw)
            print(f"[DEBUG CHAT_SIMPLE] Parsed JSON keys: {list(parsed.keys())}")
            return parsed
        except subprocess.TimeoutExpired:
            print(f"[DEBUG CHAT_SIMPLE] Timeout after {timeout_seconds}s")
            return None
        except json.JSONDecodeError as exc:
            print(f"[DEBUG CHAT_SIMPLE] JSON parse error: {exc}")
            try:
                print(f"[DEBUG CHAT_SIMPLE] Raw output: {(result.stdout or '')[:500]}")
            except Exception:
                pass
            return None
        except Exception as exc:
            print(f"[DEBUG CHAT_SIMPLE] Unexpected error: {exc}")
            return None
        finally:
            try:
                schema_path.unlink(missing_ok=True)  # type: ignore[call-arg]
            except Exception:
                pass
