"""Health monitoring for worker processes."""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from agent.autonomous.workers.process_worker import ProcessWorker

logger = logging.getLogger(__name__)


class WorkerHealthMonitor:
    """Monitor health of worker processes.
    
    Tracks worker status, detects stalled workers, and provides
    health reports for the worker pool.
    """
    
    def __init__(self, check_interval: int = 10, stall_timeout: int = 300):
        """Initialize health monitor.
        
        Args:
            check_interval: Seconds between health checks
            stall_timeout: Seconds before marking worker as stalled
        """
        self.check_interval = check_interval
        self.stall_timeout = stall_timeout
        self.health_history: Dict[str, List[Dict[str, Any]]] = {}
        logger.info(
            f"WorkerHealthMonitor initialized (interval={check_interval}s, "
            f"stall_timeout={stall_timeout}s)"
        )
    
    def check_worker_health(self, worker: ProcessWorker) -> Dict[str, Any]:
        """Check health of a worker.
        
        Args:
            worker: ProcessWorker instance
        
        Returns:
            Health status dict
        """
        health = {
            "task_id": worker.task_id,
            "status": worker.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issues": [],
            "is_healthy": True,
        }
        
        if not worker.process:
            health["issues"].append("No process")
            health["is_healthy"] = False
            return health
        
        # Check if process is still running
        if worker.process.poll() is not None:
            health["status"] = "completed"
            return health
        
        # Check for stalled worker (no result file update)
        if worker.start_time:
            elapsed = time.time() - worker.start_time
            if elapsed > self.stall_timeout:
                health["issues"].append(
                    f"Stalled for {elapsed:.0f}s (timeout: {self.stall_timeout}s)"
                )
                health["is_healthy"] = False
        
        # Try to get result (indicates progress)
        result = worker.get_result()
        if result:
            health["has_result"] = True
        
        return health
    
    def monitor_all(self, workers: Dict[str, ProcessWorker]) -> Dict[str, Dict[str, Any]]:
        """Monitor all workers.
        
        Args:
            workers: Dict mapping task_id -> ProcessWorker
        
        Returns:
            Dict mapping task_id -> health status
        """
        health_report = {}
        
        for task_id, worker in workers.items():
            health = self.check_worker_health(worker)
            health_report[task_id] = health
            
            # Track history
            if task_id not in self.health_history:
                self.health_history[task_id] = []
            
            self.health_history[task_id].append(health)
        
        return health_report
    
    def get_unhealthy_workers(self, health_report: Dict[str, Dict[str, Any]]) -> List[str]:
        """Get list of unhealthy workers.
        
        Args:
            health_report: Health report from monitor_all()
        
        Returns:
            List of unhealthy task IDs
        """
        unhealthy = []
        
        for task_id, health in health_report.items():
            if not health["is_healthy"]:
                unhealthy.append(task_id)
        
        return unhealthy
    
    def get_health_summary(self, health_report: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of worker health.
        
        Args:
            health_report: Health report from monitor_all()
        
        Returns:
            Summary dict
        """
        total = len(health_report)
        healthy = sum(1 for h in health_report.values() if h["is_healthy"])
        unhealthy = total - healthy
        
        return {
            "total_workers": total,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "health_percentage": (healthy / total * 100) if total > 0 else 0,
        }
