from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from agent.agent_logging.run_logger import finalize_run, log_event


HANDOFF_DIR = Path(__file__).resolve().parents[1] / "handoff"


def _last_events(run_path: Path, limit: int = 10) -> List[Dict[str, Any]]:
    events_path = run_path / "events.jsonl"
    if not events_path.exists():
        return []
    try:
        lines = events_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            import json

            out.append(json.loads(line))
        except Exception:
            continue
    return out


def trigger_handoff(run_path: str | Path, task, evidence: Dict[str, Any]) -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    waiting = HANDOFF_DIR / "WAITING.yaml"
    payload = {
        "task_id": getattr(task, "id", ""),
        "run_path": str(Path(run_path).resolve()),
        "blocked_at": datetime.now().isoformat(),
        "reason": "requires_human",
        "evidence": evidence or {},
    }
    waiting.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    log_event(run_path, "handoff_wait", payload)


def wait_for_continue(poll_seconds: float = 2.0, timeout_minutes: Optional[int] = None) -> bool:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    flag = HANDOFF_DIR / "CONTINUE.flag"
    start = time.time()
    while True:
        if flag.exists():
            try:
                flag.unlink()
            except Exception:
                pass
            waiting = HANDOFF_DIR / "WAITING.yaml"
            try:
                waiting.unlink()
            except Exception:
                pass
            return True
        if timeout_minutes is not None and (time.time() - start) > timeout_minutes * 60:
            return False
        time.sleep(poll_seconds)


def escalate(run_path: str | Path, reason: str, task_id: str | None = None) -> None:
    finalize_run(run_path, "escalated", f"{reason}" + (f" (task_id={task_id})" if task_id else ""))
    raise SystemExit(2)


def abort(run_path: str | Path, reason: str) -> None:
    finalize_run(run_path, "aborted", reason)
    raise SystemExit(1)


def self_heal_browser_failure(run_path: str | Path, task, metadata: Dict[str, Any]) -> None:
    # Lightweight hook for browser-specific failure evidence; main self-heal loop lives in supervisor.py.
    log_event(run_path, "browser_failure", {"task_id": getattr(task, "id", ""), "metadata": metadata})


__all__ = [
    "HANDOFF_DIR",
    "_last_events",
    "trigger_handoff",
    "wait_for_continue",
    "escalate",
    "abort",
    "self_heal_browser_failure",
]
