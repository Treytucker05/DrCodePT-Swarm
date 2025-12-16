from __future__ import annotations

"""Base verifier interface and result container."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class VerifyResult:
    passed: bool
    message: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


class Verifier:
    def __init__(self, args: Dict[str, Any]):
        self.args = args or {}

    def verify(self, context: Dict[str, Any]) -> VerifyResult:  # pragma: no cover - interface
        raise NotImplementedError

