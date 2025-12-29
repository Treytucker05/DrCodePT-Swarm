"""
Base classes for the Skills system.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AuthStatus(str, Enum):
    """Authentication status for a skill."""
    AUTHENTICATED = "authenticated"
    NEEDS_AUTH = "needs_auth"
    AUTH_EXPIRED = "auth_expired"
    AUTH_FAILED = "auth_failed"
    NOT_CONFIGURED = "not_configured"


@dataclass
class SkillResult:
    """Result of a skill operation."""
    ok: bool
    data: Any = None
    error: Optional[str] = None
    needs_auth: bool = False
    auth_url: Optional[str] = None  # URL for OAuth if needed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error,
            "needs_auth": self.needs_auth,
            "auth_url": self.auth_url,
        }


class Skill(ABC):
    """
    Base class for all skills.

    A skill represents a complete capability for interacting with
    an external service. Skills handle their own auth, provide
    high-level operations, and report availability.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique skill identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        ...

    @property
    def requires_auth(self) -> bool:
        """Whether this skill requires authentication."""
        return True

    @abstractmethod
    def auth_status(self) -> AuthStatus:
        """Check current authentication status."""
        ...

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """List available operations for this skill."""
        ...

    def is_available(self) -> bool:
        """Check if the skill is ready to use."""
        status = self.auth_status()
        return status == AuthStatus.AUTHENTICATED or not self.requires_auth

    def begin_oauth(self) -> Optional[str]:
        """
        Start OAuth flow if needed.

        Returns:
            OAuth URL to open in browser, or None if not applicable
        """
        return None

    def complete_oauth(self, auth_code: str) -> SkillResult:
        """
        Complete OAuth flow with authorization code.

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            SkillResult indicating success/failure
        """
        return SkillResult(ok=False, error="OAuth not supported")
