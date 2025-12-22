from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.modes import swarm as swarm_mod
from agent.preflight.clarify import ClarifyResult
from agent.preflight.repo_fish import PreflightResult


class _DummyLLM:
    def with_context(self, **_kwargs):
        return self


def _fake_preflight(run_dir: Path) -> PreflightResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    root_listing = []
    repo_map = []
    root_listing_path = run_dir / "root_listing.json"
    repo_index_path = run_dir / "repo_index.json"
    repo_map_path = run_dir / "repo_map.json"
    root_listing_path.write_text(json.dumps({"entries": []}), encoding="utf-8")
    repo_index_path.write_text(json.dumps({"files": []}), encoding="utf-8")
    repo_map_path.write_text(json.dumps({"files": []}), encoding="utf-8")
    return PreflightResult(
        run_dir=run_dir,
        root_listing_path=root_listing_path,
        repo_index_path=repo_index_path,
        repo_map_path=repo_map_path,
        root_listing=root_listing,
        repo_map=repo_map,
    )


def _ready_clarify() -> ClarifyResult:
    return ClarifyResult(
        ready_to_run=True,
        normalized_objective="swarm aggregation test",
        task_type="other",
        search_terms=[],
        glob_patterns=[],
        candidate_roots=[],
        blocking_questions=[],
        assumptions_if_no_answer=[],
        expected_output="ok",
    )


def test_swarm_aggregation_handles_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWARM_SUMMARIZE", "0")
    run_root = tmp_path / "runs"
    run_root.mkdir()

    monkeypatch.setattr(swarm_mod, "_swarm_run_dir", lambda: run_root)
    monkeypatch.setattr(swarm_mod.CodexCliClient, "from_env", lambda *args, **kwargs: _DummyLLM())

    monkeypatch.setattr(
        swarm_mod,
        "_decompose",
        lambda *args, **kwargs: [
            swarm_mod.Subtask(id="A", goal="boom", depends_on=[], notes=""),
            swarm_mod.Subtask(id="B", goal="ok", depends_on=[], notes=""),
        ],
    )

    monkeypatch.setattr(
        swarm_mod,
        "run_preflight",
        lambda **kwargs: _fake_preflight(kwargs["run_dir"]),
    )
    monkeypatch.setattr(swarm_mod, "run_clarifier", lambda *args, **kwargs: _ready_clarify())

    def _fake_run_subagent(subtask, **kwargs):
        run_dir = kwargs.get("run_dir")
        if subtask.id == "A":
            raise RuntimeError("boom")
        swarm_mod._write_result(run_dir, {"ok": True})
        return subtask, "success", "", run_dir

    monkeypatch.setattr(swarm_mod, "_run_subagent", _fake_run_subagent)

    swarm_mod.mode_swarm("test objective", unsafe_mode=False)

    results = list(run_root.rglob("result.json"))
    assert len(results) >= 2
    payloads = [json.loads(p.read_text(encoding="utf-8")) for p in results]
    assert any(p.get("ok") is False and (p.get("error") or {}).get("type") == "RuntimeError" for p in payloads)
    assert any(p.get("ok") is True for p in payloads)
