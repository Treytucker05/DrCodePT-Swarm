from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.codex_client import CodexTaskClient


def log_healing_attempt(run_path: str | Path, payload: Dict[str, Any]) -> None:
    p = Path(run_path)
    p.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now().isoformat(), **(payload or {})}
    (p / "healing.jsonl").open("a", encoding="utf-8", errors="replace", newline="\n").write(
        json.dumps(rec, ensure_ascii=False) + "\n"
    )


def apply_self_healing(
    *,
    goal: str,
    failed_task_yaml: str,
    error: str,
    recent_events: Optional[List[Dict[str, Any]]] = None,
    codex: Optional[CodexTaskClient] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Self-heal a failing YAML task by:
      1) analyzing the failure (structured JSON)
      2) generating a corrected YAML plan (structured JSON)

    Returns a dict containing:
      - corrected_plan (YAML string)
      - root_cause
      - suggested_tool_or_step_changes
      - stop_condition_if_applicable
    """
    client = codex or CodexTaskClient.from_env()

    analysis = client.analyze_failure(
        goal=goal,
        task_yaml=failed_task_yaml,
        error=error,
        recent_events=recent_events or [],
        timeout_seconds=timeout_seconds,
    )

    corrected = client.generate_yaml_plan(
        goal=goal,
        previous_yaml=failed_task_yaml,
        failure_analysis=analysis,
        timeout_seconds=timeout_seconds,
    )

    corrected_yaml = (corrected.get("yaml") or "").strip()

    return {
        "corrected_plan": corrected_yaml,
        "root_cause": analysis.get("root_cause", ""),
        "suggested_tool_or_step_changes": analysis.get("suggested_tool_or_step_changes", []),
        "stop_condition_if_applicable": analysis.get("stop_condition_if_applicable"),
        "analysis_explanation_short": analysis.get("explanation_short", ""),
    }


__all__ = ["apply_self_healing", "log_healing_attempt"]

