from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behavior.

    Example:
        >>> RetryConfig(max_attempts=3, initial_delay_s=1.0, max_delay_s=5.0)
    """

    max_attempts: int = 3
    initial_delay_s: float = 1.0
    max_delay_s: float = 5.0
    backoff_factor: float = 2.0

    def with_overrides(self, **kwargs: Any) -> "RetryConfig":
        return RetryConfig(**{**self.__dict__, **kwargs})


LLM_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay_s=2.0, max_delay_s=10.0, backoff_factor=2.0)
TOOL_RETRY_CONFIG = RetryConfig(max_attempts=2, initial_delay_s=1.0, max_delay_s=5.0, backoff_factor=2.0)
WEB_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay_s=1.0, max_delay_s=10.0, backoff_factor=2.0)


def _default_is_transient(exc: Exception) -> bool:
    return isinstance(exc, (TimeoutError, ConnectionError, OSError))


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    config: RetryConfig,
    is_transient: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
    """Retry a callable with exponential backoff.

    Retries only on transient errors by default (TimeoutError, ConnectionError, OSError).

    Example:
        >>> retry_with_backoff(lambda: "ok", config=RetryConfig(max_attempts=1))
        'ok'
    """

    if config.max_attempts <= 0:
        raise ValueError("max_attempts must be > 0")
    delay = max(0.0, config.initial_delay_s)
    last_exc: Optional[Exception] = None
    transient_check = is_transient or _default_is_transient

    for attempt in range(1, config.max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if not transient_check(exc) or attempt >= config.max_attempts:
                raise
            if on_retry:
                on_retry(exc, attempt, delay)
            sleep_for = min(config.max_delay_s, delay)
            if sleep_for > 0:
                sleep_fn(sleep_for)
            delay = max(delay * config.backoff_factor, delay)

    if last_exc:
        raise last_exc
    raise RuntimeError("retry_with_backoff exhausted without exception")
