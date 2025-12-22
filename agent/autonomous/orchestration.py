"""Task orchestration with dependency tracking."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Orchestrate task execution with dependencies."""

    def __init__(self, tasks: List[str], dependencies: Dict[str, List[str]]):
        """Initialize orchestrator.

        Args:
            tasks: List of task IDs
            dependencies: Dict mapping task_id -> [depends_on_ids]
        """
        self.tasks = tasks
        self.dependencies = dependencies

    def should_run_task(self, task_id: str, results: Dict[str, str]) -> bool:
        """Check if task should run based on dependencies.

        Args:
            task_id: ID of task to check
            results: Dict mapping task_id -> status

        Returns:
            True if task should run, False otherwise
        """
        if task_id not in self.dependencies:
            return True

        for dep_id in self.dependencies[task_id]:
            if dep_id not in results:
                return False  # Dependency not run yet
            if results[dep_id] == "failed":
                return False  # Dependency failed

        return True

    def get_task_mode(self, task_id: str, results: Dict[str, str]) -> str:
        """Get execution mode for task.

        Args:
            task_id: ID of task
            results: Dict mapping task_id -> status

        Returns:
            "normal" or "reduced"
        """
        if task_id not in self.dependencies:
            return "normal"

        # Check if any dependencies failed
        for dep_id in self.dependencies[task_id]:
            if dep_id in results and results[dep_id] == "failed":
                return "reduced"  # Run reduced synthesis

        return "normal"

    def get_execution_order(self) -> List[str]:
        """Get topological sort of tasks.

        Returns:
            List of task IDs in execution order
        """
        visited = set()
        order = []

        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)

            # Visit dependencies first
            if task_id in self.dependencies:
                for dep_id in self.dependencies[task_id]:
                    visit(dep_id)

            order.append(task_id)

        for task_id in self.tasks:
            visit(task_id)

        return order
