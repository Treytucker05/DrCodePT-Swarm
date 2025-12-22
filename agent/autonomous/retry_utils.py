"""Retry utilities for handling transient failures."""

import logging
import time
from typing import Callable, TypeVar, Optional, Type, Tuple

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    transient_exceptions: Tuple[Type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
        OSError,
    ),
    *args,
    **kwargs
) -> T:
    """Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 10.0)
        backoff_factor: Multiplier for delay between attempts (default: 2.0)
        transient_exceptions: Tuple of exception types to retry on
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func

    Raises:
        The last exception if all attempts fail
    """
    last_exception: Optional[Exception] = None
    delay = initial_delay

    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(
                f"Attempt {attempt}/{max_attempts} for {func.__name__}",
                extra={"attempt": attempt, "max_attempts": max_attempts},
            )
            return func(*args, **kwargs)

        except transient_exceptions as exc:
            last_exception = exc

            if attempt >= max_attempts:
                logger.error(
                    f"Failed after {max_attempts} attempts: {exc}",
                    exc_info=True,
                    extra={"attempts": max_attempts, "error": str(exc)},
                )
                raise

            logger.warning(
                f"Transient error on attempt {attempt}/{max_attempts}: {exc}. "
                f"Retrying in {delay:.1f}s...",
                extra={
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "delay": delay,
                    "error": str(exc),
                },
            )
            time.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)

        except Exception as exc:
            logger.error(
                f"Non-transient error: {exc}",
                exc_info=True,
                extra={"error_type": type(exc).__name__},
            )
            raise

    if last_exception:
        raise last_exception


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
        transient_exceptions: Tuple[Type[Exception], ...] = (
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.transient_exceptions = transient_exceptions

    def retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic."""
        return retry_with_backoff(
            func,
            max_attempts=self.max_attempts,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
            backoff_factor=self.backoff_factor,
            transient_exceptions=self.transient_exceptions,
            *args,
            **kwargs,
        )


# Pre-configured retry policies
LLM_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=2.0,
    max_delay=10.0,
    backoff_factor=2.0,
)

TOOL_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    initial_delay=1.0,
    max_delay=5.0,
    backoff_factor=2.0,
)

WEB_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    backoff_factor=2.0,
)
