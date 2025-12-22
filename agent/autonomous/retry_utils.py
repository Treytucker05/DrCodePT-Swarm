from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    initial_delay_s: float = 0.5
    max_delay_s: float = 4.0
    backoff_factor: float = 2.0
    jitter_s: float = 0.0

    def with_overrides(self, **kwargs: Any) -> "RetryConfig":
        return RetryConfig(**{**self.__dict__, **kwargs})


LLM_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay_s=0.5, max_delay_s=4.0, backoff_factor=2.0)
TOOL_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay_s=0.2, max_delay_s=2.0, backoff_factor=2.0)
WEB_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay_s=0.5, max_delay_s=3.0, backoff_factor=2.0)


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    config: RetryConfig,
    is_transient: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
    if config.max_attempts <= 0:
        raise ValueError("max_attempts must be > 0")
    delay = max(0.0, config.initial_delay_s)
    last_exc: Optional[Exception] = None
    for attempt in range(1, config.max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            transient = is_transient(exc) if is_transient else True
            if not transient or attempt >= config.max_attempts:
                raise
            if on_retry:
                on_retry(exc, attempt, delay)
            sleep_for = min(config.max_delay_s, delay)
            if config.jitter_s:
                sleep_for += config.jitter_s
            if sleep_for > 0:
                sleep_fn(sleep_for)
            delay = max(delay * config.backoff_factor, delay)
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_with_backoff exhausted without exception")
