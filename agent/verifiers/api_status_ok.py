from __future__ import annotations

from typing import Dict

from .base import Verifier, VerifyResult


class ApiStatusOkVerifier(Verifier):
    def verify(self, context: Dict) -> VerifyResult:
        expected = int(self.args.get("expected_status", 200))
        result = context.get("last_result") or {}
        status = None
        if isinstance(result, dict):
            if "status_code" in result:
                status = result.get("status_code")
            else:
                status = result.get("output", {}).get("status_code")
        else:
            status = getattr(result, "output", {}).get("status_code", None)

        passed = status == expected
        return VerifyResult(passed, f"status={status}, expected={expected}")
