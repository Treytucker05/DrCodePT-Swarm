from __future__ import annotations

"""Run logging utilities for DrCodePT Agent."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

RUNS_ROOT = Path(__file__).resolve().parents[1] / "runs"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def _ensure_unique_dir(base_path: Path) -> Path:
    if not base_path.exists():
        return base_path
    counter = 1
    while True:
        candidate = Path(f"{base_path}_{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def init_run(task_id: str) -> Path:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    run_dir_name = f"{_timestamp()}_{task_id}"
    run_path = _ensure_unique_dir(RUNS_ROOT / run_dir_name)
    run_path.mkdir(parents=True, exist_ok=True)

    # required subfolders
    for sub in ("before", "evidence", "output"):
        (run_path / sub).mkdir(parents=True, exist_ok=True)

    # touch events file
    events_file = run_path / "events.jsonl"
    events_file.touch(exist_ok=True)

    return run_path


def log_event(run_path: Path, event_type: str, data: Dict[str, Any]):
    payload = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "data": data,
    }
    events_file = Path(run_path) / "events.jsonl"
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload))
        f.write("\n")


def finalize_run(run_path: Path, outcome: str, summary: str):
    summary_file = Path(run_path) / "summary.md"
    content = f"# Run outcome: {outcome}\n\n{summary}\n"
    summary_file.write_text(content, encoding="utf-8")


__all__ = ["init_run", "log_event", "finalize_run"]
