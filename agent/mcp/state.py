from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _state_path() -> Path:
    base = Path(__file__).resolve().parents[1]
    return base / "memory" / "mcp_state.json"


def get_active_server() -> Optional[str]:
    path = _state_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if isinstance(data, dict):
            name = data.get("active_server")
            return str(name) if name else None
    except Exception:
        return None
    return None


def set_active_server(name: str) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"active_server": name}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
