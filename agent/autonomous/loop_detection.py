"""Loop detection for autonomous agents."""

import logging
import hashlib
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


def _hash_dict(d: dict) -> str:
    """Hash a dictionary."""
    import json
    s = json.dumps(d, sort_keys=True, default=str)
    return hashlib.md5(s.encode()).hexdigest()


def _hash_str(s: str) -> str:
    """Hash a string."""
    return hashlib.md5(s.encode()).hexdigest()


class LoopDetector:
    """Detect loops in agent execution.

    A loop is defined as:
    - Same tool executed multiple times
    - With the same arguments
    - Producing the same output
    """

    def __init__(self, max_repeats: int = 3):
        """Initialize loop detector.

        Args:
            max_repeats: Number of identical repeats to trigger loop detection
        """
        self.max_repeats = max_repeats
        self.history: Dict[str, List[str]] = {}  # key -> [output_hashes]

    def check(
        self,
        tool_name: str,
        args: dict,
        output: str,
    ) -> Tuple[bool, Optional[str]]:
        """Check if this is a loop.

        Args:
            tool_name: Name of tool executed
            args: Arguments passed to tool
            output: Output from tool

        Returns:
            Tuple of (is_loop, message)
        """
        # Create key from tool name and args
        args_hash = _hash_dict(args)
        output_hash = _hash_str(output)
        key = f"{tool_name}:{args_hash}"

        # Initialize history for this key if needed
        if key not in self.history:
            self.history[key] = []

        # Add output hash to history
        self.history[key].append(output_hash)

        # Check if we have enough repeats
        if len(self.history[key]) < self.max_repeats:
            return False, None

        # Check if last N outputs are identical
        recent_outputs = self.history[key][-self.max_repeats:]
        if len(set(recent_outputs)) == 1:
            # All recent outputs are identical
            message = (
                f"Loop detected: {tool_name} produced identical output "
                f"{self.max_repeats} times with args {args}"
            )
            logger.error(message)
            return True, message

        return False, None

    def reset(self) -> None:
        """Reset loop detection history."""
        self.history.clear()

    def get_history(self) -> Dict[str, List[str]]:
        """Get execution history."""
        return self.history.copy()
