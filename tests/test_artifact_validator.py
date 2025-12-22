"""Tests for artifact validator."""

import pytest
import tempfile
import json
from pathlib import Path
from agent.autonomous.qa.artifact_validator import ArtifactValidator


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_artifact_validator_initialization():
    """Test ArtifactValidator initialization."""
    validator = ArtifactValidator()
    assert validator is not None


def test_validate_json_artifact_valid(temp_dir):
    """Test validating valid JSON artifact."""
    validator = ArtifactValidator()
    
    artifact_path = temp_dir / "data.json"
    artifact_path.write_text(json.dumps({"key": "value"}))
    
    report = validator.validate_json_artifact(artifact_path)
    assert report["valid"] is True
    assert report["size_bytes"] > 0


def test_validate_json_artifact_invalid(temp_dir):
    """Test validating invalid JSON artifact."""
    validator = ArtifactValidator()
    
    artifact_path = temp_dir / "data.json"
    artifact_path.write_text("{invalid json")
    
    report = validator.validate_json_artifact(artifact_path)
    assert report["valid"] is False
    assert len(report["issues"]) > 0


def test_validate_json_artifact_empty(temp_dir):
    """Test validating empty JSON artifact."""
    validator = ArtifactValidator()
    
    artifact_path = temp_dir / "data.json"
    artifact_path.write_text("")
    
    report = validator.validate_json_artifact(artifact_path)
    assert report["valid"] is False


def test_validate_text_artifact_valid(temp_dir):
    """Test validating valid text artifact."""
    validator = ArtifactValidator()
    
    artifact_path = temp_dir / "data.txt"
    artifact_path.write_text("Line 1\nLine 2\nLine 3")
    
    report = validator.validate_text_artifact(artifact_path)
    assert report["valid"] is True
    assert report["line_count"] == 3


def test_validate_artifacts_dir(temp_dir):
    """Test validating artifacts directory."""
    validator = ArtifactValidator()
    
    # Create artifacts
    (temp_dir / "data.json").write_text(json.dumps({"key": "value"}))
    (temp_dir / "notes.txt").write_text("Some notes")
    
    report = validator.validate_artifacts_dir(temp_dir)
    assert len(report["artifacts"]) == 2
    assert report["total_size_bytes"] > 0
