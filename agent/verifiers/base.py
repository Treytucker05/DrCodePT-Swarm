from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class VerifierResult:
    id: str
    passed: bool
    details: str = ""
    metadata: Dict[str, Any] | None = None


class VerifierAdapter:
    verifier_id: str = ""

    def __init__(self, args: Optional[Dict[str, Any]] = None):
        self.args = args or {}

    def verify(self, context: Dict[str, Any]) -> VerifierResult:  # pragma: no cover
        raise NotImplementedError


__all__ = ["VerifierAdapter", "VerifierResult"]

