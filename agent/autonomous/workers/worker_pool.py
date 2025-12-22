import logging
import time
from typing import Dict, List, Optional
from pathlib import Path
from agent.autonomous.workers.process_worker import ProcessWorker

logger = logging.getLogger(__name__)

class WorkerPool:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.workers: Dict[str, ProcessWorker] = {}
        self.completed: Dict[str, dict] = {}
    
    def submit(self, task_id: str, task_goal: str, run_dir: Path, profile: str = "deep") -> bool:
        while self._count_running() >= self.max_workers:
            time.sleep(1)
        worker = ProcessWorker(task_id, task_goal, run_dir, profile)
        if not worker.start():
            return False
        self.workers[task_id] = worker
        return True
    
    def _count_running(self) -> int:
        return sum(1 for w in self.workers.values() if w.is_running())
    
    def collect_results(self, timeout: int = 3600) -> Dict[str, dict]:
        start_time = time.time()
        for task_id, worker in self.workers.items():
            remaining_timeout = timeout - (time.time() - start_time)
            if remaining_timeout <= 0:
                worker.kill()
                continue
            worker.wait(timeout=int(remaining_timeout))
            result = worker.get_result()
            if result:
                self.completed[task_id] = result
        return self.completed
    
    def get_status(self) -> Dict[str, str]:
        return {task_id: worker.status for task_id, worker in self.workers.items()}
    
    def kill_all(self) -> int:
        killed = 0
        for worker in self.workers.values():
            if worker.kill():
                killed += 1
        return killed
