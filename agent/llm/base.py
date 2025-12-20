from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Protocol


class LLMClient(Protocol):
    provider: str
    model: str

    def complete_json(
        self,
        prompt: str,
        *,
        schema_path: Path,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Return a JSON object conforming to the provided JSON Schema.
        """

