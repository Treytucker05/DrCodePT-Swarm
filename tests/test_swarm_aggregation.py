"""Tests for swarm aggregation."""

import pytest
from concurrent.futures import Future
from agent.modes.swarm import aggregate_swarm_results


def create_mock_future(result=None, exception=None):
    """Create a mock future."""
    future = Future()
    if exception:
        future.set_exception(exception)
    else:
        future.set_result(result)
    return future


def test_aggregation_all_success():
    """Test aggregation when all workers succeed."""
    class MockResult:
        def __init__(self, task_id):
            self.task_id = task_id
            self.status = "success"

    futures = [
        create_mock_future(result=MockResult("A")),
        create_mock_future(result=MockResult("B")),
    ]

    result = aggregate_swarm_results(futures)
    assert result.status == "success"
    assert len(result.results) == 2
    assert len(result.failures) == 0


def test_aggregation_partial_failure():
    """Test aggregation with partial failure."""
    class MockResult:
        def __init__(self, task_id):
            self.task_id = task_id
            self.status = "success"

    futures = [
        create_mock_future(result=MockResult("A")),
        create_mock_future(exception=TimeoutError("Worker timed out")),
    ]

    result = aggregate_swarm_results(futures)
    assert result.status == "partial_failure"
    assert len(result.results) == 1
    assert len(result.failures) == 1


def test_aggregation_all_failure():
    """Test aggregation when all workers fail."""
    futures = [
        create_mock_future(exception=Exception("Worker crashed")),
        create_mock_future(exception=Exception("Worker crashed")),
    ]

    result = aggregate_swarm_results(futures)
    assert result.status == "failure"
    assert len(result.results) == 0
    assert len(result.failures) == 2
