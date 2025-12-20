from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StubLLM:
    """
    Deterministic LLM stub for unit tests.

    Provide a list of dict responses; each `complete_json(...)` call returns the next dict.
    """

    responses: List[Dict[str, Any]]
    provider: str = "stub"
    model: str = "stub"
    calls: List[str] = field(default_factory=list)
    _idx: int = 0

    def complete_json(
        self,
        prompt: str,
        *,
        schema_path: Path,  # noqa: ARG002
        timeout_seconds: Optional[int] = None,  # noqa: ARG002
    ) -> Dict[str, Any]:
        self.calls.append(prompt)
        if self._idx >= len(self.responses):
            raise RuntimeError("StubLLM out of responses")
        out = self.responses[self._idx]
        self._idx += 1
        return out

    def reason_json(
        self,
        prompt: str,
        *,
        schema_path: Path,  # noqa: ARG002
        timeout_seconds: Optional[int] = None,  # noqa: ARG002
    ) -> Dict[str, Any]:
        return self.complete_json(
            prompt,
            schema_path=schema_path,
            timeout_seconds=timeout_seconds,
        )
