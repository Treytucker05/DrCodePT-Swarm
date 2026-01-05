from __future__ import annotations

import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from agent.autonomous.models import ToolResult

_ALLOWED_TEST_COMMANDS = {"python", "py", "pytest"}


class SelfReviewArgs(BaseModel):
    run_tests: bool = Field(
        default=True, description="Run pytest as part of the self-review"
    )
    test_command: str = Field(
        default="python -m pytest -q",
        description="Test command to run when run_tests is True",
    )
    report_path: Optional[str] = Field(
        default=None,
        description="Optional path for the report (relative to repo root if not absolute)",
    )
    max_output_chars: int = Field(
        default=4000,
        description="Max characters of test output to include in the report",
    )


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "agent").is_dir() and (parent / "AGENTS.md").is_file():
            return parent
    return here.parents[3]


def _command_root(command: str) -> str:
    try:
        parts = shlex.split(command, posix=False)
    except Exception:
        parts = command.strip().split()
    if not parts:
        return ""
    token = Path(parts[0]).name.lower()
    for ext in (".exe", ".cmd", ".bat"):
        if token.endswith(ext):
            token = token[: -len(ext)]
    return token


def _tail(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def self_review(ctx, args: SelfReviewArgs) -> ToolResult:
    repo_root = _find_repo_root()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.report_path:
        report_path = Path(args.report_path)
        if not report_path.is_absolute():
            report_path = repo_root / report_path
    else:
        report_path = repo_root / "runs" / "self_review" / f"self_review_{timestamp}.md"

    report_path.parent.mkdir(parents=True, exist_ok=True)

    test_exit_code = None
    stdout_tail = ""
    stderr_tail = ""
    test_command = ""

    if args.run_tests:
        test_command = (args.test_command or "").strip()
        if not test_command:
            return ToolResult(success=False, error="test_command is required when run_tests is True")

        if _command_root(test_command) not in _ALLOWED_TEST_COMMANDS:
            return ToolResult(
                success=False,
                error="test_command not allowed (use python/py/pytest)",
            )

        result = subprocess.run(
            test_command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            shell=True,
        )
        test_exit_code = result.returncode
        stdout_tail = _tail(result.stdout or "", args.max_output_chars)
        stderr_tail = _tail(result.stderr or "", args.max_output_chars)

    report_lines = [
        "# Self Review Report",
        "",
        f"- Timestamp: {datetime.now().isoformat()}",
        f"- Repo root: {repo_root}",
        f"- Run dir: {getattr(ctx, 'run_dir', None)}",
        "",
        "## Tests",
    ]

    if args.run_tests:
        report_lines.extend(
            [
                f"- Command: {test_command}",
                f"- Exit code: {test_exit_code}",
                "",
                "### Stdout (tail)",
                "```",
                stdout_tail or "(no stdout)",
                "```",
                "",
                "### Stderr (tail)",
                "```",
                stderr_tail or "(no stderr)",
                "```",
            ]
        )
    else:
        report_lines.append("- Skipped (run_tests=False)")

    report_lines.extend(
        [
            "",
            "## Next Actions",
            "- If tests failed, inspect failing tests and address the first error shown above.",
            "- Re-run self_review after fixes.",
        ]
    )

    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    success = True
    if args.run_tests and test_exit_code not in (0, None):
        success = False

    return ToolResult(
        success=success,
        output={
            "report_path": str(report_path),
            "test_exit_code": test_exit_code,
        },
    )


__all__ = ["SelfReviewArgs", "self_review"]
