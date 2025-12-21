import json
from pathlib import Path

from agent.autonomous.modes import mail_guided
from agent.memory.procedures.mail_yahoo import MailProcedure


def test_folder_merge_saves_mapping_and_skips_planner(monkeypatch, tmp_path):
    run_dir = tmp_path / "runs" / "test_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "mail_report.md").write_text(
        "## Folders (3)\n- Deliveries\n- Personal\n- Work\n\n", encoding="utf-8"
    )
    (run_dir / "mail_plan.json").write_text(
        json.dumps({"rules": [{"name": "merge", "planned_moves": []}]}),
        encoding="utf-8",
    )
    (run_dir / "answers.json").write_text(
        json.dumps(
            {"answers": {"q1": "Work, Personal", "q2": "none"}, "missing_required": []}
        ),
        encoding="utf-8",
    )

    def _fake_run_executor(_args, **_kwargs):
        class _Proc:
            stdout = ""
            stderr = ""
            returncode = 0

        return _Proc()

    saved = {}

    def _fake_save(proc):
        saved["proc"] = proc

    def _fake_codex(prompt, schema, **_kwargs):
        if "FolderGrouper" in prompt:
            return {
                "targets": ["Work", "Personal"],
                "mapping": {"Deliveries": "Work", "Personal": "Personal", "Work": "Work"},
            }
        if "Planner" in prompt:
            raise AssertionError("Planner should not run for folder consolidation")
        return {"questions": [], "rationale": ""}

    monkeypatch.setattr(mail_guided, "_run_executor", _fake_run_executor)
    monkeypatch.setattr(mail_guided, "_newest_run_dir", lambda: run_dir)
    monkeypatch.setattr(mail_guided, "load_procedure", lambda: MailProcedure())
    monkeypatch.setattr(mail_guided, "save_procedure", _fake_save)
    monkeypatch.setattr(mail_guided, "_run_codex_json", _fake_codex)

    mail_guided.run_mail_guided("Help me consolidate folders")

    assert "proc" in saved, "expected save_procedure to be called"
    proc = saved["proc"]
    assert proc.folder_merge_mapping.get("Deliveries") == "Work"
    assert proc.folder_merge_rules, "expected folder_merge_rules"
    assert proc.rules == []
