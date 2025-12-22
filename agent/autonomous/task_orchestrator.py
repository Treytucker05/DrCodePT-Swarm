from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class TaskOrchestrator:
    def failed_dependencies(self, deps: Iterable[str], status_by_id: Dict[str, str]) -> List[str]:
        return [d for d in deps if status_by_id.get(d) == "failed"]

    def should_reduce(self, deps: Iterable[str], status_by_id: Dict[str, str]) -> Tuple[bool, List[str]]:
        failed = self.failed_dependencies(deps, status_by_id)
        return bool(failed), failed
