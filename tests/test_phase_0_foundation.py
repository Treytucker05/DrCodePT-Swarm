from __future__ import annotations

import pytest

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.exceptions import (
    AgentException,
    ConfigurationError,
    DependencyError,
    InteractionRequiredError,
    LLMError,
    MemoryError,
    PlanningError,
    ReflectionError,
    ToolExecutionError,
)
from agent.autonomous.monitoring import ResourceMetrics, ResourceMonitor
from agent.autonomous.retry_utils import RetryConfig, retry_with_backoff
from agent.autonomous.runner import AgentRunner


def test_exception_hierarchy_and_context() -> None:
    cause = RuntimeError("boom")
    err = AgentException("failed", context={"step": "plan"}, original_exception=cause)
    assert err.message == "failed"
    assert err.context == {"step": "plan"}
    assert err.original_exception is cause
    for cls in (
        ToolExecutionError,
        PlanningError,
        MemoryError,
        LLMError,
        ConfigurationError,
        DependencyError,
        ReflectionError,
        InteractionRequiredError,
    ):
        assert issubclass(cls, AgentException)


def test_retry_success_first_attempt() -> None:
    result = retry_with_backoff(lambda: "ok", config=RetryConfig(max_attempts=2, initial_delay_s=0))
    assert result == "ok"


def test_retry_success_after_transient_failures() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        if calls["count"] < 3:
            raise TimeoutError("transient")
        return "ok"

    result = retry_with_backoff(
        _fn,
        config=RetryConfig(max_attempts=3, initial_delay_s=0),
        sleep_fn=lambda _delay: None,
    )
    assert result == "ok"
    assert calls["count"] == 3


def test_retry_failure_after_max_attempts() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        raise TimeoutError("transient")

    with pytest.raises(TimeoutError):
        retry_with_backoff(
            _fn,
            config=RetryConfig(max_attempts=2, initial_delay_s=0),
            sleep_fn=lambda _delay: None,
        )
    assert calls["count"] == 2


def test_retry_non_transient_fails_immediately() -> None:
    calls = {"count": 0}

    def _fn():
        calls["count"] += 1
        raise ValueError("fatal")

    with pytest.raises(ValueError):
        retry_with_backoff(
            _fn,
            config=RetryConfig(max_attempts=3, initial_delay_s=0),
            sleep_fn=lambda _delay: None,
        )
    assert calls["count"] == 1


def test_resource_monitoring_get_metrics_and_health() -> None:
    monitor = ResourceMonitor(psutil_module=False)
    metrics = monitor.get_metrics()
    assert isinstance(metrics, ResourceMetrics)
    assert metrics.memory_mb >= 0.0
    assert metrics.cpu_percent >= 0.0
    assert monitor.check_health(metrics) is True

    tight_monitor = ResourceMonitor(max_memory_mb=0.1, psutil_module=False)
    unhealthy = ResourceMetrics(memory_mb=10.0, cpu_percent=0.0, open_files=0, threads=0)
    assert tight_monitor.check_health(unhealthy) is False


class _FailingLLM:
    provider = "stub"
    model = "stub"

    def complete_json(self, prompt, *, schema_path, timeout_seconds=None):
        raise ValueError("boom")

    def reason_json(self, prompt, *, schema_path, timeout_seconds=None):
        raise ValueError("boom")


def test_runner_handles_llm_failure(tmp_path) -> None:
    llm = _FailingLLM()
    agent_cfg = AgentConfig(enable_web_gui=False, enable_desktop=False, memory_db_path=tmp_path / "mem.sqlite3")
    runner_cfg = RunnerConfig(
        max_steps=2,
        timeout_seconds=5,
        llm_max_retries=0,
        llm_retry_backoff_seconds=0.0,
        llm_plan_timeout_seconds=1,
        llm_plan_retry_timeout_seconds=1,
    )
    planner_cfg = PlannerConfig(mode="react")
    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        run_dir=tmp_path / "run",
    )
    result = runner.run(task="fail planning")
    assert result.success is False
    assert result.stop_reason == "llm_plan_timeout"
