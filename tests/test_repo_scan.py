from __future__ import annotations

from pathlib import Path

from agent.autonomous.repo_scan import build_repo_index, build_repo_map
from agent.config.profile import ProfileConfig


def _profile(max_files: int, max_bytes: int) -> ProfileConfig:
    return ProfileConfig(
        name="fast",
        workers=1,
        plan_timeout_s=30,
        plan_retry_timeout_s=10,
        heartbeat_s=1,
        max_files_to_read=max_files,
        max_total_bytes_to_read=max_bytes,
        max_glob_results=100,
        max_web_sources=1,
        allow_interactive=False,
        stage_checkpoints=False,
    )


def test_repo_index_skips_common_dirs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()
    (repo_root / ".git" / "config").write_text("git", encoding="utf-8")
    (repo_root / "node_modules").mkdir()
    (repo_root / "node_modules" / "pkg.js").write_text("js", encoding="utf-8")
    (repo_root / "__pycache__").mkdir()
    (repo_root / "__pycache__" / "x.pyc").write_text("pyc", encoding="utf-8")
    (repo_root / "keep.py").write_text("print('ok')", encoding="utf-8")

    run_dir = tmp_path / "run"
    run_dir.mkdir()

    results = build_repo_index(repo_root, run_dir=run_dir, max_results=50)
    assert (run_dir / "repo_index.json").is_file()
    for entry in results:
        parts = Path(entry.path).parts
        assert ".git" not in parts
        assert "node_modules" not in parts
        assert "__pycache__" not in parts


def test_repo_map_respects_byte_cap(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "a.txt").write_text("a" * 10, encoding="utf-8")
    (repo_root / "b.txt").write_text("b" * 10, encoding="utf-8")

    run_dir = tmp_path / "run"
    run_dir.mkdir()

    index = build_repo_index(repo_root, run_dir=run_dir, max_results=10)
    profile = _profile(max_files=5, max_bytes=1)
    mapped = build_repo_map(index, run_dir=run_dir, profile=profile)
    assert (run_dir / "repo_map.json").is_file()
    assert len(mapped) == 1
