from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent.modes.swarm import mode_swarm


def _make_fake_coded_response(schema_name: str) -> Dict[str, Any]:
    if schema_name == "task_decomposition.schema.json":
        return {
            "subtasks": [
                {"id": "A", "goal": "Do A", "depends_on": [], "notes": ""},
                {"id": "B", "goal": "Do B", "depends_on": [], "notes": ""},
            ]
        }
    if schema_name in {"plan_next_step.schema.json", "plan.schema.json"}:
        return {
            "goal": "Finish quickly",
            "steps": [
                {
                    "id": "step_1",
                    "goal": "Finish",
                    "rationale_short": "Smoke check",
                    "tool_name": "finish",
                    "tool_args": [{"key": "summary", "value": "ok"}],
                    "success_criteria": [],
                    "preconditions": [],
                    "postconditions": [],
                }
            ],
        }
    if schema_name == "reflection.schema.json":
        return {
            "status": "success",
            "explanation_short": "",
            "next_hint": "",
            "failure_type": "none",
            "lesson": "",
            "memory_write": None,
        }
    if schema_name == "condition_check.schema.json":
        return {"ok": True, "failed": []}
    if schema_name == "chat_response.schema.json":
        return {"response": "ok", "action": {"type": "none", "folder": None}}
    raise AssertionError(f"Unhandled schema in test stub: {schema_name}")


def test_swarm_runs_with_explicit_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    expected_cwd = str(repo_root.resolve())
    calls: List[Dict[str, Any]] = []

    monkeypatch.setenv("SWARM_MAX_WORKERS", "2")
    monkeypatch.setenv("SWARM_MAX_SUBTASKS", "2")
    monkeypatch.setenv("SWARM_MAX_STEPS", "1")
    monkeypatch.setenv("SWARM_PLANNER_MODE", "react")
    monkeypatch.setenv("SWARM_SUMMARIZE", "0")
    monkeypatch.setenv("SWARM_LLM_HEARTBEAT_SECONDS", "0")

    def _no_chdir(_: str) -> None:
        raise AssertionError("os.chdir should not be called in swarm threads")

    monkeypatch.setattr(os, "chdir", _no_chdir)

    def fake_run(cmd: List[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cwd = kwargs.get("cwd")
        assert cwd is not None, "swarm must pass explicit cwd to subprocess.run"
        actual = str(Path(cwd).resolve())
        assert actual == expected_cwd, (
            f"swarm must use repo_root as cwd for codex runs: {actual} != {expected_cwd}"
        )

        try:
            schema_idx = cmd.index("--output-schema")
            out_idx = cmd.index("--output-last-message")
        except ValueError as exc:
            raise AssertionError("codex CLI args missing output flags") from exc

        schema_path = Path(cmd[schema_idx + 1])
        out_path = Path(cmd[out_idx + 1])
        payload = _make_fake_coded_response(schema_path.name)
        out_path.write_text(json.dumps(payload), encoding="utf-8")

        calls.append({"cmd": cmd, "cwd": actual})
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    from agent.llm import codex_cli_client

    monkeypatch.setattr(codex_cli_client.subprocess, "run", fake_run)

    mode_swarm("Smoke test objective", unsafe_mode=False)

    assert len(calls) >= 2, "expected at least one codex call per subagent"
