from __future__ import annotations

from pathlib import Path
from typing import Dict

from .base import Verifier, VerifyResult


class FileExistsVerifier(Verifier):
    def verify(self, context: Dict) -> VerifyResult:
        path = self.args.get("path")
        if not path:
            return VerifyResult(False, "No path provided")

        target = Path(path)
        exists = target.exists()
        return VerifyResult(exists, f"File exists: {exists}", {"path": str(target)})

