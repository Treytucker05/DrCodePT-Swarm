from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


STORE_PATH = Path(__file__).resolve().parent / "case_store.json"


def _load() -> Dict[str, Any]:
    if STORE_PATH.exists():
        try:
            data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {"successes": [], "failures": []}


def _save(data: Dict[str, Any]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_failure_signature(task_id: str, step_id: str, reason: str) -> str:
    raw = f"{task_id}|{step_id}|{reason}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()[:16]


def retrieve_similar_cases(signature: str, top_k: int = 3) -> List[Dict[str, Any]]:
    data = _load()
    failures = data.get("failures") or []
    if not isinstance(failures, list):
        return []
    hits = [f for f in reversed(failures) if isinstance(f, dict) and f.get("signature") == signature]
    return hits[: int(top_k)]


def record_success(signature: str, fix_applied: Any = None) -> None:
    data = _load()
    successes = data.setdefault("successes", [])
    if isinstance(successes, list):
        successes.append({"signature": signature, "fix_applied": fix_applied})
    _save(data)


def record_failure(
    signature: str,
    reason: str,
    *,
    task_id: str = "",
    step_id: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    data = _load()
    failures = data.setdefault("failures", [])
    if isinstance(failures, list):
        failures.append(
            {
                "signature": signature,
                "reason": reason,
                "task_id": task_id,
                "step_id": step_id,
                "metadata": metadata or {},
            }
        )
    _save(data)


def load_playbook(playbook_id: str) -> Optional[Dict[str, Any]]:
    """
    Legacy helper; loads:
      1) site playbooks from `agent/memory/site_playbooks/<id>.yaml` (login flows, selectors, etc)
      2) learned playbooks from `agent/learning/playbooks/<id>.json` (fallback)
    """
    base_dir = Path(__file__).resolve().parents[1] / "memory" / "site_playbooks"
    for ext in (".yaml", ".yml"):
        candidate = base_dir / f"{playbook_id}{ext}"
        if candidate.exists():
            try:
                import yaml

                data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else None
            except Exception:
                return None

    pb_dir = Path(__file__).resolve().parent / "playbooks"
    candidate = pb_dir / f"{playbook_id}.json"
    if not candidate.exists():
        return None
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


__all__ = [
    "generate_failure_signature",
    "retrieve_similar_cases",
    "record_success",
    "record_failure",
    "load_playbook",
    "STORE_PATH",
]
