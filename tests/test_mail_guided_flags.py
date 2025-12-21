import json
from pathlib import Path

from agent.autonomous.modes import mail_guided


def test_mail_guided_no_create_flag(monkeypatch, tmp_path):
    run_dir = tmp_path / "runs" / "test_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "mail_report.md").write_text("# report\n", encoding="utf-8")
    (run_dir / "mail_plan.json").write_text(
        json.dumps({"rules": [{"name": "r1", "planned_moves": []}]}),
        encoding="utf-8",
    )

    captured = {"args": []}

    def _fake_run_executor(args, **_kwargs):
        captured["args"].append(list(args))
        class _Proc:
            stdout = ""
            stderr = ""
            returncode = 0
        return _Proc()

    monkeypatch.setattr(mail_guided, "_run_executor", _fake_run_executor)
    monkeypatch.setattr(mail_guided, "_newest_run_dir", lambda: run_dir)
    monkeypatch.setattr(
        mail_guided,
        "_run_codex_json",
        lambda *args, **kwargs: {"questions": [], "rationale": ""},
    )
    monkeypatch.setattr(mail_guided, "_planned_moves_count", lambda _plan: 0)

    mail_guided.run_mail_guided("Execute. Do not create folders.")

    assert captured["args"], "expected executor calls"
    assert "--no-create-folders" in captured["args"][0]
