from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .base import VerifierAdapter, VerifierResult


class TextInFileVerifier(VerifierAdapter):
    verifier_id = "text_in_file"

    def verify(self, context: Dict[str, Any]) -> VerifierResult:
        path = self.args.get("path")
        text = self.args.get("text")
        if not path or text is None:
            return VerifierResult(id=self.verifier_id, passed=False, details="text_in_file requires args.path and args.text")
        p = Path(str(path))
        if not p.exists():
            return VerifierResult(id=self.verifier_id, passed=False, details=f"missing: {p}")
        content = p.read_text(encoding="utf-8", errors="replace")
        passed = str(text) in content
        return VerifierResult(id=self.verifier_id, passed=passed, details="found" if passed else "not_found")


__all__ = ["TextInFileVerifier"]

