"""Tests for process worker."""

import pytest
import tempfile
import json
import time
from pathlib import Path
from agent.autonomous.workers.process_worker import ProcessWorker


@pytest.fixture
def worker_dir():
    """Create temporary worker directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_process_worker_initialization(worker_dir):
    """Test ProcessWorker initialization."""
    worker = ProcessWorker("task_1", "test goal", worker_dir)
    
    assert worker.task_id == "task_1"
    assert worker.task_goal == "test goal"
    assert worker.status == "pending"


def test_process_worker_status_transitions(worker_dir):
    """Test worker status transitions."""
    worker = ProcessWorker("task_1", "test goal", worker_dir)
    
    assert worker.status == "pending"
    
    # Simulate status changes
    worker.status = "running"
    assert worker.status == "running"
    
    worker.status = "completed"
    assert worker.status == "completed"


def test_process_worker_get_result(worker_dir):
    """Test getting result from worker."""
    worker = ProcessWorker("task_1", "test goal", worker_dir)
    
    # Create result file
    task_dir = worker_dir / "task_1"
    task_dir.mkdir()
    result_data = {"status": "success", "data": "test"}
    (task_dir / "result.json").write_text(json.dumps(result_data))
    
    # Get result
    result = worker.get_result()
    assert result == result_data


def test_process_worker_get_result_not_found(worker_dir):
    """Test getting result when file doesn't exist."""
    worker = ProcessWorker("task_1", "test goal", worker_dir)
    
    result = worker.get_result()
    assert result is None


def test_process_worker_is_running(worker_dir):
    """Test checking if worker is running."""
    worker = ProcessWorker("task_1", "test goal", worker_dir)
    
    # Not started yet
    assert not worker.is_running()
    
    # Simulate running
    worker.process = type('obj', (object,), {'poll': lambda self: None})()
    assert worker.is_running()
    
    # Simulate completed
    worker.process = type('obj', (object,), {'poll': lambda self: 0})()
    assert not worker.is_running()


def test_process_worker_get_duration(worker_dir):
    """Test getting worker duration."""
    worker = ProcessWorker("task_1", "test goal", worker_dir)
    
    # No duration yet
    assert worker.get_duration() is None
    
    # Set times
    worker.start_time = 100.0
    worker.end_time = 110.0
    
    duration = worker.get_duration()
    assert duration == 10.0
