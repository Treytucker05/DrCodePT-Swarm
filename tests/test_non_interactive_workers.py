from __future__ import annotations

import builtins

from pathlib import Path

from agent.autonomous.config import AgentConfig, RunContext
from agent.autonomous.tools.builtins import build_default_tool_registry


def test_human_ask_blocked_when_interactive_disabled(tmp_path: Path, monkeypatch) -> None:
    def _fail_input(_prompt: str | None = None) -> str:
        raise AssertionError("input() was called while interaction is disabled")

    monkeypatch.setattr(builtins, "input", _fail_input)

    agent_cfg = AgentConfig(allow_human_ask=False)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ctx = RunContext(run_id="t", run_dir=run_dir, workspace_dir=run_dir, profile=agent_cfg.profile)
    reg = build_default_tool_registry(agent_cfg, run_dir)

    result = reg.call("human_ask", {"question": "Q?"}, ctx)
    assert result.success is False
    assert result.error == "interaction_required"
