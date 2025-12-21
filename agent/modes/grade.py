from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm import schemas as llm_schemas


@dataclass
class TraceSummary:
    trace_path: Path
    total_events: int
    tool_counts: Dict[str, int]
    error_events: List[str]
    stop_reason: str
    key_events: List[Dict[str, Any]]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _grade_llm() -> CodexCliClient:
    base = CodexCliClient.from_env()
    model = (os.getenv("GRADE_MODEL") or os.getenv("CODEX_MODEL_GRADE") or "").strip()
    if not model:
        return base
    return CodexCliClient(
        codex_bin=base.codex_bin,
        model=model,
        timeout_seconds=base.timeout_seconds,
        profile_reason=base.profile_reason,
        profile_exec=base.profile_exec,
    )


def _iter_trace_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("trace.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def _find_trace(target: str | None) -> Optional[Path]:
    repo = _repo_root()
    runs_root = repo / "runs"

    if target:
        candidate = Path(target.strip().strip("\"'"))
        if candidate.is_file():
            return candidate
        if candidate.is_dir():
            trace = candidate / "trace.jsonl"
            if trace.is_file():
                return trace
        # Try find by run_id
        for trace in _iter_trace_files(runs_root):
            if trace.parent.name == target:
                return trace

    # Default: latest trace under runs
    traces = _iter_trace_files(runs_root)
    return traces[0] if traces else None


def _summarize_trace(path: Path, *, max_events: int = 120) -> TraceSummary:
    tool_counts: Dict[str, int] = {}
    error_events: List[str] = []
    key_events: List[Dict[str, Any]] = []
    stop_reason = ""
    total = 0

    def _tool_from_event(evt: Dict[str, Any]) -> Optional[str]:
        if "tool" in evt and isinstance(evt.get("tool"), str):
            return evt["tool"]
        if "tool_name" in evt and isinstance(evt.get("tool_name"), str):
            return evt["tool_name"]
        action = evt.get("action")
        if isinstance(action, dict):
            t = action.get("tool_name") or action.get("tool")
            if isinstance(t, str):
                return t
        return None

    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                evt = json.loads(line)
            except Exception:
                continue

            evt_type = str(evt.get("type") or "")
            tool_name = _tool_from_event(evt)
            if tool_name:
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            if "error" in evt_type or evt_type in {"error_report", "recovery_failed", "tool_error"}:
                error_events.append(evt_type)
            if evt_type == "stop":
                stop_reason = str(evt.get("reason") or "")

            if evt_type in {"step", "error_report", "recovery_failed", "stop", "tool_retry", "observation"}:
                key_events.append(evt)

    # keep the most recent key events
    key_events = key_events[-max_events:]

    return TraceSummary(
        trace_path=path,
        total_events=total,
        tool_counts=tool_counts,
        error_events=error_events[-20:],
        stop_reason=stop_reason,
        key_events=key_events,
    )


def _format_summary(summary: TraceSummary) -> str:
    tools_sorted = sorted(summary.tool_counts.items(), key=lambda x: x[1], reverse=True)
    top_tools = tools_sorted[:8]
    tool_lines = [f"{name}:{count}" for name, count in top_tools]
    payload = {
        "trace_path": str(summary.trace_path),
        "total_events": summary.total_events,
        "stop_reason": summary.stop_reason,
        "top_tools": tool_lines,
        "error_events": summary.error_events,
        "key_events_tail": summary.key_events,
    }
    return json.dumps(payload, ensure_ascii=False)


def grade_run(target: str | None = None) -> None:
    try:
        llm = _grade_llm()
    except CodexCliNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return
    except CodexCliAuthError as exc:
        print(f"[ERROR] {exc}")
        return

    trace = _find_trace(target)
    if trace is None or not trace.exists():
        print("[GRADE] No trace.jsonl found. Run a task first.")
        return

    summary = _summarize_trace(trace)
    formatted = _format_summary(summary)

    prompt = (
        "You are grading an autonomous agent run.\n"
        "Score the run on reasoning, tool usage, and efficiency (1-10) and give an overall score.\n"
        "Use the trace summary and key events to justify issues and recommendations.\n"
        "Be concise and critical.\n\n"
        f"TRACE SUMMARY (json):\n{formatted}\n"
    )

    data = llm.reason_json(prompt, schema_path=llm_schemas.GRADE)
    if not isinstance(data, dict):
        print("[GRADE] Failed to parse grade response.")
        return

    scores = data.get("scores") or {}
    print("\n[GRADE] Results")
    print("---------------")
    print(
        f"Reasoning: {scores.get('reasoning')} | Tool usage: {scores.get('tool_usage')} | "
        f"Efficiency: {scores.get('efficiency')} | Overall: {scores.get('overall')}"
    )
    summary_text = (data.get("summary") or "").strip()
    if summary_text:
        print("\nSummary:")
        print(summary_text)

    issues = data.get("issues") or []
    if issues:
        print("\nIssues:")
        for item in issues:
            print(f"- {item}")

    recs = data.get("recommendations") or []
    if recs:
        print("\nRecommendations:")
        for item in recs:
            print(f"- {item}")

    print(f"\nTrace: {trace}")


__all__ = ["grade_run"]
