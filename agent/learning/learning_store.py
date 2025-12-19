import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

from agent.logging.redaction import redact

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
    """Generates a unique hash signature for a failure case."""
    base = {
        "tool": tool or "",
        "site": site or "",
        "url": url or "",
        "exception_type": exception_type or "",
        "verifier_failed": verifier_failed or "",
        "dom_hints_hash": _hash_dict(dom_hints or {}),
    }
    return _hash_dict(base)


def record_failure(task_id: str, signature: str, context: Dict[str, Any]):
    """Records a new failure case to the log file."""
    FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "signature": signature,
        "context": redact(context),
    }
    with open(FAILURE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def retrieve_similar_cases(signature: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Retrieves similar failure cases based on the signature."""
    cases = []
    if FAILURE_LOG.is_file():
        with open(FAILURE_LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    cases.append(data)
                except Exception:
                    continue
    
    # Simple similarity: exact signature first, then recent others
    exact = [c for c in cases if c.get("signature") == signature]
    others = [c for c in cases if c.get("signature") != signature]
    
    # Prioritize exact matches, then sort others by timestamp (most recent first)
    others.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    ranked = exact + others
    return ranked[:top_k]


def load_playbook(site: str) -> Dict[str, Any]:
    """Loads a site-specific playbook for known issues."""
    path = PLAYBOOK_DIR / f"{site}.yaml"
    if path.is_file():
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    return {}
