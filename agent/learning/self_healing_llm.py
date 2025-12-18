"""Self-Healing module powered by local Ollama models."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from agent.learning.ollama_client import analyze_failure as ollama_analyze

_LAST_ANALYSIS: Dict[str, Any] = {}


def analyze_failure_with_llm(
    task_goal: str,
    error_message: str,
    task_yaml: str,
    execution_log: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Delegate analysis to Ollama and cache metadata."""
    global _LAST_ANALYSIS
    try:
        analysis = ollama_analyze(task_goal, error_message, execution_log)
        if analysis:
            analysis.setdefault("confidence", 0.0)
            analysis.setdefault("is_fixable", bool(analysis.get("corrected_yaml")))
            _LAST_ANALYSIS = analysis
        return analysis
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[WARNING] LLM analysis failed: {exc}")
        return None


def apply_self_healing(
    run_path: Path,
    task_def,
    error_message: str,
    execution_log: Dict[str, Any],
) -> Optional[str]:
    """
    Apply self-healing to a failed task.

    Returns:
        Path to corrected YAML file if healing succeeded, None otherwise.
    """
    yaml_path = run_path / "original_task.yaml"
    if not yaml_path.exists():
        return None

    task_yaml = yaml_path.read_text()
    analysis = analyze_failure_with_llm(
        task_goal=task_def.goal,
        error_message=error_message,
        task_yaml=task_yaml,
        execution_log=execution_log,
    )

    if not analysis or not analysis.get("is_fixable"):
        return None

    heal_dir = run_path / "self_heal"
    heal_dir.mkdir(parents=True, exist_ok=True)

    analysis_path = heal_dir / "analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2))

    corrected_path = heal_dir / "corrected_plan.yaml"
    if analysis.get("corrected_yaml"):
        corrected_path.write_text(analysis["corrected_yaml"])
        return str(corrected_path)

    return None


def get_last_analysis() -> Dict[str, Any]:
    """Expose last LLM analysis metadata."""
    return _LAST_ANALYSIS or {}


def log_healing_attempt(
    run_path: Path,
    attempt_number: int,
    success: bool,
    details: Dict[str, Any],
):
    """Log a self-healing attempt to healing_log.jsonl."""
    log_path = run_path / "healing_log.jsonl"
    entry = {
        "attempt": attempt_number,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "details": details,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    # Lightweight self-check
    dummy = analyze_failure_with_llm(
        task_goal="Create a file named test.txt",
        error_message="Permission denied",
        task_yaml="id: test\nname: Test\ntype: shell\ngoal: Create file\ncommand: touch /root/test.txt",
        execution_log={"error": "Permission denied"},
    )
    print(dummy or "analysis unavailable")
