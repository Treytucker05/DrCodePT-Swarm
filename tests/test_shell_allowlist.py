from __future__ import annotations

from pathlib import Path

import pytest

from agent.autonomous.config import AgentConfig, RunContext
from agent.autonomous.tools.builtins import shell_exec_factory


class _Proc:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_shell_exec_blocks_non_allowlisted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    agent_cfg = AgentConfig(unsafe_mode=False, fs_allowed_roots=(tmp_path,))
    ctx = RunContext(run_id="t", run_dir=tmp_path, workspace_dir=tmp_path)

    called = {"count": 0}

    def _fake_run(*args, **kwargs):
        called["count"] += 1
        return _Proc()

    monkeypatch.setattr("agent.autonomous.tools.builtins.subprocess.run", _fake_run)

    shell_exec = shell_exec_factory(agent_cfg)
    result = shell_exec(ctx, type("Args", (), {"command": "echo hi", "timeout_seconds": 1, "cwd": None})())
    assert result.success is False
    assert "blocked" in (result.error or "")
    assert called["count"] == 0


def test_shell_exec_allows_rg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    agent_cfg = AgentConfig(unsafe_mode=False, fs_allowed_roots=(tmp_path,))
    ctx = RunContext(run_id="t", run_dir=tmp_path, workspace_dir=tmp_path)

    called = {"count": 0}

    def _fake_run(*args, **kwargs):
        called["count"] += 1
        return _Proc(returncode=0, stdout="rg 13.0", stderr="")

    monkeypatch.setattr("agent.autonomous.tools.builtins.subprocess.run", _fake_run)

    shell_exec = shell_exec_factory(agent_cfg)
    result = shell_exec(ctx, type("Args", (), {"command": "rg --version", "timeout_seconds": 1, "cwd": None})())
    assert result.success is True
    assert called["count"] == 1


def test_shell_exec_blocks_chaining(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    agent_cfg = AgentConfig(unsafe_mode=False, fs_allowed_roots=(tmp_path,))
    ctx = RunContext(run_id="t", run_dir=tmp_path, workspace_dir=tmp_path)

    shell_exec = shell_exec_factory(agent_cfg)
    result = shell_exec(ctx, type("Args", (), {"command": "python -V && echo hi", "timeout_seconds": 1, "cwd": None})())
    assert result.success is False
    assert "blocked" in (result.error or "")
