import os
import subprocess

from agent import treys_agent


def test_mail_prefix_routes_to_workflow(monkeypatch) -> None:
    captured = {}

    def _fake_run(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        class _Result:
            returncode = 0
        return _Result()

    monkeypatch.setattr(subprocess, "run", _fake_run)

    routed = treys_agent._maybe_route_mail(
        "Mail task: Continue consolidation using saved rule deliveries_to_shopping_online_small_merge..."
    )

    assert routed is True
    cmd = captured["args"][0]
    assert cmd[:3] == [treys_agent.sys.executable, "-m", "agent.autonomous.modes.mail_guided"]
    assert "--objective" in cmd
    obj_index = cmd.index("--objective") + 1
    assert cmd[obj_index] == "Continue consolidation using saved rule deliveries_to_shopping_online_small_merge..."
    assert captured["kwargs"]["cwd"] == str(treys_agent.Path(treys_agent.__file__).resolve().parents[1])
    env = captured["kwargs"]["env"]
    assert str(treys_agent.Path(treys_agent.__file__).resolve().parents[1]) in env["PYTHONPATH"].split(os.pathsep)
