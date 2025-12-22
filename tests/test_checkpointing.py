"""Tests for checkpoint management."""

import pytest
import tempfile
import json
from pathlib import Path
from agent.autonomous.checkpointing import CheckpointManager


def test_checkpoint_manager_initialization():
    """Test CheckpointManager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        manager = CheckpointManager(run_dir)

        assert manager.checkpoint_dir.exists()
        assert manager.checkpoint_dir == run_dir / "checkpoints"


def test_save_and_load_checkpoint():
    """Test saving and loading checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        manager = CheckpointManager(run_dir)

        # Save checkpoint
        state = {"data": "test", "step": 1}
        manager.save_checkpoint(1, state)

        # Load checkpoint
        loaded = manager.load_checkpoint(1)
        assert loaded == state


def test_list_checkpoints():
    """Test listing checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        manager = CheckpointManager(run_dir)

        # Save multiple checkpoints
        manager.save_checkpoint(1, {"step": 1})
        manager.save_checkpoint(2, {"step": 2})
        manager.save_checkpoint(3, {"step": 3})

        # List checkpoints
        checkpoints = manager.list_checkpoints()
        assert checkpoints == [1, 2, 3]


def test_get_latest_checkpoint():
    """Test getting latest checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        manager = CheckpointManager(run_dir)

        # Save checkpoints
        manager.save_checkpoint(1, {"step": 1})
        manager.save_checkpoint(5, {"step": 5})
        manager.save_checkpoint(3, {"step": 3})

        # Get latest
        latest = manager.get_latest_checkpoint()
        assert latest == 5


def test_delete_checkpoint():
    """Test deleting checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        manager = CheckpointManager(run_dir)

        # Save checkpoint
        manager.save_checkpoint(1, {"step": 1})
        assert manager.get_latest_checkpoint() == 1

        # Delete checkpoint
        deleted = manager.delete_checkpoint(1)
        assert deleted is True
        assert manager.get_latest_checkpoint() is None


def test_cleanup_old_checkpoints():
    """Test cleaning up old checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        manager = CheckpointManager(run_dir)

        # Save 10 checkpoints
        for i in range(1, 11):
            manager.save_checkpoint(i, {"step": i})

        # Cleanup, keeping last 3
        deleted = manager.cleanup_old_checkpoints(keep_last_n=3)
        assert deleted == 7

        # Verify only last 3 remain
        remaining = manager.list_checkpoints()
        assert remaining == [8, 9, 10]
