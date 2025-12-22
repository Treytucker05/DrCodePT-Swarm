from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class QaResult:
    ok: bool
    errors: List[str]
    warnings: List[str]


def _read_json(path: Path) -> Optional[Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def validate_artifacts(run_dir: Path, expected_files: Iterable[str]) -> QaResult:
    errors: List[str] = []
    warnings: List[str] = []
    for name in expected_files:
        path = run_dir / name
        if not path.exists():
            errors.append(f"missing {name}")
    result_path = run_dir / "result.json"
    if result_path.exists():
        if _read_json(result_path) is None:
            errors.append("invalid JSON in result.json")
    trace_path = run_dir / "trace.jsonl"
    if trace_path.exists():
        try:
            lines = trace_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if not lines:
                errors.append("trace.jsonl is empty")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                except Exception:
                    errors.append("invalid JSON line in trace.jsonl")
                    break
        except Exception:
            errors.append("failed to read trace.jsonl")
    repo_map_path = run_dir / "repo_map.json"
    if repo_map_path.exists():
        if _read_json(repo_map_path) is None:
            errors.append("invalid JSON in repo_map.json")
    return QaResult(ok=not errors, errors=errors, warnings=warnings)


def format_qa_summary(artifact_results: Dict[str, QaResult], test_result: Optional[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for sub_id, result in artifact_results.items():
        status = "ok" if result.ok else "issues"
        detail = ""
        if result.errors:
            detail = " | " + "; ".join(result.errors)
        lines.append(f"- {sub_id}: {status}{detail}")
    if test_result:
        status = "ok" if test_result.get("ok") else "failed"
        detail = ""
        if test_result.get("message"):
            detail = f" | {test_result['message']}"
        lines.append(f"- tests: {status}{detail}")
    return lines


__all__ = ["QaResult", "format_qa_summary", "validate_artifacts"]

