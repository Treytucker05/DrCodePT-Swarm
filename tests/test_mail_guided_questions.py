import json
from pathlib import Path

from agent.autonomous.modes import mail_guided


def test_mail_guided_blocks_until_answers(monkeypatch, tmp_path):
    run_dir = tmp_path / "runs" / "test_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "mail_report.md").write_text("# report\n", encoding="utf-8")

    def _fake_run_executor(_args, **_kwargs):
        class _Proc:
            stdout = ""
            stderr = ""
            returncode = 0
        return _Proc()

    monkeypatch.setattr(mail_guided, "_run_executor", _fake_run_executor)
    monkeypatch.setattr(mail_guided, "_newest_run_dir", lambda: run_dir)

    calls = {"planner": 0}

    def _fake_codex(prompt, schema, **_kwargs):
        if "Questioner" in prompt:
            return {"questions": ["Q1?", "Q2?"], "rationale": "need info"}
        if "AnswerParser" in prompt:
            return {"answers": {"q1": "A1", "q2": "A2"}, "missing_required": []}
        if "Planner" in prompt:
            calls["planner"] += 1
            return {
                "procedure": mail_guided.load_procedure().model_dump(),
                "summary": "ok",
            }
        return {}

    monkeypatch.setattr(mail_guided, "_run_codex_json", _fake_codex)
    monkeypatch.setattr(mail_guided, "_planned_moves_count", lambda _plan: 0)

    mail_guided.run_mail_guided("Plan something")

    questions_path = run_dir / "questions.json"
    assert questions_path.is_file()
    assert calls["planner"] == 0

    (run_dir / "mail_plan.json").write_text(
        json.dumps({"rules": [{"name": "r1", "planned_moves": []}]}),
        encoding="utf-8",
    )
    inputs = iter(["A1", "A2", "continue"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

    mail_guided.run_mail_guided("Plan something")

    assert calls["planner"] == 0

    mail_guided.run_mail_guided("Plan something")

    assert calls["planner"] == 1
