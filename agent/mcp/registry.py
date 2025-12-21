from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class McpServerSpec:
    name: str
    command: str
    args: list[str]
    env: Dict[str, str]


def _registry_path() -> Path:
    return Path(__file__).resolve().parent / "servers.json"


def load_registry() -> Dict[str, McpServerSpec]:
    path = _registry_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    out: Dict[str, McpServerSpec] = {}
    for name, spec in data.items():
        if not isinstance(spec, dict):
            continue
        cmd = str(spec.get("command") or "").strip()
        if not cmd:
            continue
        args = spec.get("args") or []
        env = spec.get("env") or {}
        if not isinstance(args, list):
            args = []
        if not isinstance(env, dict):
            env = {}
        out[name] = McpServerSpec(name=name, command=cmd, args=[str(a) for a in args], env={str(k): str(v) for k, v in env.items()})
    return out


def get_server(name: str) -> Optional[McpServerSpec]:
    return load_registry().get(name)


def list_servers() -> Dict[str, McpServerSpec]:
    return load_registry()
