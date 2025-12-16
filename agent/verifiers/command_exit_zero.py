from __future__ import annotations

from typing import Dict

from .base import Verifier, VerifyResult


class CommandExitZeroVerifier(Verifier):
    def verify(self, context: Dict) -> VerifyResult:
        result = context.get("last_result") or {}
        exit_code = None
        if isinstance(result, dict):
            if "exit_code" in result:
                exit_code = result.get("exit_code")
            else:
                exit_code = result.get("output", {}).get("exit_code")
        else:
            exit_code = getattr(result, "output", {}).get("exit_code", None)

        passed = exit_code == 0
        return VerifyResult(passed, f"exit_code={exit_code}")
