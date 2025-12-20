from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class JsonlTracer:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: Dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    @property
    def trace_path(self) -> str:
        return str(self.path)

