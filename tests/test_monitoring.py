from __future__ import annotations

from types import SimpleNamespace

from agent.autonomous.monitoring import ResourceMonitor
from agent.autonomous.state import AgentState
from agent.autonomous.models import Observation


class _DummyTracer:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def log(self, payload) -> None:
        self.events.append(payload)


def _make_state(count: int) -> AgentState:
    state = AgentState(task="t")
    for idx in range(count):
        state.add_observation(Observation(source="test", raw=str(idx), salient_facts=[str(idx)]))
    return state


def test_monitoring_logs_and_trims() -> None:
    tracer = _DummyTracer()
    state = _make_state(50)
    monitor = ResourceMonitor(
        log_interval_s=0,
        health_check_steps=1,
        max_observations=10,
        keep_last_observations=5,
        psutil_module=False,
    )

    monitor.tick(step_index=1, state=state, tracer=tracer)

    assert len(state.observations) <= 10
    kinds = [e.get("kind") for e in tracer.events if e.get("type") == "resource"]
    assert "periodic" in kinds
    assert "health_check" in kinds
    health = next(e for e in tracer.events if e.get("kind") == "health_check")
    assert "trimmed_observations" in health


def test_monitoring_uses_psutil_stub() -> None:
    class _FakeProcess:
        def memory_info(self):
            return SimpleNamespace(rss=123, vms=456)

        def num_threads(self):
            return 7

        def cpu_percent(self, interval=None):
            return 1.5

        def open_files(self):
            return []

    class _FakePsutil:
        def Process(self, _pid):
            return _FakeProcess()

    monitor = ResourceMonitor(psutil_module=_FakePsutil(), log_interval_s=0, health_check_steps=0)
    metrics = monitor.snapshot()
    assert metrics.psutil_available is True
    assert metrics.rss_bytes == 123
    assert metrics.vms_bytes == 456
    assert metrics.num_threads == 7
