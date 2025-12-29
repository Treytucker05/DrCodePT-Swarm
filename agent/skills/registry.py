"""
Skill Registry - Manages available skills.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Type

from .base import AuthStatus, Skill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Registry for managing available skills.

    Skills are registered by name and can be queried for availability.
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """
        Register a skill.

        Args:
            skill: Skill instance to register
        """
        self._skills[skill.name] = skill
        logger.debug(f"Registered skill: {skill.name}")

    def get(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.

        Args:
            name: Skill name

        Returns:
            Skill instance or None if not found
        """
        return self._skills.get(name)

    def list_skills(self) -> List[str]:
        """Get names of all registered skills."""
        return list(self._skills.keys())

    def list_available(self) -> List[str]:
        """Get names of skills that are ready to use."""
        return [
            name for name, skill in self._skills.items()
            if skill.is_available()
        ]

    def get_status(self) -> Dict[str, Dict[str, str]]:
        """
        Get status of all registered skills.

        Returns:
            Dict mapping skill name to status info
        """
        result = {}
        for name, skill in self._skills.items():
            status = skill.auth_status()
            result[name] = {
                "name": name,
                "description": skill.description,
                "auth_status": status.value,
                "available": skill.is_available(),
                "capabilities": skill.get_capabilities(),
            }
        return result


# Global registry
_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """Get the global skill registry."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
        _register_default_skills(_registry)
    return _registry


def _register_default_skills(registry: SkillRegistry) -> None:
    """Register default skills."""
    try:
        from .calendar import CalendarSkill
        registry.register(CalendarSkill())
    except Exception as e:
        logger.debug(f"Failed to register calendar skill: {e}")

    # Future skills can be added here:
    # - BrowserSkill
    # - FilesystemSkill
    # - EmailSkill
    # - etc.
