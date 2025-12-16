from __future__ import annotations

"""Learning store for failure signatures and site playbooks."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

MEMORY_ROOT = Path(__file__).resolve().parents[1] / "memory"
FAILURE_LOG = MEMORY_ROOT / "failure_cases.jsonl"
PLAYBOOK_DIR = MEMORY_ROOT / "site_playbooks"


def _hash_dict(data: Dict[str, Any]) -> str:
    try:
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
    except Exception:
        serialized = str(data)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_failure_signature(tool: str, site: str, url: str, exception_type: str, verifier_failed: str, dom_hints: Dict[str, Any]) -> str:
    base = {
        "tool": tool or "",
        "site": site or "",
        "url": url or "",
        "exception_type": exception_type or "",
        "verifier_failed": verifier_failed or "",
        "dom_hints_hash": _hash_dict(dom_hints or {}),
    }
    return _hash_dict(base)


def retrieve_similar_cases(signature: str, top_k: int = 3) -> List[Dict[str, Any]]:
    cases = []
    if FAILURE_LOG.is_file():
        for line in FAILURE_LOG.read_text(encoding="utf-8").splitlines():
            try:
                data = json.loads(line)
                cases.append(data)
            except Exception:
                continue
    # Simple similarity: exact signature first, then recent others
    exact = [c for c in cases if c.get("signature") == signature]
    others = [c for c in cases if c.get("signature") != signature]
    ranked = exact + others
    return ranked[:top_k]


def record_success(signature: str, fix_applied: Any):
    FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "signature": signature,
        "fix_strategy": fix_applied,
        "outcome": "success",
        "timestamp": datetime.now().isoformat(),
    }
    with FAILURE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry))
        f.write("\n")


def record_failure(signature: str, reason: str, task_id: str = "", step_id: str = "", metadata: Dict[str, Any] | None = None):
    """Persist a failure signature for future retrieval."""

    FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "signature": signature,
        "reason": reason,
        "task_id": task_id,
        "step_id": step_id,
        "metadata": metadata or {},
        "outcome": "failure",
        "timestamp": datetime.now().isoformat(),
    }
    with FAILURE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry))
        f.write("\n")


def load_playbook(site: str) -> Dict[str, Any]:
    path = PLAYBOOK_DIR / f"{site}.yaml"
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def update_playbook(site: str, key: str, value: Any):
    data = load_playbook(site)
    data[key] = value
    path = PLAYBOOK_DIR / f"{site}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


__all__ = [
    "generate_failure_signature",
    "retrieve_similar_cases",
    "record_success",
    "record_failure",
    "load_playbook",
    "update_playbook",
]
