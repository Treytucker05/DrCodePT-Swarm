"""Tests for isolation package exports."""

from dataclasses import fields

from agent.autonomous.isolation import (
    DEFAULT_SKIP_DIRS,
    WorktreeInfo,
    copy_repo_to_workspace,
    create_worktree,
    remove_worktree,
    sanitize_branch_name,
)


def test_isolation_exports_smoke():
    assert isinstance(DEFAULT_SKIP_DIRS, set)

    assert [f.name for f in fields(WorktreeInfo)] == ["path", "branch"]

    assert callable(copy_repo_to_workspace)
    assert callable(create_worktree)
    assert callable(remove_worktree)
    assert callable(sanitize_branch_name)

