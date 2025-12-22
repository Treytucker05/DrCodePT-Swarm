from __future__ import annotations

from pathlib import Path

from agent.autonomous.task_orchestrator import TaskOrchestrator
from agent.modes import swarm as swarm_mod


def test_task_orchestrator_reduced_goal(tmp_path: Path) -> None:
    orchestrator = TaskOrchestrator()
    subtask = swarm_mod.Subtask(id="C", goal="Synthesize results", depends_on=["A", "B"], notes="")
    status_by_id = {"A": "failed", "B": "success"}
    should_reduce, failed = orchestrator.should_reduce(subtask.depends_on, status_by_id)
    assert should_reduce is True
    assert failed == ["A"]

    run_dir = tmp_path / "A_run"
    run_dir.mkdir()
    results_by_id = {"A": {"error": {"message": "boom", "type": "exception"}}}
    run_dirs_by_id = {"A": run_dir}
    subtasks_by_id = {"A": swarm_mod.Subtask(id="A", goal="Collect data", depends_on=[], notes="")}

    reduced = swarm_mod._build_reduced_goal(
        subtask,
        failed_deps=failed,
        results_by_id=results_by_id,
        run_dirs_by_id=run_dirs_by_id,
        subtasks_by_id=subtasks_by_id,
    )
    assert "Reduced synthesis mode" in reduced
    assert "Failed dependencies: A" in reduced
    assert "Missing artifacts" in reduced
    assert "Propose next-run objectives" in reduced
