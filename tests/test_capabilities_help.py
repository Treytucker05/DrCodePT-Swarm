from agent import treys_agent


def test_capability_help_routing(monkeypatch, capsys):
    captured = {"called": False}

    def _fake_run():
        captured["called"] = True
        print("Team Think Mail")

    monkeypatch.setattr(treys_agent, "_run_capabilities", _fake_run)
    monkeypatch.setattr(
        treys_agent,
        "mode_autonomous",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not execute tools")),
        raising=False,
    )

    assert treys_agent._is_capability_query("What can you help me with?") is True
    treys_agent._run_capabilities()

    out = capsys.readouterr().out
    assert captured["called"] is True
    assert "Team" in out and "Think" in out and "Mail" in out
