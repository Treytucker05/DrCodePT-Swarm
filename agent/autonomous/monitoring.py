from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

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
    psutil_available: bool = False
    rss_bytes: int = 0
    vms_bytes: int = 0
    num_threads: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "open_files": self.open_files,
            "threads": self.threads,
            "psutil_available": self.psutil_available,
            "rss_bytes": self.rss_bytes,
            "vms_bytes": self.vms_bytes,
            "num_threads": self.num_threads,
        }


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
        log_interval_s: float = 0.0,
        health_check_steps: int = 10,
        max_observations: int = 1000,
        keep_last_observations: int = 1000,
        psutil_module=None,
        time_fn=time.monotonic,
    ) -> None:
        self.max_memory_mb = max_memory_mb
        self.max_threads = max_threads
        self.max_open_files = max_open_files
        self.log_interval_s = log_interval_s
        self.health_check_steps = health_check_steps
        self.max_observations = max_observations
        self.keep_last_observations = keep_last_observations
        self._time_fn = time_fn
        self._last_log_ts = 0.0
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
        except ImportError as exc:
            logger.info("psutil not installed; resource monitoring limited: %s", exc)
            return None
        except Exception as exc:
            logger.warning("psutil import failed: %s", exc)
            return None

    def snapshot(self) -> ResourceMetrics:
        if self._process is None:
            threads = threading.active_count()
            return ResourceMetrics(
                memory_mb=0.0,
                cpu_percent=0.0,
                open_files=0,
                threads=threads,
                psutil_available=False,
                rss_bytes=0,
                vms_bytes=0,
                num_threads=threads,
            )
        memory_mb = 0.0
        cpu_percent = 0.0
        open_files = 0
        threads = 0
        rss_bytes = 0
        vms_bytes = 0
        num_threads = 0
        try:
            mem_info = self._process.memory_info()
            rss_bytes = int(getattr(mem_info, "rss", 0) or 0)
            vms_bytes = int(getattr(mem_info, "vms", 0) or 0)
            memory_mb = float(rss_bytes) / (1024 * 1024)
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
            num_threads = int(self._process.num_threads())
            threads = num_threads
        except Exception as exc:
            logger.debug("Failed to read thread count: %s", exc)
            threads = threading.active_count()
            num_threads = threads
        return ResourceMetrics(
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            open_files=open_files,
            threads=threads,
            psutil_available=True,
            rss_bytes=rss_bytes,
            vms_bytes=vms_bytes,
            num_threads=num_threads,
        )

    def get_metrics(self) -> ResourceMetrics:
        return self.snapshot()

    def check_health(self, metrics: Optional[ResourceMetrics] = None) -> bool:
        metrics = metrics or self.snapshot()
        if metrics.memory_mb > self.max_memory_mb:
            return False
        if metrics.threads > self.max_threads:
            return False
        if metrics.open_files > self.max_open_files:
            return False
        return True

    def log_metrics(self, metrics: Optional[ResourceMetrics] = None) -> None:
        metrics = metrics or self.snapshot()
        logger.debug(
            "resource_metrics memory_mb=%.2f cpu=%.2f open_files=%d threads=%d psutil=%s",
            metrics.memory_mb,
            metrics.cpu_percent,
            metrics.open_files,
            metrics.threads,
            metrics.psutil_available,
        )

    def _trim_observations(self, state) -> int:
        if self.max_observations <= 0:
            return 0
        total = len(state.observations)
        if total <= self.max_observations:
            return 0
        keep_last = min(max(1, self.keep_last_observations), self.max_observations)
        state.observations = state.observations[-keep_last:]
        return total - len(state.observations)

    def tick(self, *, step_index: int, state, tracer) -> None:
        metrics = self.snapshot()
        now = self._time_fn()
        log_every = self.log_interval_s
        if log_every <= 0 or (now - self._last_log_ts) >= log_every:
            self.log_metrics(metrics)
            if tracer is not None:
                tracer.log({"type": "resource", "kind": "periodic", "metrics": metrics.to_dict()})
            self._last_log_ts = now
        if self.health_check_steps and step_index % self.health_check_steps == 0:
            trimmed = self._trim_observations(state)
            ok = self.check_health(metrics)
            payload = {
                "type": "resource",
                "kind": "health_check",
                "ok": ok,
                "trimmed_observations": trimmed,
                "metrics": metrics.to_dict(),
            }
            if tracer is not None:
                tracer.log(payload)
            if not ok:
                logger.warning("Resource limits exceeded: %s", payload)
