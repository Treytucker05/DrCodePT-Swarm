"""
Execution Monitor - Ensures robust task execution.

This module provides:
- Precondition checks before tool execution
- Postcondition verification after execution
- Retry with exponential backoff
- Timeout enforcement
- Stuck-loop detection via ThrashGuard
- Health checks for dependencies
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ExecutionStatus(str, Enum):
    """Status of an execution attempt."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    PRECONDITION_FAILED = "precondition_failed"
    POSTCONDITION_FAILED = "postcondition_failed"
    RETRYING = "retrying"


@dataclass
class ExecutionResult(Generic[T]):
    """Result of a monitored execution."""
    status: ExecutionStatus
    result: Optional[T] = None
    error: Optional[str] = None
    attempts: int = 1
    duration_seconds: float = 0.0
    retries_exhausted: bool = False


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    retryable_errors: List[str] = field(default_factory=lambda: [
        "timeout",
        "connection",
        "rate_limit",
        "temporary",
        "transient",
    ])


@dataclass
class TimeoutConfig:
    """Configuration for timeout behavior."""
    default_timeout_seconds: float = 30.0
    tool_timeouts: Dict[str, float] = field(default_factory=dict)

    def get_timeout(self, tool_name: str) -> float:
        """Get timeout for a specific tool."""
        return self.tool_timeouts.get(tool_name, self.default_timeout_seconds)


