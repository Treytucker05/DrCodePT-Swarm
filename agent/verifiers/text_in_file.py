from __future__ import annotations

from pathlib import Path
from typing import Dict

from .base import Verifier, VerifyResult


class TextInFileVerifier(Verifier):
    def verify(self, context: Dict) -> VerifyResult:
        path = self.args.get("path")
        text = self.args.get("text")
        if not path or text is None:
            return VerifyResult(False, "Missing path or text")

        target = Path(path)
        if not target.is_file():
            return VerifyResult(False, f"File not found: {path}")

        content = target.read_text(encoding="utf-8")
        found = text in content
        return VerifyResult(found, f"Text {'found' if found else 'not found'}", {"path": str(target)})
