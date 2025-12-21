from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"


def _now_id() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def init_run(task_id: str) -> str:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_name = f"{_now_id()}_{task_id}"
    run_path = RUNS_DIR / run_name
    run_path.mkdir(parents=True, exist_ok=True)
    (run_path / "events.jsonl").write_text("", encoding="utf-8")
    return str(run_path)


def log_event(run_path: str | Path, event_type: str, payload: Dict[str, Any]) -> None:
    p = Path(run_path)
    p.mkdir(parents=True, exist_ok=True)
    evt = {
        "ts": datetime.now().isoformat(),
        "type": event_type,
        "payload": payload,
    }
    (p / "events.jsonl").open("a", encoding="utf-8", errors="replace", newline="\n").write(
        json.dumps(evt, ensure_ascii=False) + "\n"
    )


def finalize_run(run_path: str | Path, status: str, summary: str = "") -> None:
    p = Path(run_path)
    data = {"status": status, "summary": summary, "finished_at": datetime.now().isoformat()}
    (p / "result.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = ["init_run", "log_event", "finalize_run", "RUNS_DIR"]

