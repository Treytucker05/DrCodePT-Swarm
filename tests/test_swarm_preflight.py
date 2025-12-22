from __future__ import annotations

import builtins
import json
from pathlib import Path

import pytest

from agent.modes import swarm as swarm_mod
from agent.preflight.clarify import ClarifyResult


class _DummyLLM:
    def with_context(self, **_kwargs):
        return self


def _write_artifacts(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trace.jsonl").write_text(
        json.dumps({"type": "stop"}) + "\n",
        encoding="utf-8",
    )
    swarm_mod._write_result(run_dir, {"ok": True})


def test_preflight_prompts_before_workers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWARM_SUMMARIZE", "0")
    run_root = tmp_path / "runs"
    run_root.mkdir()

    monkeypatch.setattr(swarm_mod, "_swarm_run_dir", lambda: run_root)
    monkeypatch.setattr(swarm_mod.CodexCliClient, "from_env", lambda *args, **kwargs: _DummyLLM())

    monkeypatch.setattr(
        swarm_mod,
        "_decompose",
        lambda *args, **kwargs: [swarm_mod.Subtask(id="A", goal="do work", depends_on=[], notes="")],
    )

    clarify_calls = {"count": 0}
    prompt_called = {"value": False}

    def _fake_clarifier(*_args, **_kwargs) -> ClarifyResult:
        clarify_calls["count"] += 1
        if clarify_calls["count"] == 1:
            return ClarifyResult(
                ready_to_run=False,
                normalized_objective="Find a launcher",
                task_type="find_filepath",
                search_terms=["launcher"],
                glob_patterns=[],
                candidate_roots=[],
                blocking_questions=[
                    {
                        "id": "launcher_type",
                        "question": "Which launcher type?",
                        "why": "Need target file type",
                        "default": None,
                    }
                ],
                assumptions_if_no_answer=[],
                expected_output="Path to the launcher file.",
            )
        return ClarifyResult(
            ready_to_run=True,
            normalized_objective="Find the launcher path",
            task_type="find_filepath",
            search_terms=["launcher"],
            glob_patterns=["**/*.bat"],
            candidate_roots=["launchers"],
            blocking_questions=[],
            assumptions_if_no_answer=[],
            expected_output="Path to the launcher file.",
        )

    def _fake_input(_prompt: str | None = None) -> str:
        prompt_called["value"] = True
        return "bat"

    def _fake_run_subagent(subtask, **kwargs):
        assert prompt_called["value"], "expected clarification before starting workers"
        run_dir = kwargs.get("run_dir")
        _write_artifacts(run_dir)
        return subtask, "success", "", run_dir

    monkeypatch.setattr(swarm_mod, "run_clarifier", _fake_clarifier)
    monkeypatch.setattr(builtins, "input", _fake_input)
    monkeypatch.setattr(swarm_mod, "_run_subagent", _fake_run_subagent)

    swarm_mod.mode_swarm("Find launcher", unsafe_mode=False, profile="fast")


def test_preflight_creates_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWARM_SUMMARIZE", "0")
    run_root = tmp_path / "runs"
    run_root.mkdir()

    monkeypatch.setattr(swarm_mod, "_swarm_run_dir", lambda: run_root)
    monkeypatch.setattr(swarm_mod.CodexCliClient, "from_env", lambda *args, **kwargs: _DummyLLM())
    monkeypatch.setattr(
        swarm_mod,
        "_decompose",
        lambda *args, **kwargs: [swarm_mod.Subtask(id="A", goal="do work", depends_on=[], notes="")],
    )

    def _fake_clarifier(*_args, **_kwargs) -> ClarifyResult:
        return ClarifyResult(
            ready_to_run=True,
            normalized_objective="Review repo",
            task_type="repo_review",
            search_terms=["readme"],
            glob_patterns=["README.md"],
            candidate_roots=["."],
            blocking_questions=[],
            assumptions_if_no_answer=[],
            expected_output="Summary",
        )

    def _fail_input(_prompt: str | None = None) -> str:
        raise AssertionError("input() should not be called when ready_to_run is true")

    def _fake_run_subagent(subtask, **kwargs):
        run_dir = kwargs.get("run_dir")
        _write_artifacts(run_dir)
        return subtask, "success", "", run_dir

    monkeypatch.setattr(swarm_mod, "run_clarifier", _fake_clarifier)
    monkeypatch.setattr(builtins, "input", _fail_input)
    monkeypatch.setattr(swarm_mod, "_run_subagent", _fake_run_subagent)

    swarm_mod.mode_swarm("Review repo", unsafe_mode=False, profile="fast")

    preflight = run_root / "preflight"
    assert (preflight / "root_listing.json").is_file()
    assert (preflight / "repo_index.json").is_file()
    assert (preflight / "repo_map.json").is_file()


def test_swarm_worker_blocks_human_ask(tmp_path: Path) -> None:
    from agent.autonomous.config import RunContext
    from agent.autonomous.tools.builtins import build_default_tool_registry

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    agent_cfg = swarm_mod._build_agent_cfg(repo_root, unsafe_mode=False, profile_name="fast")

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ctx = RunContext(run_id="t", run_dir=run_dir, workspace_dir=run_dir, profile=agent_cfg.profile)
    reg = build_default_tool_registry(agent_cfg, run_dir)

    result = reg.call("human_ask", {"question": "Q?"}, ctx)
    assert result.success is False
    assert result.error == "interaction_required"
