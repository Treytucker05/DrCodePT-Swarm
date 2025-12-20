from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .base import VerifierAdapter, VerifierResult


class JsonHasEntriesVerifier(VerifierAdapter):
    verifier_id = "json_has_entries"

    def verify(self, context: Dict[str, Any]) -> VerifierResult:
        path = self.args.get("path")
        if not path:
            return VerifierResult(id=self.verifier_id, passed=False, details="json_has_entries requires args.path")
        p = Path(str(path))
        if not p.exists():
            return VerifierResult(id=self.verifier_id, passed=False, details=f"missing: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            return VerifierResult(id=self.verifier_id, passed=False, details=f"invalid_json: {exc}")
        has_entries = False
        if isinstance(data, list):
            has_entries = len(data) > 0
        elif isinstance(data, dict):
            has_entries = len(data) > 0
        return VerifierResult(id=self.verifier_id, passed=has_entries, details="non_empty" if has_entries else "empty")


__all__ = ["JsonHasEntriesVerifier"]

