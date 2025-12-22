import logging
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ProcessWorker:
    def __init__(self, task_id: str, task_goal: str, run_dir: Path, profile: str = "deep"):
        self.task_id = task_id
        self.task_goal = task_goal
        self.run_dir = run_dir
        self.profile = profile
        self.process: Optional[subprocess.Popen] = None
        self.status = "pending"
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self) -> bool:
        worker_dir = self.run_dir / self.task_id
        worker_dir.mkdir(parents=True, exist_ok=True)
        try:
            cmd = ["python", "-m", "agent.run", "--task", self.task_goal, "--run-dir", str(worker_dir), "--profile", self.profile]
            stdout_file = open(worker_dir / "stdout.log", "w")
            stderr_file = open(worker_dir / "stderr.log", "w")
            self.process = subprocess.Popen(cmd, cwd=self.run_dir.parent, stdout=stdout_file, stderr=stderr_file)
            self.status = "running"
            self.start_time = datetime.now(timezone.utc).timestamp()
            return True
        except Exception as exc:
            self.status = "failed"
            return False
    
    def wait(self, timeout: Optional[int] = None) -> bool:
        if not self.process:
            return False
        try:
            self.process.wait(timeout=timeout)
            self.status = "completed"
            self.end_time = datetime.now(timezone.utc).timestamp()
            return True
        except subprocess.TimeoutExpired:
            self.status = "timeout"
            return False
    
    def get_result(self) -> Optional[Dict[str, Any]]:
        result_path = self.run_dir / self.task_id / "result.json"
        if not result_path.exists():
            return None
        try:
            return json.loads(result_path.read_text())
        except:
            return None
    
    def is_running(self) -> bool:
        if not self.process:
            return False
        return self.process.poll() is None
    
    def kill(self) -> bool:
        if not self.process or not self.is_running():
            return False
        try:
            self.process.kill()
            self.process.wait(timeout=5)
            self.status = "killed"
            return True
        except:
            return False
    
    def get_duration(self) -> Optional[float]:
        if not self.start_time or not self.end_time:
            return None
        return self.end_time - self.start_time
