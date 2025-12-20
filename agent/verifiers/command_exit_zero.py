from __future__ import annotations

from typing import Any, Dict

from .base import VerifierAdapter, VerifierResult


class CommandExitZeroVerifier(VerifierAdapter):
    verifier_id = "command_exit_zero"

    def verify(self, context: Dict[str, Any]) -> VerifierResult:
        last = context.get("last_result") or {}
        if isinstance(last, dict):
            exit_code = last.get("exit_code")
            if exit_code is None:
                # Fall back to overall tool success if no exit code was captured.
                passed = bool(context.get("tool_success", False))
                return VerifierResult(id=self.verifier_id, passed=passed, details="no exit_code in last_result")
            passed = int(exit_code) == 0
            return VerifierResult(id=self.verifier_id, passed=passed, details=f"exit_code={exit_code}")
        return VerifierResult(id=self.verifier_id, passed=bool(context.get("tool_success", False)), details="non-dict last_result")


__all__ = ["CommandExitZeroVerifier"]

