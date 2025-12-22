import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from agent.autonomous.workers.process_worker import ProcessWorker

logger = logging.getLogger(__name__)

class WorkerHealthMonitor:
    def __init__(self, check_interval: int = 10, stall_timeout: int = 300):
        self.check_interval = check_interval
        self.stall_timeout = stall_timeout
        self.health_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def check_worker_health(self, worker: ProcessWorker) -> Dict[str, Any]:
        health = {"task_id": worker.task_id, "status": worker.status, "timestamp": datetime.now(timezone.utc).isoformat(), "issues": [], "is_healthy": True}
        if not worker.process:
            health["issues"].append("No process")
            health["is_healthy"] = False
            return health
        if worker.process.poll() is not None:
            health["status"] = "completed"
            return health
        if worker.start_time and time.time() - worker.start_time > self.stall_timeout:
            health["issues"].append(f"Stalled for {time.time() - worker.start_time:.0f}s")
            health["is_healthy"] = False
        return health
    
    def monitor_all(self, workers: Dict[str, ProcessWorker]) -> Dict[str, Dict[str, Any]]:
        health_report = {}
        for task_id, worker in workers.items():
            health = self.check_worker_health(worker)
            health_report[task_id] = health
            if task_id not in self.health_history:
                self.health_history[task_id] = []
            self.health_history[task_id].append(health)
        return health_report
    
    def get_unhealthy_workers(self, health_report: Dict[str, Dict[str, Any]]) -> List[str]:
        return [task_id for task_id, health in health_report.items() if not health["is_healthy"]]
    
    def get_health_summary(self, health_report: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        total = len(health_report)
        healthy = sum(1 for h in health_report.values() if h["is_healthy"])
        return {"total_workers": total, "healthy": healthy, "unhealthy": total - healthy, "health_percentage": (healthy / total * 100) if total > 0 else 0}
