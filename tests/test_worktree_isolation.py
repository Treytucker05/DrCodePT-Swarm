"""Tests for git worktree isolation."""

import pytest
import tempfile
import subprocess
from pathlib import Path
from agent.autonomous.isolation.worktree import WorktreeIsolation


@pytest.fixture
def git_repo():
    """Create a temporary git repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Configure git
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        (repo_path / "README.md").write_text("# Test Repo")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


def test_worktree_isolation_initialization(git_repo):
    """Test WorktreeIsolation initialization."""
    isolation = WorktreeIsolation(git_repo, "test_run")

    assert isolation.repo_root == git_repo
    assert isolation.run_id == "test_run"
    assert isolation.worktrees_dir.exists()


def test_create_worktree(git_repo):
    """Test creating a worktree."""
    isolation = WorktreeIsolation(git_repo, "test_run")

    worktree_path = isolation.create_worktree("task_1")

    assert worktree_path.exists()
    assert worktree_path.name == "test_run_task_1"


def test_cleanup_worktree(git_repo):
    """Test cleaning up a worktree."""
    isolation = WorktreeIsolation(git_repo, "test_run")

    # Create worktree
    worktree_path = isolation.create_worktree("task_1")
    assert worktree_path.exists()

    # Cleanup
    result = isolation.cleanup_worktree("task_1")
    assert result is True
    assert not worktree_path.exists()


def test_cleanup_all_worktrees(git_repo):
    """Test cleaning up all worktrees."""
    isolation = WorktreeIsolation(git_repo, "test_run")

    # Create multiple worktrees
    isolation.create_worktree("task_1")
    isolation.create_worktree("task_2")
    isolation.create_worktree("task_3")

    # Cleanup all
    cleaned = isolation.cleanup_all()
    assert cleaned == 3
