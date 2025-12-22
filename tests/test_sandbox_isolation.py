"""Tests for sandbox isolation."""

import pytest
import tempfile
import shutil
from pathlib import Path
from agent.autonomous.isolation.sandbox import SandboxIsolation


@pytest.fixture
def test_repo():
    """Create a temporary repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create some files
        (repo_path / "README.md").write_text("# Test Repo")
        (repo_path / "file1.py").write_text("# Python file")
        (repo_path / "subdir").mkdir()
        (repo_path / "subdir" / "file2.py").write_text("# Another file")

        yield repo_path


def test_sandbox_isolation_initialization(test_repo):
    """Test SandboxIsolation initialization."""
    isolation = SandboxIsolation(test_repo, "test_run")

    assert isolation.repo_root == test_repo
    assert isolation.run_id == "test_run"
    assert isolation.sandboxes_dir.exists()


def test_create_sandbox(test_repo):
    """Test creating a sandbox."""
    isolation = SandboxIsolation(test_repo, "test_run")

    sandbox_path = isolation.create_sandbox("task_1")

    assert sandbox_path.exists()
    assert (sandbox_path / "README.md").exists()
    assert (sandbox_path / "file1.py").exists()


def test_get_changes(test_repo):
    """Test detecting changes in sandbox."""
    isolation = SandboxIsolation(test_repo, "test_run")

    sandbox_path = isolation.create_sandbox("task_1")

    # Modify a file
    (sandbox_path / "file1.py").write_text("# Modified")

    # Add a new file
    (sandbox_path / "new_file.py").write_text("# New file")

    # Get changes
    changes = isolation.get_changes("task_1")

    assert "file1.py" in changes
    assert changes["file1.py"] == "modified"
    assert "new_file.py" in changes
    assert changes["new_file.py"] == "added"


def test_apply_changes(test_repo):
    """Test applying changes from sandbox."""
    isolation = SandboxIsolation(test_repo, "test_run")

    sandbox_path = isolation.create_sandbox("task_1")

    # Modify a file in sandbox
    (sandbox_path / "file1.py").write_text("# Modified in sandbox")

    # Apply changes
    result = isolation.apply_changes("task_1", test_repo)
    assert result is True

    # Verify change was applied
    assert (test_repo / "file1.py").read_text() == "# Modified in sandbox"


def test_cleanup_sandbox(test_repo):
    """Test cleaning up a sandbox."""
    isolation = SandboxIsolation(test_repo, "test_run")

    sandbox_path = isolation.create_sandbox("task_1")
    assert sandbox_path.exists()

    # Cleanup
    result = isolation.cleanup_sandbox("task_1")
    assert result is True
    assert not sandbox_path.exists()


def test_cleanup_all_sandboxes(test_repo):
    """Test cleaning up all sandboxes."""
    isolation = SandboxIsolation(test_repo, "test_run")

    # Create multiple sandboxes
    isolation.create_sandbox("task_1")
    isolation.create_sandbox("task_2")
    isolation.create_sandbox("task_3")

    # Cleanup all
    cleaned = isolation.cleanup_all()
    assert cleaned == 3
