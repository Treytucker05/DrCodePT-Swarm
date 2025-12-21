import json
import sys
from pathlib import Path

import pytest

from agent.memory.procedures.mail_yahoo import MailProcedure, MoveRule


class DummyIMAP:
    def __init__(self, *args, **kwargs):
        pass

    def login(self, *_args, **_kwargs):
        return ("OK", [])

    def logout(self):
        return ("OK", [])


def _run_executor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, procedure, search_map):
    import agent.autonomous.tools.mail_yahoo_imap_executor as executor

    monkeypatch.setattr(executor, "load_procedure", lambda: procedure)
    monkeypatch.setattr(executor, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(executor, "_run_id", lambda: "test_run")
    monkeypatch.setattr(executor, "_load_creds", lambda: ("u", "p", "test"))
    monkeypatch.setattr(executor.imaplib, "IMAP4_SSL", DummyIMAP)
    monkeypatch.setattr(executor, "list_folders", lambda _imap: list(search_map.keys()))

    def fake_search(_imap, folder, _criteria):
        return search_map.get(folder, [])

    monkeypatch.setattr(executor, "search_uids", fake_search)

    argv = [
        "prog",
        "--dry-run",
        "--max-per-rule",
        "1",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    code = executor.main()
    assert code == 0
    plan_path = tmp_path / "runs" / "test_run" / "mail_plan.json"
    return json.loads(plan_path.read_text(encoding="utf-8"))


def test_plans_moves_from_search_folders(tmp_path, monkeypatch):
    rule = MoveRule(
        name="amazon_to_agenttest",
        to_folder="AgentTest",
        from_contains=["amazon"],
        search_folders=["Deliveries"],
        max_messages=1,
    )
    proc = MailProcedure(target_folders=["AgentTest"], rules=[rule])
    search_map = {
        "Deliveries": ["1", "2", "3", "4"],
        "INBOX": [],
    }
    plan = _run_executor(tmp_path, monkeypatch, proc, search_map)
    planned_moves = plan["rules"][0].get("planned_moves")
    assert planned_moves, "expected planned_moves"
    assert len(planned_moves) == 1
    assert planned_moves[0]["source_folder"] == "Deliveries"


def test_skips_when_source_equals_destination(tmp_path, monkeypatch):
    rule = MoveRule(
        name="amazon_to_agenttest",
        to_folder="Deliveries",
        from_contains=["amazon"],
        search_folders=["Deliveries"],
        max_messages=1,
    )
    proc = MailProcedure(target_folders=["Deliveries"], rules=[rule])
    search_map = {"Deliveries": ["1", "2"]}
    plan = _run_executor(tmp_path, monkeypatch, proc, search_map)
    planned_moves = plan["rules"][0].get("planned_moves")
    assert planned_moves == []


def test_protected_folders_not_used_as_source(tmp_path, monkeypatch):
    rule = MoveRule(
        name="amazon_to_agenttest",
        to_folder="AgentTest",
        from_contains=["amazon"],
        search_folders=["Trash", "Deliveries"],
        max_messages=1,
    )
    proc = MailProcedure(
        target_folders=["AgentTest"],
        rules=[rule],
        protected_folders=["Trash"],
    )
    search_map = {
        "Trash": ["9"],
        "Deliveries": ["1"],
    }
    plan = _run_executor(tmp_path, monkeypatch, proc, search_map)
    planned_moves = plan["rules"][0].get("planned_moves")
    assert planned_moves and planned_moves[0]["source_folder"] == "Deliveries"
