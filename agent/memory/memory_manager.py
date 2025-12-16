from __future__ import annotations

"""
Persistent agent memory stored in memory/agent_memory.json.
Fields: completed_tasks, facts, preferences, credentials (site -> credential_id mapping).
"""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

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
