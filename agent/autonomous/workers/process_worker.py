"""Process-based worker for parallel task execution."""

import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ProcessWorker:
    """Spawn and manage a worker process.
    
    Each worker runs in a separate process, allowing true parallelism.
    Workers communicate via result files in JSON format.
    """
    
    def __init__(self, task_id: str, task_goal: str, run_dir: Path, profile: str = "deep"):
        """Initialize process worker.
        
        Args:
            task_id: Unique task ID
            task_goal: Goal/task description
            run_dir: Directory for worker output
            profile: Execution profile (fast, deep, audit)
        """
        self.task_id = task_id
        self.task_goal = task_goal
        self.run_dir = run_dir
        self.profile = profile
        self.process: Optional[subprocess.Popen] = None
        self.status = "pending"
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        logger.info(f"ProcessWorker initialized: {task_id}")
    
    def start(self) -> bool:
        """Start worker process.
        
        Returns:
            True if started successfully, False otherwise
        """
        worker_dir = self.run_dir / self.task_id
        worker_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Build command to run agent
            cmd = [
                "python",
                "-m",
                "agent.run",
                "--task",
                self.task_goal,
                "--run-dir",
                str(worker_dir),
                "--profile",
                self.profile,
            ]
            
            # Open log files
            stdout_file = open(worker_dir / "stdout.log", "w")
            stderr_file = open(worker_dir / "stderr.log", "w")
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                cwd=self.run_dir.parent,
                stdout=stdout_file,
                stderr=stderr_file,
            )
            
            self.status = "running"
            self.start_time = datetime.now(timezone.utc).timestamp()
            logger.info(f"Started worker {self.task_id} (PID: {self.process.pid})")
            return True
        
        except Exception as exc:
            logger.error(f"Failed to start worker {self.task_id}: {exc}", exc_info=True)
            self.status = "failed"
            return False
    
    def wait(self, timeout: Optional[int] = None) -> bool:
        """Wait for worker to complete.
        
        Args:
            timeout: Timeout in seconds (None = wait forever)
        
        Returns:
            True if completed, False if timeout
        """
        if not self.process:
            logger.warning(f"Worker {self.task_id} not started")
            return False
        
        try:
            self.process.wait(timeout=timeout)
            self.status = "completed"
            self.end_time = datetime.now(timezone.utc).timestamp()
            logger.info(f"Worker {self.task_id} completed")
            return True
        
        except subprocess.TimeoutExpired:
            self.status = "timeout"
            logger.warning(f"Worker {self.task_id} timed out")
            return False
    
    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get result from worker.
        
        Returns:
            Result dict or None if not available
        """
        result_path = self.run_dir / self.task_id / "result.json"
        
        if not result_path.exists():
            logger.debug(f"Result file not found: {result_path}")
            return None
        
        try:
            data = json.loads(result_path.read_text())
            logger.debug(f"Loaded result for {self.task_id}")
            return data
        
        except Exception as exc:
            logger.error(f"Error loading result: {exc}", exc_info=True)
            return None
    
    def is_running(self) -> bool:
        """Check if worker is still running.
        
        Returns:
            True if running, False otherwise
        """
        if not self.process:
            return False
        
        return self.process.poll() is None
    
    def kill(self) -> bool:
        """Kill worker process.
        
        Returns:
            True if killed, False if not running
        """
        if not self.process or not self.is_running():
            return False
        
        try:
            self.process.kill()
            self.process.wait(timeout=5)
            self.status = "killed"
            logger.warning(f"Killed worker {self.task_id}")
            return True
        
        except Exception as exc:
            logger.error(f"Error killing worker: {exc}", exc_info=True)
            return False
    
    def get_duration(self) -> Optional[float]:
        """Get worker execution duration in seconds.
        
        Returns:
            Duration or None if not completed
        """
        if not self.start_time or not self.end_time:
            return None
        
        return self.end_time - self.start_time
