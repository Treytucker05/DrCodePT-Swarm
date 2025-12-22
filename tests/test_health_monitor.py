"""Tests for worker health monitoring."""

import pytest
import tempfile
import time
from pathlib import Path
from agent.autonomous.workers.process_worker import ProcessWorker
from agent.autonomous.workers.health_monitor import WorkerHealthMonitor


@pytest.fixture
def worker_dir():
    """Create temporary worker directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_health_monitor_initialization():
    """Test WorkerHealthMonitor initialization."""
    monitor = WorkerHealthMonitor(check_interval=10, stall_timeout=300)
    
    assert monitor.check_interval == 10
    assert monitor.stall_timeout == 300


def test_check_worker_health(worker_dir):
    """Test checking worker health."""
    monitor = WorkerHealthMonitor()
    worker = ProcessWorker("task_1", "goal", worker_dir)
    
    health = monitor.check_worker_health(worker)
    
    assert health["task_id"] == "task_1"
    assert health["status"] == "pending"
    assert "timestamp" in health


def test_check_worker_health_no_process(worker_dir):
    """Test checking health of worker with no process."""
    monitor = WorkerHealthMonitor()
    worker = ProcessWorker("task_1", "goal", worker_dir)
    
    health = monitor.check_worker_health(worker)
    
    assert not health["is_healthy"]
    assert "No process" in health["issues"]


def test_monitor_all(worker_dir):
    """Test monitoring all workers."""
    monitor = WorkerHealthMonitor()
    
    workers = {
        "task_1": ProcessWorker("task_1", "goal 1", worker_dir),
        "task_2": ProcessWorker("task_2", "goal 2", worker_dir),
    }
    
    health_report = monitor.monitor_all(workers)
    
    assert len(health_report) == 2
    assert "task_1" in health_report
    assert "task_2" in health_report


def test_get_unhealthy_workers(worker_dir):
    """Test getting unhealthy workers."""
    monitor = WorkerHealthMonitor()
    
    health_report = {
        "task_1": {"is_healthy": True},
        "task_2": {"is_healthy": False},
        "task_3": {"is_healthy": True},
    }
    
    unhealthy = monitor.get_unhealthy_workers(health_report)
    
    assert len(unhealthy) == 1
    assert "task_2" in unhealthy


def test_get_health_summary(worker_dir):
    """Test getting health summary."""
    monitor = WorkerHealthMonitor()
    
    health_report = {
        "task_1": {"is_healthy": True},
        "task_2": {"is_healthy": False},
        "task_3": {"is_healthy": True},
    }
    
    summary = monitor.get_health_summary(health_report)
    
    assert summary["total_workers"] == 3
    assert summary["healthy"] == 2
    assert summary["unhealthy"] == 1
    assert summary["health_percentage"] == pytest.approx(66.67, rel=0.01)
