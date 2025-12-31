from __future__ import annotations

"""
Persistent agent memory stored in memory/agent_memory.json.
Fields: completed_tasks, facts, preferences, credentials (site -> credential_id mapping).
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.autonomous.memory.sqlite_store import SqliteMemoryStore

ROOT = Path(__file__).resolve().parent
MEMORY_PATH = ROOT / "agent_memory.json"

DEFAULT_MEMORY: Dict[str, Any] = {
    "completed_tasks": [],
    "facts": {},
    "preferences": {},
    "credentials": {},
}

_CACHE: Dict[str, Any] | None = None


def load_memory() -> Dict[str, Any]:
    """Load memory from disk (cached). Creates default file if missing/invalid."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    if MEMORY_PATH.is_file():
        try:
            _CACHE = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            _CACHE = deepcopy(DEFAULT_MEMORY)
    else:
        _CACHE = deepcopy(DEFAULT_MEMORY)
        save_memory(_CACHE)

    if not isinstance(_CACHE, dict):
        _CACHE = deepcopy(DEFAULT_MEMORY)

    # Migration: credential_paths -> credentials
    if "credential_paths" in _CACHE and "credentials" not in _CACHE:
        old = _CACHE.pop("credential_paths") or {}
        if isinstance(old, dict):
            _CACHE["credentials"] = {k: str(v) for k, v in old.items()}

    # Ensure required keys exist
    for key, default_value in DEFAULT_MEMORY.items():
        _CACHE.setdefault(key, deepcopy(default_value))

    return _CACHE


def save_memory(data: Dict[str, Any] | None = None) -> Path:
    """Persist memory to disk and update cache."""
    global _CACHE
    if data is None:
        data = _CACHE if _CACHE is not None else deepcopy(DEFAULT_MEMORY)
    _CACHE = data
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return MEMORY_PATH


def update_memory(key: str, value: Any) -> Dict[str, Any]:
    """Set a top-level key and save."""
    data = load_memory()
    data[key] = value
    save_memory(data)
    return data


__all__ = ["load_memory", "save_memory", "update_memory", "MEMORY_PATH"]


class MemoryManager:
    """Lightweight wrapper for long-term memory with similarity search."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or (ROOT / "autonomous_memory.sqlite3")
        self._store = SqliteMemoryStore(self.path)

    def store(self, key: str, value: Any, *, kind: str = "experience") -> None:
        content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        self._store.upsert(kind=kind, key=key, content=content, metadata={"key": key})

    def add_completed_task(self, task: Dict[str, Any]) -> None:
        """Store a completed task record."""
        timestamp = task.get("timestamp") or ""
        key = f"completed_task:{timestamp or 'unknown'}"
        self.store(key, task, kind="completed_task")

    def add_fact(self, fact: str, *, category: str = "lessons") -> None:
        """Store a learned fact or lesson."""
        if not fact:
            return
        key = f"{category}:{abs(hash(fact))}"
        payload = {"fact": fact, "category": category}
        self.store(key, payload, kind=category)

    def add_preference(self, key: str, value: Any) -> None:
        """Store a user preference."""
        if not key:
            return
        payload = {"key": key, "value": value}
        self.store(f"pref:{key}", payload, kind="preference")

    def retrieve_similar(self, query: str, k: int = 3, *, kinds: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        records = self._store.search(query, kinds=kinds, limit=k)
        results: List[Dict[str, Any]] = []
        for rec in records:
            content = rec.content
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = content
            results.append(
                {
                    "key": rec.key,
                    "content": parsed,
                    "metadata": rec.metadata,
                }
            )
        return results

    def close(self) -> None:
        try:
            self._store.close()
        except Exception:
            pass


__all__.append("MemoryManager")
