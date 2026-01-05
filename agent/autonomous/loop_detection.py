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

    Read-only tools are exempt from loop detection since getting
    the same result multiple times is expected behavior for queries.
    """

    # Read-only tools that should be exempt from loop detection
    # These tools query data without side effects, so identical results are valid
    EXEMPT_TOOLS = {
        # Calendar & Tasks
        "list_calendar_events",
        "get_free_time",
        "check_calendar_conflicts",
        "list_all_tasks",
        "search_tasks",
        "get_task_details",
        # File system reads
        "file_read",
        "list_dir",
        "glob_paths",
        "file_search",
        # Web reads
        "web_fetch",
        "web_search",
        # System info
        "system_info",
        "clipboard_get",
        # Memory reads
        "memory_search",
    }

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
        # Skip loop detection for read-only tools
        # These tools query data without side effects, so identical results are expected
        if tool_name in self.EXEMPT_TOOLS:
            logger.debug(f"Loop detection skipped for read-only tool: {tool_name}")
            return False, None

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

    def update(self, tool_name: str, args_hash: str, output_hash: str) -> bool:
        """Update detector with pre-hashed args and output values. Returns True if loop detected.

        This is a convenient adapter for callers that already hash args/output. It behaves like `check`
        but expects pre-computed hashes and returns a boolean.
        """
        # Skip loop detection for read-only tools
        if tool_name in self.EXEMPT_TOOLS:
            logger.debug(f"Loop detection skipped for read-only tool: {tool_name}")
            return False

        key = f"{tool_name}:{args_hash}"
        if key not in self.history:
            self.history[key] = []
        self.history[key].append(output_hash)
        # If we don't have enough samples yet, not a loop
        if len(self.history[key]) < self.max_repeats:
            return False
        recent = self.history[key][-self.max_repeats:]
        if len(set(recent)) == 1:
            logger.error(f"Loop detected via update: {tool_name} args_hash={args_hash}")
            return True
        return False
