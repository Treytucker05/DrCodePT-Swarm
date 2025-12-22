"""Tests for benchmarking."""

import pytest
import tempfile
import json
from pathlib import Path
from scripts.benchmark import BenchmarkRunner


def test_benchmark_runner_initialization():
    """Test BenchmarkRunner initialization."""
    runner = BenchmarkRunner()
    assert len(runner.results) == 0


def test_benchmark_task():
    """Test benchmarking a single task."""
    runner = BenchmarkRunner()
    
    result = runner.benchmark_task(
        "test_task",
        "Test task",
        "Test goal",
        timeout=10,
    )
    
    assert result["task_name"] == "test_task"
    assert result["success"] is True
    assert result["duration_seconds"] > 0


def test_benchmark_multiple_tasks():
    """Test benchmarking multiple tasks."""
    runner = BenchmarkRunner()
    
    runner.benchmark_task("task_1", "Task 1", "Goal 1")
    runner.benchmark_task("task_2", "Task 2", "Goal 2")
    runner.benchmark_task("task_3", "Task 3", "Goal 3")
    
    assert len(runner.results) == 3


def test_save_results():
    """Test saving benchmark results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runner = BenchmarkRunner()
        runner.benchmark_task("task_1", "Task 1", "Goal 1")
        
        output_path = Path(tmpdir) / "results.json"
        runner.save_results(output_path)
        
        assert output_path.exists()
        
        data = json.loads(output_path.read_text())
        assert len(data) == 1


def test_get_summary():
    """Test getting benchmark summary."""
    runner = BenchmarkRunner()
    
    runner.benchmark_task("task_1", "Task 1", "Goal 1")
    runner.benchmark_task("task_2", "Task 2", "Goal 2")
    
    summary = runner.get_summary()
    
    assert summary["total_benchmarks"] == 2
    assert summary["successful"] == 2
    assert "avg_duration" in summary
