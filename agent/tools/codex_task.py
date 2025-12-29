"""
Codex Task Tool - Wrapper for using Codex CLI as a tool.

This makes Codex CLI a callable tool rather than the brain:
- The agent's planner (OpenRouter) decides WHEN to use Codex
- Codex handles actual code execution/audit tasks
- Results flow back to the agent loop

Use cases:
- Write/edit code
- Fix bugs
- Audit repository
- Run tests
- Code review
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CodexTaskArgs(BaseModel):
    """Arguments for the codex_task tool."""
    task: str = Field(..., description="What to do (e.g., 'fix bug in auth.py')")
    constraints: List[str] = Field(
        default_factory=list,
        description="Constraints (e.g., 'don't modify tests', 'run pytest after')"
    )
    target_paths: List[str] = Field(
        default_factory=list,
        description="Specific files/directories to focus on"
    )
    test_command: Optional[str] = Field(
        None,
        description="Command to run tests after changes"
    )
    timeout_seconds: int = Field(
        default=300,
        description="Timeout for the task"
    )


@dataclass
class CodexTaskResult:
    """Result from a Codex task execution."""
    success: bool
    summary: str = ""
    files_changed: List[str] = field(default_factory=list)
    diff_summary: str = ""
    commands_run: List[str] = field(default_factory=list)
    test_results: Optional[str] = None
    error: Optional[str] = None
    raw_output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "summary": self.summary,
            "files_changed": self.files_changed,
            "diff_summary": self.diff_summary,
            "commands_run": self.commands_run,
            "test_results": self.test_results,
            "error": self.error,
        }


def _build_codex_prompt(args: CodexTaskArgs) -> str:
    """Build a focused prompt for Codex."""
    parts = [f"TASK: {args.task}"]

    if args.constraints:
        parts.append("\nCONSTRAINTS:")
        for c in args.constraints:
            parts.append(f"- {c}")

    if args.target_paths:
        parts.append("\nFOCUS ON THESE FILES:")
        for p in args.target_paths:
            parts.append(f"- {p}")

    if args.test_command:
        parts.append(f"\nAFTER CHANGES, RUN: {args.test_command}")

    parts.append("\n\nProceed with the task. Make minimal, focused changes.")

    return "\n".join(parts)


def codex_task(args: CodexTaskArgs) -> CodexTaskResult:
    """
    Execute a code task using Codex CLI.

    This is the main entry point for using Codex as a tool.
    """
    try:
        from agent.llm.codex_cli_client import CodexCliClient, call_codex

        # Build the prompt
        prompt = _build_codex_prompt(args)

        logger.info(f"[CODEX_TASK] Starting: {args.task[:50]}...")

        # Call Codex
        result = call_codex(
            prompt=prompt,
            agent="Main",
            timeout=args.timeout_seconds,
            enable_search=False,  # Focus on local code
        )

        # Parse result
        if "error" in result:
            error_type = result.get("error", "unknown")
            if error_type == "rate_limit":
                return CodexTaskResult(
                    success=False,
                    error="Rate limit reached. Try again later.",
                    raw_output=str(result),
                )
            elif error_type == "timeout":
                return CodexTaskResult(
                    success=False,
                    error=f"Task timed out after {args.timeout_seconds}s",
                    raw_output=str(result),
                )
            else:
                return CodexTaskResult(
                    success=False,
                    error=result.get("stderr", str(result)),
                    raw_output=str(result),
                )

        # Success case
        output = result.get("result", "")

        # Try to extract structured info
        files_changed = _extract_files_changed(output)
        diff_summary = _extract_diff_summary(output)
        commands = _extract_commands(output)

        return CodexTaskResult(
            success=True,
            summary=f"Completed: {args.task[:100]}",
            files_changed=files_changed,
            diff_summary=diff_summary,
            commands_run=commands,
            raw_output=output[:2000] if output else None,
        )

    except Exception as e:
        logger.error(f"[CODEX_TASK] Failed: {e}")
        return CodexTaskResult(
            success=False,
            error=str(e),
        )


def _extract_files_changed(output: str) -> List[str]:
    """Extract list of modified files from Codex output."""
    files = []
    # Look for common patterns
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("Modified:") or line.startswith("Created:"):
            path = line.split(":", 1)[1].strip()
            if path:
                files.append(path)
        elif line.startswith("+++ ") or line.startswith("--- "):
            # Diff format
            path = line[4:].strip()
            if path and not path.startswith("/dev/null"):
                files.append(path)
    return list(set(files))


def _extract_diff_summary(output: str) -> str:
    """Extract a summary of changes from Codex output."""
    lines = []
    in_diff = False
    for line in output.split("\n"):
        if line.startswith("diff ") or line.startswith("@@"):
            in_diff = True
        if in_diff and len(lines) < 20:
            lines.append(line)
        if len(lines) >= 20:
            lines.append("... (truncated)")
            break
    return "\n".join(lines)


def _extract_commands(output: str) -> List[str]:
    """Extract commands that were run."""
    commands = []
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("$ ") or line.startswith("> "):
            commands.append(line[2:])
        elif line.startswith("Running:"):
            cmd = line.split(":", 1)[1].strip()
            if cmd:
                commands.append(cmd)
    return commands


def codex_task_tool(ctx, args: CodexTaskArgs):
    """
    Tool wrapper for codex_task that returns ToolResult.

    This integrates with the agent's tool registry.
    """
    from agent.autonomous.models import ToolResult as LegacyToolResult

    result = codex_task(args)

    if result.success:
        output = {
            "summary": result.summary,
            "files_changed": result.files_changed,
            "diff_summary": result.diff_summary[:500] if result.diff_summary else "",
            "commands_run": result.commands_run,
        }
        if result.test_results:
            output["test_results"] = result.test_results
        return LegacyToolResult(
            success=True,
            output=output,
        )
    else:
        return LegacyToolResult(
            success=False,
            error=result.error or "Codex task failed",
            retryable=True,
        )


# Convenience functions for common tasks

def codex_fix_bug(file_path: str, bug_description: str, **kwargs) -> CodexTaskResult:
    """Fix a bug in a specific file."""
    return codex_task(CodexTaskArgs(
        task=f"Fix bug: {bug_description}",
        target_paths=[file_path],
        **kwargs,
    ))


def codex_add_feature(description: str, target_paths: List[str] = None, **kwargs) -> CodexTaskResult:
    """Add a new feature."""
    return codex_task(CodexTaskArgs(
        task=f"Add feature: {description}",
        target_paths=target_paths or [],
        **kwargs,
    ))


def codex_audit(scope: str = ".", focus: str = "security", **kwargs) -> CodexTaskResult:
    """Audit code for issues."""
    return codex_task(CodexTaskArgs(
        task=f"Audit for {focus} issues",
        target_paths=[scope],
        constraints=["Report issues only, don't modify code"],
        **kwargs,
    ))


def codex_refactor(file_path: str, description: str, **kwargs) -> CodexTaskResult:
    """Refactor code."""
    return codex_task(CodexTaskArgs(
        task=f"Refactor: {description}",
        target_paths=[file_path],
        **kwargs,
    ))


__all__ = [
    "CodexTaskArgs",
    "CodexTaskResult",
    "codex_task",
    "codex_task_tool",
    "codex_fix_bug",
    "codex_add_feature",
    "codex_audit",
    "codex_refactor",
]
