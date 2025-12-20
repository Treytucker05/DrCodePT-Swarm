from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .base import VerifierAdapter, VerifierResult


class FileExistsVerifier(VerifierAdapter):
    verifier_id = "file_exists"

    def verify(self, context: Dict[str, Any]) -> VerifierResult:
        path = self.args.get("path")
        if not path:
            return VerifierResult(id=self.verifier_id, passed=False, details="file_exists requires args.path")
        exists = Path(str(path)).exists()
        return VerifierResult(id=self.verifier_id, passed=exists, details=("exists" if exists else "missing"))


__all__ = ["FileExistsVerifier"]

