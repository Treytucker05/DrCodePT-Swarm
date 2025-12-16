from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .base import Verifier, VerifyResult


class JsonHasEntriesVerifier(Verifier):
    def verify(self, context: Dict) -> VerifyResult:
        path = self.args.get("path")
        min_entries = int(self.args.get("min_entries", 1))
        if not path:
            return VerifyResult(False, "No path provided")

        target = Path(path)
        if not target.is_file():
            return VerifyResult(False, f"File not found: {path}")

        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            count = len(data) if hasattr(data, "__len__") else 0
            ok = count >= min_entries
            return VerifyResult(ok, f"entries={count}, required>={min_entries}", {"count": count})
        except Exception as exc:  # pragma: no cover
            return VerifyResult(False, f"JSON load failed: {exc}")

