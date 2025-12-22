from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for retry behavior.

    Args:
        max_attempts: Maximum number of attempts.
        initial_delay_s: Initial delay in seconds (alias: initial_delay).
        max_delay_s: Max delay in seconds (alias: max_delay).
        backoff_factor: Exponential backoff multiplier.

    Example:
        >>> RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=5.0)
    """

    max_attempts: int = 3
    initial_delay_s: float = 1.0
    max_delay_s: float = 5.0
    backoff_factor: float = 2.0

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_s: Optional[float] = None,
        max_delay_s: Optional[float] = None,
        backoff_factor: float = 2.0,
        *,
        initial_delay: Optional[float] = None,
        max_delay: Optional[float] = None,
    ) -> None:
        if initial_delay_s is None:
            initial_delay_s = 1.0 if initial_delay is None else float(initial_delay)
        elif initial_delay is not None and float(initial_delay_s) != float(initial_delay):
            raise ValueError("initial_delay and initial_delay_s must match")
        if max_delay_s is None:
            max_delay_s = 5.0 if max_delay is None else float(max_delay)
        elif max_delay is not None and float(max_delay_s) != float(max_delay):
            raise ValueError("max_delay and max_delay_s must match")
        object.__setattr__(self, "max_attempts", int(max_attempts))
        object.__setattr__(self, "initial_delay_s", float(initial_delay_s))
        object.__setattr__(self, "max_delay_s", float(max_delay_s))
        object.__setattr__(self, "backoff_factor", float(backoff_factor))

    @property
    def initial_delay(self) -> float:
        return self.initial_delay_s

    @property
    def max_delay(self) -> float:
        return self.max_delay_s

    def with_overrides(self, **kwargs: Any) -> "RetryConfig":
        if "initial_delay" in kwargs:
            if "initial_delay_s" in kwargs and kwargs["initial_delay"] != kwargs["initial_delay_s"]:
                raise ValueError("initial_delay and initial_delay_s must match")
            kwargs["initial_delay_s"] = kwargs.pop("initial_delay")
        if "max_delay" in kwargs:
            if "max_delay_s" in kwargs and kwargs["max_delay"] != kwargs["max_delay_s"]:
                raise ValueError("max_delay and max_delay_s must match")
            kwargs["max_delay_s"] = kwargs.pop("max_delay")
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
