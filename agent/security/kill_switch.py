"""
Kill Switch - Emergency stop mechanism for the agent.

The kill switch provides an immediate way to stop all agent execution.
It works by checking for the existence of a file or environment flag.

Usage:
    # Check before each action
    if check_kill_switch():
        raise AgentKilledException("Kill switch activated")

    # Or use the context manager
    with KillSwitch.guarded():
        # Agent code here
        pass
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default kill switch file path
DEFAULT_KILL_SWITCH_FILE = Path.home() / ".agent_kill_switch"


class AgentKilledException(Exception):
    """Exception raised when kill switch is activated."""
    pass


class KillSwitch:
    """
    Kill switch for emergency agent shutdown.

    The kill switch can be triggered by:
    1. Creating the kill switch file
    2. Setting AGENT_KILL_SWITCH=1 environment variable
    3. Calling activate() programmatically
    """

    _active = False  # Class-level flag for programmatic activation

    def __init__(
        self,
        file_path: Optional[Path] = None,
        env_var: str = "AGENT_KILL_SWITCH",
    ):
        """
        Initialize kill switch.

        Args:
            file_path: Path to kill switch file. If exists, switch is active.
            env_var: Environment variable to check.
        """
        self.file_path = file_path or Path(
            os.environ.get("AGENT_KILL_SWITCH_FILE", str(DEFAULT_KILL_SWITCH_FILE))
        )
        self.env_var = env_var

    def is_active(self) -> bool:
        """Check if kill switch is active."""
        # Check class-level flag
        if KillSwitch._active:
            return True

        # Check environment variable
        if os.environ.get(self.env_var, "").lower() in ("1", "true", "yes"):
            return True

        # Check file existence
        if self.file_path.exists():
            return True

        return False

    def activate(self, reason: str = "Manual activation") -> None:
        """
        Activate the kill switch.

        This creates the kill switch file with the reason.
        """
        KillSwitch._active = True
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(f"Kill switch activated: {reason}\n")
            logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
        except Exception as e:
            logger.error(f"Could not write kill switch file: {e}")

    def deactivate(self) -> None:
        """
        Deactivate the kill switch.

        This removes the kill switch file.
        """
        KillSwitch._active = False
        try:
            if self.file_path.exists():
                self.file_path.unlink()
            logger.info("Kill switch deactivated")
        except Exception as e:
            logger.error(f"Could not remove kill switch file: {e}")

    def check_or_raise(self) -> None:
        """Check kill switch and raise if active."""
        if self.is_active():
            raise AgentKilledException(
                "Kill switch is active. Agent execution stopped. "
                "Remove the kill switch file or set AGENT_KILL_SWITCH=0 to resume."
            )

    @classmethod
    @contextmanager
    def guarded(cls, file_path: Optional[Path] = None):
        """
        Context manager that checks kill switch before each yield.

        Usage:
            with KillSwitch.guarded():
                for step in steps:
                    yield  # Checks kill switch
                    execute_step()
        """
        switch = cls(file_path)
        switch.check_or_raise()
        yield switch

    @classmethod
    def reset(cls) -> None:
        """Reset the class-level flag (for testing)."""
        cls._active = False


# Global instance for convenience
_default_switch: Optional[KillSwitch] = None


def get_kill_switch() -> KillSwitch:
    """Get the default kill switch instance."""
    global _default_switch
    if _default_switch is None:
        _default_switch = KillSwitch()
    return _default_switch


def check_kill_switch() -> bool:
    """
    Check if kill switch is active.

    Call this before each agent action.
    Returns True if kill switch is active (should stop).
    """
    return get_kill_switch().is_active()


def activate_kill_switch(reason: str = "Manual activation") -> None:
    """Activate the kill switch with a reason."""
    get_kill_switch().activate(reason)


def deactivate_kill_switch() -> None:
    """Deactivate the kill switch."""
    get_kill_switch().deactivate()
