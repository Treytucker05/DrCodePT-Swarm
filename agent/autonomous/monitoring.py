from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResourceMetrics:
    """Snapshot of resource usage.

    Example:
        >>> metrics = ResourceMetrics(memory_mb=10.0, cpu_percent=1.0, open_files=5, threads=2)
    """

    memory_mb: float
    cpu_percent: float
    open_files: int
    threads: int


class ResourceMonitor:
    """Monitor process resources with optional psutil support.

    Example:
        >>> monitor = ResourceMonitor()
        >>> metrics = monitor.get_metrics()
        >>> monitor.check_health(metrics)
    """

    def __init__(
        self,
        *,
        max_memory_mb: float = 4096.0,
        max_threads: int = 200,
        max_open_files: int = 10_000,
        psutil_module=None,
    ) -> None:
        self.max_memory_mb = max_memory_mb
        self.max_threads = max_threads
        self.max_open_files = max_open_files
        self._psutil = self._load_psutil(psutil_module)
        self._process = None
        if self._psutil is not None:
            try:
                self._process = self._psutil.Process(os.getpid())
            except Exception as exc:
                logger.warning("Failed to initialize psutil process: %s", exc)
                self._process = None

    @staticmethod
    def _load_psutil(psutil_module):
        if psutil_module is False:
            return None
        if psutil_module is not None:
            return psutil_module
        try:
            import psutil  # type: ignore

            return psutil
        except ImportError:
            logger.info("psutil not installed; resource monitoring limited")
            return None
        except Exception as exc:
            logger.warning("psutil import failed: %s", exc)
            return None

    def get_metrics(self) -> ResourceMetrics:
        if self._process is None:
            return ResourceMetrics(
                memory_mb=0.0,
                cpu_percent=0.0,
                open_files=0,
                threads=threading.active_count(),
            )
        memory_mb = 0.0
        cpu_percent = 0.0
        open_files = 0
        threads = 0
        try:
            mem_info = self._process.memory_info()
            memory_mb = float(getattr(mem_info, "rss", 0)) / (1024 * 1024)
        except Exception as exc:
            logger.debug("Failed to read memory info: %s", exc)
        try:
            cpu_percent = float(self._process.cpu_percent(interval=None))
        except Exception as exc:
            logger.debug("Failed to read cpu percent: %s", exc)
        try:
            open_files = len(self._process.open_files())
        except Exception as exc:
            logger.debug("Failed to read open files: %s", exc)
        try:
            threads = int(self._process.num_threads())
        except Exception as exc:
            logger.debug("Failed to read thread count: %s", exc)
        return ResourceMetrics(
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            open_files=open_files,
            threads=threads,
        )

    def check_health(self, metrics: Optional[ResourceMetrics] = None) -> bool:
        metrics = metrics or self.get_metrics()
        if metrics.memory_mb > self.max_memory_mb:
            return False
        if metrics.threads > self.max_threads:
            return False
        if metrics.open_files > self.max_open_files:
            return False
        return True

    def log_metrics(self, metrics: Optional[ResourceMetrics] = None) -> None:
        metrics = metrics or self.get_metrics()
        logger.debug(
            "resource_metrics memory_mb=%.2f cpu=%.2f open_files=%d threads=%d",
            metrics.memory_mb,
            metrics.cpu_percent,
            metrics.open_files,
            metrics.threads,
        )
