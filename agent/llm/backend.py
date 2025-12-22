from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class RunConfig:
    schema_path: Path
    profile: str = "reason"
    timeout_seconds: Optional[int] = None


@dataclass(frozen=True)
class RunResult:
    data: Dict[str, Any]
    workdir: Path


class LLMBackend(Protocol):
    def run(
        self,
        *,
        prompt: str,
        workdir: Optional[Path],
        run_dir: Optional[Path],
        config: RunConfig,
    ) -> RunResult:
        """
        Execute an LLM run with explicit context. Implementations decide how to
        route profiles and honor workdir/run_dir. Terminal output is incidental.
        """
