"""Tests for evaluation harness."""

import pytest
import json
from pathlib import Path


@pytest.fixture
def golden_tasks():
    """Load golden tasks."""
    tasks_path = Path(__file__).parent / "fixtures" / "golden_tasks.json"
    with open(tasks_path) as f:
        return json.load(f)


def test_golden_tasks_loaded(golden_tasks):
    """Test that golden tasks are loaded."""
    assert "tasks" in golden_tasks
    assert len(golden_tasks["tasks"]) > 0


def test_golden_task_structure(golden_tasks):
    """Test that golden tasks have required structure."""
    for task in golden_tasks["tasks"]:
        assert "id" in task
        assert "description" in task
        assert "task" in task
        assert "timeout" in task


def test_repo_analysis_task(golden_tasks):
    """Test repo analysis golden task."""
    task = next(t for t in golden_tasks["tasks"] if t["id"] == "repo_analysis")
    
    assert task["expected_status"] == "success"
    assert "repo_map.json" in task["required_artifacts"]


def test_code_review_task(golden_tasks):
    """Test code review golden task."""
    task = next(t for t in golden_tasks["tasks"] if t["id"] == "code_review")
    
    assert task["expected_status"] == "success"
    assert task["timeout"] == 600


def test_no_interactive_prompts_task(golden_tasks):
    """Test no interactive prompts golden task."""
    task = next(t for t in golden_tasks["tasks"] if t["id"] == "no_interactive_prompts")
    
    assert task["mode"] == "swarm"
    assert task["expected_no_prompts"] is True


def test_partial_failure_handling_task(golden_tasks):
    """Test partial failure handling golden task."""
    task = next(t for t in golden_tasks["tasks"] if t["id"] == "partial_failure_handling")
    
    assert task["mode"] == "swarm"
    assert "success" in task["expected_status"]
    assert "partial_failure" in task["expected_status"]


def test_loop_detection_task(golden_tasks):
    """Test loop detection golden task."""
    task = next(t for t in golden_tasks["tasks"] if t["id"] == "loop_detection")
    
    assert task["expected_no_false_loops"] is True
