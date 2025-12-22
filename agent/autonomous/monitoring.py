"""Resource monitoring and health checks."""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    memory_mb: float
    cpu_percent: float
    open_files: int
    threads: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "open_files": self.open_files,
            "threads": self.threads,
        }


class ResourceMonitor:
    """Monitor system resources during agent execution."""
    
    def __init__(self, memory_limit_mb: float = 1024):
        self.memory_limit_mb = memory_limit_mb
        self.psutil = None
        self.process = None
        self._try_import_psutil()
    
    def _try_import_psutil(self) -> None:
        try:
            import psutil
            self.psutil = psutil
            self.process = psutil.Process()
            logger.info("✓ psutil available for resource monitoring")
        except ImportError:
            logger.warning("✗ psutil not installed; resource monitoring disabled")
    
    def get_metrics(self) -> ResourceMetrics:
        if not self.psutil or not self.process:
            return ResourceMetrics(0, 0, 0, 0)
        
        try:
            mem_info = self.process.memory_info()
            memory_mb = mem_info.rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.1)
            open_files = len(self.process.open_files())
            threads = self.process.num_threads()
            return ResourceMetrics(memory_mb, cpu_percent, open_files, threads)
        except Exception as exc:
            logger.error(f"Error getting resource metrics: {exc}")
            return ResourceMetrics(0, 0, 0, 0)
    
    def check_health(self) -> Dict[str, Any]:
        metrics = self.get_metrics()
        health = {"healthy": True, "metrics": metrics.to_dict(), "warnings": []}
        
        if metrics.memory_mb > self.memory_limit_mb:
            health["healthy"] = False
            health["warnings"].append(f"Memory usage {metrics.memory_mb:.1f}MB exceeds limit {self.memory_limit_mb}MB")
        
        if metrics.open_files > 100:
            health["warnings"].append(f"High number of open files: {metrics.open_files}")
        
        if metrics.threads > 50:
            health["warnings"].append(f"High number of threads: {metrics.threads}")
        
        return health
    
    def log_metrics(self) -> None:
        metrics = self.get_metrics()
        if metrics.memory_mb > 0:
            logger.debug(f"Resources: {metrics.memory_mb:.1f}MB memory, {metrics.cpu_percent:.1f}% CPU, {metrics.open_files} files, {metrics.threads} threads")
