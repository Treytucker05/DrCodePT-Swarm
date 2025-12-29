"""
Skills System - First-class integrations with external services.

Skills differ from tools in that they represent complete, coherent
capabilities for interacting with external services (like Google Calendar,
browser automation, file system operations).

Each skill:
- Handles its own authentication
- Provides a clean, high-level API
- Can be composed with other skills
- Reports its availability status
"""

from .base import Skill, SkillResult, AuthStatus
from .google_calendar import GoogleCalendarSkill
from .registry import SkillRegistry, get_skill_registry

CalendarSkill = GoogleCalendarSkill

__all__ = [
    "Skill",
    "SkillResult",
    "AuthStatus",
    "GoogleCalendarSkill",
    "CalendarSkill",
    "SkillRegistry",
    "get_skill_registry",
]
