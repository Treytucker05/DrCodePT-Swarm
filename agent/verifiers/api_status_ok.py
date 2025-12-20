from __future__ import annotations

from typing import Any, Dict

from .base import VerifierAdapter, VerifierResult


class ApiStatusOkVerifier(VerifierAdapter):
    verifier_id = "api_status_ok"

    def verify(self, context: Dict[str, Any]) -> VerifierResult:
        last = context.get("last_result") or {}
        if isinstance(last, dict):
            status = last.get("status_code")
            if status is None:
                return VerifierResult(id=self.verifier_id, passed=False, details="missing status_code")
            ok = 200 <= int(status) < 300
            return VerifierResult(id=self.verifier_id, passed=ok, details=f"status_code={status}")
        return VerifierResult(id=self.verifier_id, passed=False, details="non-dict last_result")


__all__ = ["ApiStatusOkVerifier"]

