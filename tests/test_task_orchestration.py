"""Tests for task orchestration."""

import pytest
from agent.autonomous.orchestration import TaskOrchestrator


def test_task_skipped_if_dependency_failed():
    """Test that task is skipped if dependency failed."""
    orchestrator = TaskOrchestrator(
        tasks=["task_a", "task_b", "task_c"],
        dependencies={
            "task_a": [],
            "task_b": [],
            "task_c": ["task_a", "task_b"],
        }
    )

    results = {"task_a": "failed"}
    assert not orchestrator.should_run_task("task_c", results)


def test_task_runs_in_reduced_mode_if_dependency_failed():
    """Test that task runs in reduced mode if dependency failed."""
    orchestrator = TaskOrchestrator(
        tasks=["task_a", "task_b", "task_c"],
        dependencies={
            "task_a": [],
            "task_b": [],
            "task_c": ["task_a", "task_b"],
        }
    )

    results = {"task_a": "failed", "task_b": "success"}
    mode = orchestrator.get_task_mode("task_c", results)
    assert mode == "reduced"


def test_task_runs_in_normal_mode_if_dependencies_succeed():
    """Test that task runs in normal mode if dependencies succeed."""
    orchestrator = TaskOrchestrator(
        tasks=["task_a", "task_b", "task_c"],
        dependencies={
            "task_a": [],
            "task_b": [],
            "task_c": ["task_a", "task_b"],
        }
    )

    results = {"task_a": "success", "task_b": "success"}
    mode = orchestrator.get_task_mode("task_c", results)
    assert mode == "normal"


def test_execution_order_respects_dependencies():
    """Test that execution order respects dependencies."""
    orchestrator = TaskOrchestrator(
        tasks=["task_a", "task_b", "task_c"],
        dependencies={
            "task_a": [],
            "task_b": ["task_a"],
            "task_c": ["task_a", "task_b"],
        }
    )

    order = orchestrator.get_execution_order()

    # task_a should come before task_b
    assert order.index("task_a") < order.index("task_b")

    # task_b should come before task_c
    assert order.index("task_b") < order.index("task_c")
