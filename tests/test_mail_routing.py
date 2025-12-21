from agent import treys_agent


def test_mail_prefix_routes_to_workflow(monkeypatch) -> None:
    captured = {}

    def _fake_run(objective: str) -> None:
        captured["objective"] = objective

    monkeypatch.setattr(treys_agent, "_run_mail_guided", _fake_run)

    routed = treys_agent._maybe_route_mail(
        "Mail task: Continue consolidation using saved rule deliveries_to_shopping_online_small_merge..."
    )

    assert routed is True
    assert (
        captured["objective"]
        == "Continue consolidation using saved rule deliveries_to_shopping_online_small_merge..."
    )
