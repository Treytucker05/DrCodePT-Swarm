from __future__ import annotations

import sys
import threading
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional, TextIO


@dataclass
class Spinner(AbstractContextManager):
    label: str = "Working"
    interval_seconds: float = 0.15
    stream: Optional[TextIO] = None

    def __post_init__(self) -> None:
        if self.stream is None:
            self.stream = sys.stdout
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._start_time = 0.0

    def _run(self) -> None:
        frames = ["|", "/", "-", "\\"]
        idx = 0
        while not self._stop.is_set():
            elapsed = int(time.time() - self._start_time)
            msg = f"\r[{self.label}] {frames[idx]} {elapsed:>3}s"
            try:
                assert self.stream is not None
                self.stream.write(msg)
                self.stream.flush()
            except Exception:
                pass
            idx = (idx + 1) % len(frames)
            self._stop.wait(self.interval_seconds)

        # Clear line
        try:
            assert self.stream is not None
            self.stream.write("\r" + (" " * 60) + "\r")
            self.stream.flush()
        except Exception:
            pass

    def __enter__(self) -> "Spinner":
        self._start_time = time.time()
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self._stop.set()
        self._thread.join(timeout=1)


__all__ = ["Spinner"]

