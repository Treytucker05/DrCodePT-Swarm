from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Tuple


@dataclass
class LoopDetector:
    window: int = 8
    repeat_threshold: int = 3
    _recent: Deque[Tuple[str, str, str]] = field(default_factory=deque)

    def update(self, tool_name: str, args_hash: str, output_hash: str) -> bool:
        """
        Returns True if a loop is detected:
          repeated same (tool_name, args_hash, output_hash) >= repeat_threshold within the window.
        """
        signature = (tool_name, args_hash, output_hash)
        self._recent.append(signature)
        while len(self._recent) > self.window:
            self._recent.popleft()
        count = sum(1 for entry in self._recent if entry == signature)
        return count >= self.repeat_threshold
