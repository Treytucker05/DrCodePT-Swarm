"""Worker pool for managing multiple parallel workers."""

import logging
import time
from typing import Dict, List, Optional
from pathlib import Path
from agent.autonomous.workers.process_worker import ProcessWorker

logger = logging.getLogger(__name__)


class WorkerPool:
    """Manage a pool of worker processes.
    
    Controls concurrency by limiting the number of simultaneous workers.
    Provides methods to submit tasks, wait for completion, and collect results.
    """
    
    def __init__(self, max_workers: int = 4):
        """Initialize worker pool.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.workers: Dict[str, ProcessWorker] = {}
        self.completed: Dict[str, dict] = {}
        logger.info(f"WorkerPool initialized with max_workers={max_workers}")
    
    def submit(self, task_id: str, task_goal: str, run_dir: Path, profile: str = "deep") -> bool:
        """Submit task to worker pool.
        
        Args:
            task_id: Unique task ID
            task_goal: Goal/task description
            run_dir: Directory for worker output
            profile: Execution profile (fast, deep, audit)
        
        Returns:
            True if submitted, False if pool full
        """
        # Wait for slot if pool is full
        while self._count_running() >= self.max_workers:
            logger.debug(f"Pool full ({self._count_running()}/{self.max_workers}), waiting for slot")
            time.sleep(1)
        
        # Create and start worker
        worker = ProcessWorker(task_id, task_goal, run_dir, profile)
        
        if not worker.start():
            logger.error(f"Failed to start worker {task_id}")
            return False
        
        self.workers[task_id] = worker
        logger.info(f"Submitted task {task_id} to pool")
        return True
    
    def wait_for_slot(self) -> None:
        """Wait for a worker slot to become available."""
        while self._count_running() >= self.max_workers:
            time.sleep(1)
    
    def _count_running(self) -> int:
        """Count running workers.
        
        Returns:
            Number of currently running workers
        """
        return sum(1 for w in self.workers.values() if w.is_running())
    
    def collect_results(self, timeout: int = 3600) -> Dict[str, dict]:
        """Collect results from all workers.
        
        Args:
            timeout: Total timeout in seconds
        
        Returns:
            Dict mapping task_id -> result
        """
        start_time = time.time()
        
        for task_id, worker in self.workers.items():
            remaining_timeout = timeout - (time.time() - start_time)
            
            if remaining_timeout <= 0:
                logger.warning("Timeout collecting results, killing remaining workers")
                worker.kill()
                continue
            
            # Wait for worker
            logger.info(f"Waiting for worker {task_id} (timeout: {remaining_timeout:.0f}s)")
            worker.wait(timeout=int(remaining_timeout))
            
            # Get result
            result = worker.get_result()
            if result:
                self.completed[task_id] = result
                logger.info(f"Collected result for {task_id}")
            else:
                logger.warning(f"No result for {task_id}")
        
        return self.completed
    
    def get_status(self) -> Dict[str, str]:
        """Get status of all workers.
        
        Returns:
            Dict mapping task_id -> status
        """
        return {task_id: worker.status for task_id, worker in self.workers.items()}
    
    def kill_all(self) -> int:
        """Kill all workers.
        
        Returns:
            Number of workers killed
        """
        killed = 0
        
        for worker in self.workers.values():
            if worker.kill():
                killed += 1
        
        logger.info(f"Killed {killed} workers")
        return killed
