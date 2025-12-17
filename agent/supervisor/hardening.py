from __future__ import annotations

"""Hardening utilities: escalation packets, rollback, and human handoff."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from enum import Enum

import yaml

from agent.logging.run_logger import finalize_run

FAILURES_ROOT = Path(__file__).resolve().parents[1] / "failures"
HANDOFF_ROOT = Path(__file__).resolve().parents[1] / "handoff"


def _last_events(run_path: Path, n: int = 10) -> List[Dict]:
    events_file = Path(run_path) / "events.jsonl"
    if not events_file.is_file():
        return []
    lines = events_file.read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines[-n:]]


def _serialize_for_yaml(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: _serialize_for_yaml(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_for_yaml(v) for v in value]
    return value


def self_heal_browser_failure(run_path: Path, task, metadata: Dict[str, Any]) -> Path:
    """Create an LLM-ready payload for a corrected browser step and instruct manual intervention."""
    run_path = Path(run_path)
    heal_dir = run_path / "self_heal"
    heal_dir.mkdir(parents=True, exist_ok=True)

    dom_snapshot = (metadata or {}).get("dom_snapshot") or "No DOM Snapshot Available"
    failed_step = {}
    if hasattr(task, "dict"):
        try:
            failed_step = _serialize_for_yaml(task.dict())
        except Exception:
            failed_step = {}

    payload = _serialize_for_yaml({
        "task_id": getattr(task, "id", ""),
        "goal": getattr(task, "goal", ""),
        "tool": getattr(getattr(task, "type", None), "value", getattr(task, "type", "")),
        "url": getattr(task, "url", ""),
        "failed_step": failed_step,
        "failure_reason": (metadata or {}).get("error", "Unknown browser error"),
        "dom_snapshot": dom_snapshot,
        "instruction": (
            "The previous step failed. Analyze the DOM snapshot and the failed step to generate a single, corrected "
            "step (a dictionary) that should be executed next. Output ONLY the corrected step dictionary."
        ),
        "last_10_events": _last_events(run_path),
        "timestamp": datetime.now().isoformat(),
    })

    dest = heal_dir / f"self_heal_payload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    dest.write_text(yaml.safe_dump(payload), encoding="utf-8")

    print("\n--- SELF-HEAL TRIGGERED ---")
    print(f"Payload saved to: {dest}")
    print("ACTION REQUIRED: Feed the content of this file to the Codex Planner LLM to generate a corrected step.")
    print("---------------------------\n")
    return dest


def snapshot_before_write(run_path: Path, target: Path):
    """Copy current file state into before/ prior to mutation."""
    target = Path(target)
    if not target.exists():
        return
    before_dir = Path(run_path) / "before"
    before_dir.mkdir(parents=True, exist_ok=True)
    dest = before_dir / target.name
    dest.write_bytes(target.read_bytes())


def escalate(run_path: Path, reason: str, task_id: str = "", blocking_question: str = "", suggested_human_action: str = "", evidence_path: str = ""):
    FAILURES_ROOT.mkdir(parents=True, exist_ok=True)
    run_id = Path(run_path).name
    dest_dir = FAILURES_ROOT / run_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    packet = {
        "task_id": task_id,
        "run_path": str(Path(run_path).resolve()),
        "blocked_at": datetime.now().isoformat(),
        "reason": reason,
        "blocking_question": blocking_question,
        "suggested_human_action": suggested_human_action,
        "evidence_path": evidence_path,
        "last_10_events": _last_events(run_path),
    }
    (dest_dir / "escalation.yaml").write_text(yaml.safe_dump(packet), encoding="utf-8")
    finalize_run(run_path, "escalated", f"Escalated: {reason}")


def abort(run_path: Path, reason: str):
    restore_note = "Restore files from before/ backups if needed."
    finalize_run(run_path, "aborted", f"{reason}\n\n{restore_note}")


def trigger_handoff(run_path: Path, task, evidence):
    HANDOFF_ROOT.mkdir(parents=True, exist_ok=True)
    waiting = HANDOFF_ROOT / "WAITING.yaml"
    payload = {
        "task_id": getattr(task, "id", ""),
        "run_path": str(Path(run_path).resolve()),
        "blocked_at": datetime.now().isoformat(),
        "reason": "requires_human",
        "screenshot": evidence.get("screenshot") if isinstance(evidence, dict) else None,
        "instructions": "Complete the required action then create CONTINUE.flag",
        "resume_from": getattr(task, "id", ""),
    }
    waiting.write_text(yaml.safe_dump(payload), encoding="utf-8")
    handoff_event = Path(run_path) / "events.jsonl"
    if handoff_event.is_file():
        handoff_event.write_text(handoff_event.read_text() + "")


def wait_for_continue(poll_seconds: int = 5):
    flag = HANDOFF_ROOT / "CONTINUE.flag"
    waiting = HANDOFF_ROOT / "WAITING.yaml"
    while True:
        if flag.exists():
            flag.unlink()
            if waiting.exists():
                waiting.unlink()
            return
        time.sleep(poll_seconds)


__all__ = ["escalate", "abort", "trigger_handoff", "wait_for_continue", "snapshot_before_write", "self_heal_browser_failure", "_last_events"]
