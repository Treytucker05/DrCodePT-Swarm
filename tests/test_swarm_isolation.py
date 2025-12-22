from __future__ import annotations

from pathlib import Path

import pytest

from agent.autonomous.isolation import copy_repo_to_workspace
from agent.modes import swarm as swarm_mod


class _DummyLLM:
    def with_context(self, **kwargs):
        return self


def test_copy_repo_to_workspace_skips_dirs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()
    (repo_root / ".git" / "config").write_text("git", encoding="utf-8")
    (repo_root / "node_modules").mkdir()
    (repo_root / "node_modules" / "pkg.js").write_text("js", encoding="utf-8")
    (repo_root / "__pycache__").mkdir()
    (repo_root / "__pycache__" / "x.pyc").write_text("pyc", encoding="utf-8")
    (repo_root / "src").mkdir()
    (repo_root / "src" / "main.py").write_text("print('ok')", encoding="utf-8")

    dest = tmp_path / "workspace"
    copy_repo_to_workspace(repo_root, dest)

    assert (dest / "src" / "main.py").is_file()
    assert not (dest / ".git").exists()
    assert not (dest / "node_modules").exists()
    assert not (dest / "__pycache__").exists()


def test_swarm_uses_sandbox_workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SWARM_SUMMARIZE", "0")
    run_root = tmp_path / "runs"
    run_root.mkdir()
    monkeypatch.setattr(swarm_mod, "_swarm_run_dir", lambda: run_root)
    monkeypatch.setattr(swarm_mod.CodexCliClient, "from_env", lambda *args, **kwargs: _DummyLLM())

    def _fake_decompose(llm, objective: str, *, max_items: int):
        return [swarm_mod.Subtask(id="A", goal="do work", depends_on=[], notes="")]

    monkeypatch.setattr(swarm_mod, "_decompose", _fake_decompose)

    def _fast_copy(repo_root: Path, dest: Path):
        dest.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(swarm_mod, "copy_repo_to_workspace", _fast_copy)

    captured: dict[str, Path] = {}

    def _fake_run_subagent(*args, **kwargs):
        subtask = args[0]
        workdir = kwargs.get("workdir")
        captured["workdir"] = workdir
        run_dir = kwargs.get("run_dir")
        swarm_mod._write_result(run_dir, {"ok": True})
        return subtask, "success", "", run_dir

    monkeypatch.setattr(swarm_mod, "_run_subagent", _fake_run_subagent)

    swarm_mod.mode_swarm("test", unsafe_mode=False, profile="deep")

    assert captured.get("workdir") is not None
    assert captured["workdir"].name == "workspace"
