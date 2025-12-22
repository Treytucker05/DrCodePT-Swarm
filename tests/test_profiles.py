from __future__ import annotations

from pathlib import Path

import pytest

from agent.config.profile import ProfileConfig, resolve_profile
from agent.autonomous.repo_scan import build_repo_index


def test_profile_defaults() -> None:
    profile = resolve_profile("fast")
    assert profile.name == "fast"
    assert profile.max_files_to_read > 0
    assert profile.max_total_bytes_to_read > 0

    deep = resolve_profile("deep")
    assert deep.max_files_to_read >= profile.max_files_to_read
    assert deep.max_total_bytes_to_read >= profile.max_total_bytes_to_read


def test_repo_index_respects_max_glob_results(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    for idx in range(10):
        (repo_root / f"f{idx}.txt").write_text("x", encoding="utf-8")

    run_dir = tmp_path / "run"
    run_dir.mkdir()

    results = build_repo_index(repo_root, run_dir=run_dir, max_results=5)
    assert len(results) == 5
    assert (run_dir / "repo_index.json").is_file()


def test_human_ask_blocked_when_interactive_disabled(tmp_path: Path) -> None:
    from agent.autonomous.config import AgentConfig, RunContext
    from agent.autonomous.tools.builtins import build_default_tool_registry

    profile = ProfileConfig(
        name="fast",
        workers=1,
        plan_timeout_s=30,
        plan_retry_timeout_s=10,
        heartbeat_s=1,
        max_files_to_read=5,
        max_total_bytes_to_read=1024,
        max_glob_results=10,
        max_web_sources=1,
        allow_interactive=False,
        stage_checkpoints=False,
    )
    agent_cfg = AgentConfig(profile=profile, allow_human_ask=False)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ctx = RunContext(run_id="t", run_dir=run_dir, workspace_dir=run_dir, profile=profile)
    reg = build_default_tool_registry(agent_cfg, run_dir)

    result = reg.call("human_ask", {"question": "Q?"}, ctx)
    assert result.success is False
    assert result.error == "interaction_required"
    assert isinstance(result.output, dict)


def test_file_read_caps(tmp_path: Path) -> None:
    from agent.autonomous.config import AgentConfig, RunContext
    from agent.autonomous.tools.builtins import file_read_factory
    from agent.config.profile import RunUsage

    file_path = tmp_path / "a.txt"
    file_path.write_text("hello world", encoding="utf-8")

    profile = ProfileConfig(
        name="fast",
        workers=1,
        plan_timeout_s=30,
        plan_retry_timeout_s=10,
        heartbeat_s=1,
        max_files_to_read=1,
        max_total_bytes_to_read=5,
        max_glob_results=10,
        max_web_sources=1,
        allow_interactive=False,
        stage_checkpoints=False,
    )
    usage = RunUsage()
    agent_cfg = AgentConfig(profile=profile)
    ctx = RunContext(run_id="t", run_dir=tmp_path, workspace_dir=tmp_path, profile=profile, usage=usage)

    file_read = file_read_factory(agent_cfg)
    first = file_read(ctx, type("Args", (), {"path": str(file_path), "max_bytes": 10})())
    assert first.success is True
    assert "hello" in (first.output or {}).get("content", "")

    second = file_read(ctx, type("Args", (), {"path": str(file_path), "max_bytes": 10})())
    assert second.success is False