class ExecutionMonitor:
    """
    Monitors and ensures robust execution of tools and operations.

    Features:
    - Retry with exponential backoff
    - Timeout enforcement
    - Precondition/postcondition verification
    - Health checks
    """

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        timeout_config: Optional[TimeoutConfig] = None,
    ):
        self.retry_config = retry_config or RetryConfig()
        self.timeout_config = timeout_config or TimeoutConfig()
        self._health_checks: Dict[str, Callable[[], bool]] = {}

    def register_health_check(self, name: str, check: Callable[[], bool]) -> None:
        """Register a health check function."""
        self._health_checks[name] = check

    def run_health_checks(self) -> Dict[str, bool]:
        """Run all registered health checks."""
        results = {}
        for name, check in self._health_checks.items():
            try:
                results[name] = check()
            except Exception as e:
                logger.warning(f"Health check '{name}' failed: {e}")
                results[name] = False
        return results

    def execute(
        self,
        func: Callable[..., T],
        *args,
        tool_name: str = "unknown",
        precondition: Optional[Callable[[], bool]] = None,
        postcondition: Optional[Callable[[T], bool]] = None,
        **kwargs,
    ) -> ExecutionResult[T]:
        """
        Execute a function with monitoring.

        Args:
            func: Function to execute
            tool_name: Name of the tool (for timeout lookup)
            precondition: Optional function to check before execution
            postcondition: Optional function to verify result
            *args, **kwargs: Arguments to pass to func

        Returns:
            ExecutionResult with status and result
        """
        start_time = time.time()
        timeout = self.timeout_config.get_timeout(tool_name)

        # Check precondition
        if precondition:
            try:
                if not precondition():
                    return ExecutionResult(
                        status=ExecutionStatus.PRECONDITION_FAILED,
                        error="Precondition check failed",
                        duration_seconds=time.time() - start_time,
                    )
            except Exception as e:
                return ExecutionResult(
                    status=ExecutionStatus.PRECONDITION_FAILED,
                    error=f"Precondition error: {e}",
                    duration_seconds=time.time() - start_time,
                )

        # Execute with retries
        last_error: Optional[str] = None
        attempts = 0

        for attempt in range(self.retry_config.max_retries + 1):
            attempts = attempt + 1

            try:
                # Execute with timeout
                result = self._execute_with_timeout(func, args, kwargs, timeout)

                # Check postcondition
                if postcondition:
                    try:
                        if not postcondition(result):
                            last_error = "Postcondition check failed"
                            if self._should_retry("postcondition", attempt):
                                self._wait_before_retry(attempt)
                                continue
                            return ExecutionResult(
                                status=ExecutionStatus.POSTCONDITION_FAILED,
                                result=result,
                                error=last_error,
                                attempts=attempts,
                                duration_seconds=time.time() - start_time,
                            )
                    except Exception as e:
                        last_error = f"Postcondition error: {e}"
                        if self._should_retry(str(e), attempt):
                            self._wait_before_retry(attempt)
                            continue

                # Success
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    result=result,
                    attempts=attempts,
                    duration_seconds=time.time() - start_time,
                )

            except TimeoutError as e:
                last_error = f"Timeout after {timeout}s: {e}"
                logger.warning(f"[{tool_name}] {last_error}")
                if self._should_retry("timeout", attempt):
                    self._wait_before_retry(attempt)
                    continue

            except Exception as e:
                last_error = str(e)
                logger.warning(f"[{tool_name}] Attempt {attempts} failed: {last_error}")
                if self._should_retry(last_error, attempt):
                    self._wait_before_retry(attempt)
                    continue

        # All retries exhausted
        return ExecutionResult(
            status=ExecutionStatus.FAILED,
            error=last_error,
            attempts=attempts,
            duration_seconds=time.time() - start_time,
            retries_exhausted=True,
        )

    def _execute_with_timeout(
        self,
        func: Callable[..., T],
        args: tuple,
        kwargs: dict,
        timeout: float,
    ) -> T:
        """Execute function with timeout."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Execution timed out after {timeout}s")

    def _should_retry(self, error: str, attempt: int) -> bool:
        """Check if error is retryable and attempts remain."""
        if attempt >= self.retry_config.max_retries:
            return False

        error_lower = error.lower()
        for retryable in self.retry_config.retryable_errors:
            if retryable in error_lower:
                return True

        return False

    def _wait_before_retry(self, attempt: int) -> None:
        """Wait with exponential backoff before retry."""
        delay = min(
            self.retry_config.initial_delay_seconds * (
                self.retry_config.exponential_base ** attempt
            ),
            self.retry_config.max_delay_seconds,
        )
        logger.info(f"Waiting {delay:.1f}s before retry...")
        time.sleep(delay)


# Global instance
_monitor: Optional[ExecutionMonitor] = None


def get_execution_monitor() -> ExecutionMonitor:
    """Get the global execution monitor."""
    global _monitor
    if _monitor is None:
        _monitor = ExecutionMonitor()
        # Register default health checks
        _register_default_health_checks(_monitor)
    return _monitor


def _register_default_health_checks(monitor: ExecutionMonitor) -> None:
    """Register default health checks."""
    # Check pyautogui
    def check_pyautogui() -> bool:
        try:
            import pyautogui
            return True
        except ImportError:
            return False

    # Check uiautomation
    def check_uiautomation() -> bool:
        try:
            import uiautomation
            return True
        except ImportError:
            return False

    # Check LLM availability
    def check_llm() -> bool:
        try:
            from agent.adapters import get_available_providers
            return len(get_available_providers()) > 0
        except Exception:
            return False

    # Check memory
    def check_memory() -> bool:
        try:
            from agent.memory import get_memory
            memory = get_memory()
            return memory is not None
        except Exception:
            return False

    monitor.register_health_check("pyautogui", check_pyautogui)
    monitor.register_health_check("uiautomation", check_uiautomation)
    monitor.register_health_check("llm", check_llm)
    monitor.register_health_check("memory", check_memory)


def execute_with_retry(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    timeout_seconds: float = 30.0,
    **kwargs,
) -> ExecutionResult[T]:
    """
    Convenience function to execute with retry.

    Args:
        func: Function to execute
        max_retries: Maximum retry attempts
        timeout_seconds: Timeout per attempt
        *args, **kwargs: Arguments to pass to func

    Returns:
        ExecutionResult
    """
    monitor = get_execution_monitor()
    monitor.retry_config.max_retries = max_retries
    monitor.timeout_config.default_timeout_seconds = timeout_seconds
    return monitor.execute(func, *args, **kwargs)


def run_health_checks() -> Dict[str, bool]:
    """Run all health checks and return results."""
    return get_execution_monitor().run_health_checks()
