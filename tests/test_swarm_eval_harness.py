from __future__ import annotations

import builtins
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from agent.modes import swarm as swarm_mod


@dataclass(frozen=True)
class SwarmEvalCase:
    name: str
    objective: str
    subtasks: list[swarm_mod.Subtask]
    expect_repo_map: bool = False
    expect_reduced: bool = False
    expect_structured_failure: bool = False


class _DummyLLM:
    def with_context(self, **kwargs):
        return self


def _write_artifacts(run_dir: Path, *, ok: bool, error: dict | None = None, repo_map: bool = False) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "trace.jsonl").write_text(json.dumps({"type": "stop"}) + "\n", encoding="utf-8")
    payload = {"ok": ok}
    if error:
        payload["error"] = error
    (run_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")
    if repo_map:
        (run_dir / "repo_map.json").write_text(json.dumps({"files": []}), encoding="utf-8")


def _run_swarm_eval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: SwarmEvalCase,
    *,
    capture_goal: dict | None = None,
) -> Path:
    monkeypatch.setenv("SWARM_SUMMARIZE", "0")
    run_root = tmp_path / "runs"
    run_root.mkdir()
    monkeypatch.setattr(swarm_mod, "_swarm_run_dir", lambda: run_root)
    monkeypatch.setattr(swarm_mod.CodexCliClient, "from_env", lambda *args, **kwargs: _DummyLLM())

    monkeypatch.setattr(swarm_mod, "_decompose", lambda *args, **kwargs: case.subtasks)

    def _fake_run_subagent(*args, **kwargs):
        subtask = args[0]
        run_dir = kwargs.get("run_dir")
        if capture_goal is not None and subtask.id == "C":
            capture_goal["goal"] = subtask.goal
        if case.expect_structured_failure and subtask.id == "A":
            _write_artifacts(
                run_dir,
                ok=False,
                error={"message": "boom", "type": "exception"},
                repo_map=case.expect_repo_map and subtask.id == "A",
            )
            return subtask, "failed", "boom", run_dir
        _write_artifacts(run_dir, ok=True, repo_map=case.expect_repo_map and subtask.id == "A")
        return subtask, "success", "", run_dir

    monkeypatch.setattr(swarm_mod, "_run_subagent", _fake_run_subagent)

    # Ensure no interactive prompts occur.
    monkeypatch.setattr(builtins, "input", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("input called")))

    swarm_mod.mode_swarm(case.objective, unsafe_mode=False, profile="fast")
    return run_root


def test_swarm_eval_repo_map_and_no_loop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    case = SwarmEvalCase(
        name="repo_scan",
        objective="Review repo structure",
        subtasks=[swarm_mod.Subtask(id="A", goal="Scan repo and build map", depends_on=[], notes="")],
        expect_repo_map=True,
    )
    run_root = _run_swarm_eval(tmp_path, monkeypatch, case)
    assert list(run_root.rglob("repo_map.json")), "expected repo_map.json to be produced"
    assert not list(run_root.rglob("loop_detected.json")), "unexpected loop_detected.json"


def test_swarm_eval_partial_failure_reduced_synthesis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    case = SwarmEvalCase(
        name="partial_failure",
        objective="Summarize results with partial failure",
        subtasks=[
            swarm_mod.Subtask(id="A", goal="Collect data", depends_on=[], notes=""),
            swarm_mod.Subtask(id="C", goal="Synthesize findings", depends_on=["A"], notes=""),
        ],
        expect_structured_failure=True,
        expect_reduced=True,
    )
    capture: dict = {}
    run_root = _run_swarm_eval(tmp_path, monkeypatch, case, capture_goal=capture)
    assert list(run_root.rglob("result.json")), "expected result.json artifacts"
    assert "Reduced synthesis mode" in capture.get("goal", "")
