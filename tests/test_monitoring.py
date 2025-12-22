from __future__ import annotations

from agent.autonomous.monitoring import ResourceMonitor


def test_monitoring_returns_metrics() -> None:
    monitor = ResourceMonitor()
    metrics = monitor.get_metrics()
    assert metrics.memory_mb >= 0
    assert metrics.cpu_percent >= 0


def test_monitoring_health_shape() -> None:
    monitor = ResourceMonitor()
    health = monitor.check_health()
    assert "healthy" in health
    assert "metrics" in health
    assert "warnings" in health
