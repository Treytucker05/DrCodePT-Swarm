"""Retry utilities for handling transient failures."""

import logging
import time
from typing import Callable, TypeVar, Any, Optional, Type, Tuple

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    transient_exceptions: Tuple[Type[Exception], ...] = (TimeoutError, ConnectionError, OSError),
    *args,
    **kwargs
) -> T:
    """Retry a function with exponential backoff."""
    last_exception: Optional[Exception] = None
    delay = initial_delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.debug(f"Attempt {attempt}/{max_attempts} for {func.__name__}")
            return func(*args, **kwargs)
        
        except transient_exceptions as exc:
            last_exception = exc
            
            if attempt >= max_attempts:
                logger.error(f"Failed after {max_attempts} attempts: {exc}", exc_info=True)
                raise
            
            logger.warning(f"Transient error on attempt {attempt}/{max_attempts}: {exc}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)
        
        except Exception as exc:
            logger.error(f"Non-transient error: {exc}", exc_info=True)
            raise
    
    if last_exception:
        raise last_exception


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(self, max_attempts: int = 3, initial_delay: float = 1.0, max_delay: float = 10.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    def retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic."""
        return retry_with_backoff(func, self.max_attempts, self.initial_delay, self.max_delay, self.backoff_factor, *args, **kwargs)


LLM_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay=2.0, max_delay=10.0, backoff_factor=2.0)
TOOL_RETRY_CONFIG = RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=5.0, backoff_factor=2.0)
WEB_RETRY_CONFIG = RetryConfig(max_attempts=3, initial_delay=1.0, max_delay=10.0, backoff_factor=2.0)
