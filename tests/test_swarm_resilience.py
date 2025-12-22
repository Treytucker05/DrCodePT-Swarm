from __future__ import annotations

from pathlib import Path

import pytest

from agent.modes import swarm as swarm_mod


class _DummyLLM:
    def with_context(self, **kwargs):
        return self


def test_swarm_captures_subagent_exceptions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWARM_SUMMARIZE", "0")

    run_root = tmp_path / "runs"
    run_root.mkdir()

    monkeypatch.setattr(swarm_mod, "_swarm_run_dir", lambda: run_root)
    monkeypatch.setattr(swarm_mod.CodexCliClient, "from_env", lambda *args, **kwargs: _DummyLLM())

    def _fake_decompose(llm, objective: str, *, max_items: int):
        return [swarm_mod.Subtask(id="A", goal="boom", depends_on=[], notes="")]

    monkeypatch.setattr(swarm_mod, "_decompose", _fake_decompose)

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(swarm_mod, "_run_subagent", _boom)

    swarm_mod.mode_swarm("test objective", unsafe_mode=False)

    results = list(run_root.rglob("result.json"))
    assert results, "expected a result.json for failed subagent"
