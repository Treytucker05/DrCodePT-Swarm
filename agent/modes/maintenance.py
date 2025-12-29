from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm import schemas as llm_schemas


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _iter_traces(root: Path, *, since_seconds: float, limit: int) -> List[Path]:
    if not root.exists():
        return []
    traces = [p for p in root.rglob("trace.jsonl") if p.is_file()]
    traces = [p for p in traces if (time.time() - p.stat().st_mtime) <= since_seconds]
    traces.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return traces[:limit]


def _summarize_trace(path: Path) -> Dict[str, object]:
    tool_counts: Dict[str, int] = {}
    errors: List[str] = []
    stop_reason = ""
    total = 0
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
            if evt_type == "stop":
                stop_reason = str(evt.get("reason") or "")
            tool = None
            if isinstance(evt.get("tool"), str):
                tool = evt.get("tool")
            elif isinstance(evt.get("tool_name"), str):
                tool = evt.get("tool_name")
            if tool:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            if "error" in evt_type or evt_type in {"error_report", "recovery_failed"}:
                errors.append(evt_type)
    return {
        "trace_path": str(path),
        "total_events": total,
        "stop_reason": stop_reason,
        "tools": sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:8],
        "errors": errors[-10:],
    }


def maintenance_run(days: int = 7, limit: int = 25) -> None:
    repo = _repo_root()
    runs_root = repo / "runs"
    since_seconds = max(1, days) * 86400

    traces = _iter_traces(runs_root, since_seconds=since_seconds, limit=limit)
    if not traces:
        print("[MAINTENANCE] No recent traces found.")
        return

    memory_path = os.getenv("AGENT_MEMORY_DB") or str(repo / "agent" / "memory" / "autonomous_memory.sqlite3")
    store = SqliteMemoryStore(Path(memory_path))
    try:
        for path in traces:
            summary = _summarize_trace(path)
            key = f"maintenance:{path.parent.name}"
            store.upsert(
                kind="knowledge",
                key=key,
                content=json.dumps(summary, ensure_ascii=False),
                metadata={"source": "maintenance", "run_id": path.parent.name},
            )
        print(f"[MAINTENANCE] Processed {len(traces)} runs.")
    finally:
        store.close()


def maintenance_report(days: int = 7, limit: int = 20) -> None:
    try:
        llm = CodexCliClient.from_env()
    except (CodexCliNotFoundError, CodexCliAuthError):
        maintenance_run(days=days, limit=limit)
        return

    repo = _repo_root()
    traces = _iter_traces(repo / "runs", since_seconds=max(1, days) * 86400, limit=limit)
    summaries = [_summarize_trace(p) for p in traces]
    prompt = (
        "Summarize recent agent runs and identify common failure patterns or tool issues.\n"
        "Return JSON with a short response string and no action.\n\n"
        f"DATA:\n{json.dumps(summaries, ensure_ascii=False)}\n"
    )
    data = llm.reason_json(prompt, schema_path=llm_schemas.CHAT_RESPONSE)
    if isinstance(data, dict):
        resp = (data.get("response") or "").strip()
        if resp:
            print(resp)


__all__ = ["maintenance_run", "maintenance_report"]
