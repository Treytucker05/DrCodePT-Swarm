"""Tests for worker pool."""

import pytest
import tempfile
from pathlib import Path
from agent.autonomous.workers.worker_pool import WorkerPool
from agent.autonomous.workers.process_worker import ProcessWorker


@pytest.fixture
def worker_dir():
    """Create temporary worker directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_worker_pool_initialization(worker_dir):
    """Test WorkerPool initialization."""
    pool = WorkerPool(max_workers=4)
    
    assert pool.max_workers == 4
    assert len(pool.workers) == 0


def test_worker_pool_get_status(worker_dir):
    """Test getting pool status."""
    pool = WorkerPool(max_workers=2)
    
    # Add mock workers
    worker1 = ProcessWorker("task_1", "goal 1", worker_dir)
    worker2 = ProcessWorker("task_2", "goal 2", worker_dir)
    
    pool.workers["task_1"] = worker1
    pool.workers["task_2"] = worker2
    
    status = pool.get_status()
    assert status["task_1"] == "pending"
    assert status["task_2"] == "pending"


def test_worker_pool_count_running(worker_dir):
    """Test counting running workers."""
    pool = WorkerPool(max_workers=4)
    
    # Add mock workers
    worker1 = ProcessWorker("task_1", "goal 1", worker_dir)
    worker2 = ProcessWorker("task_2", "goal 2", worker_dir)
    
    pool.workers["task_1"] = worker1
    pool.workers["task_2"] = worker2
    
    # Both pending, so 0 running
    assert pool._count_running() == 0
    
    # Simulate running
    worker1.status = "running"
    worker1.process = type('obj', (object,), {'poll': lambda self: None})()
    
    assert pool._count_running() == 1


def test_worker_pool_collect_results(worker_dir):
    """Test collecting results from workers."""
    pool = WorkerPool(max_workers=2)
    
    # Add mock workers with results
    worker1 = ProcessWorker("task_1", "goal 1", worker_dir)
    worker2 = ProcessWorker("task_2", "goal 2", worker_dir)
    
    # Create result files
    (worker_dir / "task_1").mkdir()
    (worker_dir / "task_1" / "result.json").write_text('{"status": "success"}')
    
    (worker_dir / "task_2").mkdir()
    (worker_dir / "task_2" / "result.json").write_text('{"status": "success"}')
    
    pool.workers["task_1"] = worker1
    pool.workers["task_2"] = worker2
    
    # Simulate completed
    worker1.status = "completed"
    worker2.status = "completed"
    
    results = pool.collect_results(timeout=10)
    
    assert len(results) == 2
    assert results["task_1"]["status"] == "success"
    assert results["task_2"]["status"] == "success"
