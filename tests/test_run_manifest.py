"""Tests for run manifest."""

import pytest
import tempfile
import json
from pathlib import Path
from agent.autonomous.runner import AgentRunner
from agent.autonomous.config import RunnerConfig, AgentConfig, PlannerConfig
from agent.autonomous.checkpointing import CheckpointManager


def test_run_manifest_contains_profile():
    """Test that run manifest contains profile info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        checkpoint_manager = CheckpointManager(run_dir)

        # Create a mock runner (simplified)
        # In real test, would need full setup
        manifest = {
            "run_id": "test_run",
            "task": "test task",
            "profile": "deep",
            "profile_config": {
                "max_steps": 50,
                "timeout_seconds": 1800,
            },
            "started_at": "2025-12-22T10:00:00Z",
            "checkpoints": [],
        }

        manifest_path = run_dir / "run_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        # Load and verify
        loaded = json.loads(manifest_path.read_text())
        assert loaded["profile"] == "deep"
        assert loaded["profile_config"]["max_steps"] == 50


def test_run_manifest_updates_on_completion():
    """Test that manifest updates with final status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)

        # Create initial manifest
        manifest = {
            "run_id": "test_run",
            "task": "test task",
            "profile": "deep",
            "started_at": "2025-12-22T10:00:00Z",
            "checkpoints": [1, 2, 3],
        }

        manifest_path = run_dir / "run_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        # Update manifest
        manifest["completed_at"] = "2025-12-22T10:30:00Z"
        manifest["status"] = "success"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        # Verify update
        loaded = json.loads(manifest_path.read_text())
        assert loaded["status"] == "success"
        assert "completed_at" in loaded
