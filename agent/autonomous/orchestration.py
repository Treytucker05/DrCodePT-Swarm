import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    def __init__(self, tasks: List[str], dependencies: Dict[str, List[str]]):
        self.tasks = tasks
        self.dependencies = dependencies
    
    def should_run_task(self, task_id: str, results: Dict[str, str]) -> bool:
        if task_id not in self.dependencies:
            return True
        for dep_id in self.dependencies[task_id]:
            if dep_id not in results or results[dep_id] == "failed":
                return False
        return True
    
    def get_task_mode(self, task_id: str, results: Dict[str, str]) -> str:
        if task_id not in self.dependencies:
            return "normal"
        for dep_id in self.dependencies[task_id]:
            if dep_id in results and results[dep_id] == "failed":
                return "reduced"
        return "normal"
    
    def get_execution_order(self) -> List[str]:
        visited = set()
        order = []
        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)
            if task_id in self.dependencies:
                for dep_id in self.dependencies[task_id]:
                    visit(dep_id)
            order.append(task_id)
        for task_id in self.tasks:
            visit(task_id)
        return order
