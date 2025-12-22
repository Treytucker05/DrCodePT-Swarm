from __future__ import annotations

import pytest

from agent.autonomous.retry_utils import RetryConfig, retry_with_backoff


def test_retry_succeeds_after_transient_failures() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("transient")
        return "ok"

    cfg = RetryConfig(max_attempts=5, initial_delay=0, max_delay=0, backoff_factor=1.0, transient_exceptions=(ValueError,))
    result = retry_with_backoff(
        _fn,
        max_attempts=cfg.max_attempts,
        initial_delay=cfg.initial_delay,
        max_delay=cfg.max_delay,
        backoff_factor=cfg.backoff_factor,
        transient_exceptions=cfg.transient_exceptions,
    )
    assert result == "ok"
    assert calls["count"] == 3


def test_retry_stops_after_max_attempts() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        raise ValueError("transient")

    cfg = RetryConfig(max_attempts=3, initial_delay=0, max_delay=0, backoff_factor=1.0, transient_exceptions=(ValueError,))
    with pytest.raises(ValueError):
        retry_with_backoff(
            _fn,
            max_attempts=cfg.max_attempts,
            initial_delay=cfg.initial_delay,
            max_delay=cfg.max_delay,
            backoff_factor=cfg.backoff_factor,
            transient_exceptions=cfg.transient_exceptions,
        )
    assert calls["count"] == 3


def test_retry_does_not_retry_non_transient() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        raise ValueError("fatal")

    cfg = RetryConfig(max_attempts=5, initial_delay=0, max_delay=0, backoff_factor=1.0, transient_exceptions=())
    with pytest.raises(ValueError):
        retry_with_backoff(
            _fn,
            max_attempts=cfg.max_attempts,
            initial_delay=cfg.initial_delay,
            max_delay=cfg.max_delay,
            backoff_factor=cfg.backoff_factor,
            transient_exceptions=cfg.transient_exceptions,
        )
    assert calls["count"] == 1
