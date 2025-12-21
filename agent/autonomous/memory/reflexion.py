from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic import BaseModel, Field


class ReflexionEntry(BaseModel):
    id: str
    timestamp: str
    objective: str
    context_fingerprint: str
    phase: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    reflection: str
    fix: str
    outcome: str
    tags: List[str] = Field(default_factory=list)


_RUN_DIR_ENV = "REFLEXION_RUN_DIR"
_BASE_DIR_ENV = "REFLEXION_BASE_DIR"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _runs_root() -> Path:
    override = os.getenv(_BASE_DIR_ENV, "").strip()
    if override:
        return Path(override)
    return _repo_root() / "runs"


def _current_run_dir() -> Path:
    override = os.getenv(_RUN_DIR_ENV, "").strip()
    if override:
        return Path(override)
    # Default to a shared reflexion log under runs/
    return _runs_root()


def _iter_reflexion_files() -> Iterable[Path]:
    root = _runs_root()
    if not root.exists():
        return []
    return root.rglob("reflexion.jsonl")


def _tokenize(text: str) -> List[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text or "")
    return [t for t in cleaned.split() if t]


def _score_entry(
    entry: ReflexionEntry, objective_tokens: List[str], error_tokens: List[str]
) -> Tuple[float, float]:
    haystack = " ".join(
        [
            entry.objective or "",
            " ".join(entry.errors or []),
            entry.reflection or "",
            entry.fix or "",
            entry.outcome or "",
        ]
    )
    hay_tokens = set(_tokenize(haystack))
    overlap = len(set(objective_tokens) & hay_tokens)
    if error_tokens:
        overlap += 2 * len(set(error_tokens) & hay_tokens)

    recency = 0.0
    try:
        ts = datetime.fromisoformat(entry.timestamp)
        age_seconds = max((datetime.now(timezone.utc) - ts).total_seconds(), 0.0)
        recency = 1.0 / (1.0 + age_seconds / 3600.0)
    except Exception:
        recency = 0.0
    return float(overlap), recency


def write_reflexion(entry: ReflexionEntry) -> Path:
    run_dir = _current_run_dir()
    if run_dir.is_dir() and run_dir.name == "runs":
        path = run_dir / "reflexion.jsonl"
    else:
        path = run_dir / "reflexion.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    line = entry.model_dump() if hasattr(entry, "model_dump") else entry.dict()
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    return path


def retrieve_reflexions(
    objective: str, error_signature: str | None, k: int = 5
) -> List[ReflexionEntry]:
    objective_tokens = _tokenize(objective)
    error_tokens = _tokenize(error_signature or "")
    scored: List[Tuple[float, float, ReflexionEntry]] = []

    for file_path in _iter_reflexion_files():
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                entry = ReflexionEntry.model_validate(raw)
            except Exception:
                continue
            overlap, recency = _score_entry(entry, objective_tokens, error_tokens)
            if overlap <= 0:
                continue
            scored.append((overlap, recency, entry))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [entry for _, _, entry in scored[: max(0, k)]]
