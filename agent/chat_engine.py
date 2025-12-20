from __future__ import annotations

"""
Chat engine for terminal/CLI use.
Offline-only: always returns local summary of tasks and recent runs.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yaml
from dotenv import load_dotenv

AGENT_ROOT = Path(__file__).resolve().parent
TASKS_DIR = AGENT_ROOT / "tasks"
RUNS_DIR = AGENT_ROOT / "runs"

load_dotenv()


def _task_to_json(path: Path) -> Dict[str, str]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}
    return {
        "name": path.name.replace(".yaml", ""),
        "type": data.get("type", "unknown"),
        "goal": data.get("goal", ""),
    }


def list_tasks() -> List[Path]:
    return sorted(TASKS_DIR.glob("*.yaml"))


def _status_from_summary(summary_text: str) -> str:
    text = summary_text.lower()
    if "run outcome: success" in text:
        return "success"
    if "escalated" in text:
        return "escalated"
    if "abort" in text or "fail" in text:
        return "failed"
    return "in-progress"


def list_runs(limit: int = 5):
    runs = [p for p in RUNS_DIR.iterdir() if p.is_dir()]
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for r in runs[:limit]:
        summary = (r / "summary.md").read_text(encoding="utf-8") if (r / "summary.md").is_file() else ""
        status = _status_from_summary(summary) if summary else "in-progress"
        started = datetime.fromtimestamp(r.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        out.append({"id": r.name, "status": status, "startedAt": started})
    return out


def chat_reply(user_msg: str) -> str:
    user_msg = (user_msg or "").strip()
    tasks = [_task_to_json(p)["name"] for p in list_tasks()]
    runs = list_runs(5)
    run_summaries = ", ".join(f"{r['id']} ({r['status']})" for r in runs) or "no runs yet"
    return (
        "Local chat (offline). "
        f"Tasks: {', '.join(tasks[:8])}" + ("..." if len(tasks) > 8 else "") + ". "
        f"Recent runs: {run_summaries}. "
        "Model replies are disabled in this offline chat mode. Use the autonomous runner (`python -m agent.run`) "
        "which uses your Codex CLI login (`codex login`)."
    )


__all__ = ["chat_reply"]
