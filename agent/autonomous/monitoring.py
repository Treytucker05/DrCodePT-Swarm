from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .state import AgentState


@dataclass(frozen=True)
class ResourceMetrics:
    timestamp: float
    pid: int
    rss_bytes: Optional[int] = None
    vms_bytes: Optional[int] = None
    num_threads: Optional[int] = None
    cpu_percent: Optional[float] = None
    open_files: Optional[int] = None
    psutil_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "pid": self.pid,
            "rss_bytes": self.rss_bytes,
            "vms_bytes": self.vms_bytes,
            "num_threads": self.num_threads,
            "cpu_percent": self.cpu_percent,
            "open_files": self.open_files,
            "psutil_available": self.psutil_available,
        }


def _load_psutil(psutil_module):
    if psutil_module is False:
        return None
    if psutil_module is not None:
        return psutil_module
    try:
        import psutil  # type: ignore

        return psutil
    except Exception:
        return None


class ResourceMonitor:
    def __init__(
        self,
        *,
        log_interval_s: float = 30.0,
        health_check_steps: int = 10,
        max_observations: int = 200,
        keep_last_observations: int = 40,
        psutil_module=None,
        time_fn=time.monotonic,
    ) -> None:
        self.log_interval_s = max(0.0, float(log_interval_s))
        self.health_check_steps = max(0, int(health_check_steps))
        self.max_observations = max(1, int(max_observations))
        self.keep_last_observations = max(1, int(keep_last_observations))
        self._time_fn = time_fn
        self._last_log = 0.0

        self._psutil = _load_psutil(psutil_module)
        self._process = None
        if self._psutil is not None:
            try:
                self._process = self._psutil.Process(os.getpid())
            except Exception:
                self._process = None

    @property
    def psutil_available(self) -> bool:
        return self._process is not None

    def snapshot(self) -> ResourceMetrics:
        pid = os.getpid()
        now = time.time()
        if self._process is None:
            return ResourceMetrics(
                timestamp=now,
                pid=pid,
                num_threads=threading.active_count(),
                psutil_available=False,
            )
        rss = vms = None
        cpu = None
        threads = None
        open_files = None
        try:
            mem = self._process.memory_info()
            rss = int(getattr(mem, "rss", 0) or 0)
            vms = int(getattr(mem, "vms", 0) or 0)
        except Exception:
            pass
        try:
            threads = int(self._process.num_threads())
        except Exception:
            pass
        try:
            cpu = float(self._process.cpu_percent(interval=None))
        except Exception:
            pass
        try:
            open_files = len(self._process.open_files())
        except Exception:
            open_files = None
        return ResourceMetrics(
            timestamp=now,
            pid=pid,
            rss_bytes=rss,
            vms_bytes=vms,
            num_threads=threads,
            cpu_percent=cpu,
            open_files=open_files,
            psutil_available=True,
        )

    def _should_log(self, now: float) -> bool:
        if self.log_interval_s <= 0:
            return True
        return (now - self._last_log) >= self.log_interval_s

    def _trim_observations(self, state: AgentState) -> Optional[Dict[str, int]]:
        count = len(state.observations)
        if count <= self.max_observations:
            return None
        state.compact(keep_last=self.keep_last_observations, max_total=self.max_observations)
        return {"before": count, "after": len(state.observations)}

    def tick(self, *, step_index: int, state: AgentState, tracer) -> None:
        now = self._time_fn()
        if self._should_log(now):
            metrics = self.snapshot()
            tracer.log(
                {
                    "type": "resource",
                    "kind": "periodic",
                    "step_index": step_index,
                    "metrics": metrics.to_dict(),
                }
            )
            self._last_log = now

        if self.health_check_steps and step_index > 0 and step_index % self.health_check_steps == 0:
            trimmed = self._trim_observations(state)
            metrics = self.snapshot()
            payload = {
                "type": "resource",
                "kind": "health_check",
                "step_index": step_index,
                "metrics": metrics.to_dict(),
            }
            if trimmed:
                payload["trimmed_observations"] = trimmed
            tracer.log(payload)
