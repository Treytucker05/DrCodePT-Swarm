from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Tuple


@dataclass
class LoopDetector:
    window: int = 8
    repeat_threshold: int = 3
    _recent: Deque[Tuple[str, str]] = field(default_factory=deque)

    def update(self, action_signature: str, state_fingerprint: str) -> bool:
        """
        Returns True if a loop is detected:
          repeated same (action_signature, state_fingerprint) >= repeat_threshold within the window.
        """
        self._recent.append((action_signature, state_fingerprint))
        while len(self._recent) > self.window:
            self._recent.popleft()

        count = sum(1 for a, s in self._recent if a == action_signature and s == state_fingerprint)
        return count >= self.repeat_threshold

