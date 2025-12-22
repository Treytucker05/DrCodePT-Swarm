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

    result = retry_with_backoff(
        _fn,
        config=RetryConfig(max_attempts=5, initial_delay_s=0),
        is_transient=lambda exc: isinstance(exc, ValueError),
        sleep_fn=lambda _delay: None,
    )
    assert result == "ok"
    assert calls["count"] == 3


def test_retry_stops_after_max_attempts() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        raise ValueError("transient")

    with pytest.raises(ValueError):
        retry_with_backoff(
            _fn,
            config=RetryConfig(max_attempts=3, initial_delay_s=0),
            is_transient=lambda exc: isinstance(exc, ValueError),
            sleep_fn=lambda _delay: None,
        )
    assert calls["count"] == 3


def test_retry_does_not_retry_non_transient() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        raise ValueError("fatal")

    with pytest.raises(ValueError):
        retry_with_backoff(
            _fn,
            config=RetryConfig(max_attempts=5, initial_delay_s=0),
            is_transient=lambda exc: False,
            sleep_fn=lambda _delay: None,
        )
    assert calls["count"] == 1
