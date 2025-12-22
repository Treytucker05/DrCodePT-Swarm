"""Execution profiles for different analysis depths."""

import logging
from dataclasses import dataclass
from typing import Dict, Literal

logger = logging.getLogger(__name__)

ProfileType = Literal["fast", "deep", "audit"]


@dataclass
class Profile:
    """Execution profile with budgets and settings.

    Attributes:
        name: Profile name (fast, deep, audit)
        max_steps: Maximum planning steps
        timeout_seconds: Total execution timeout
        max_files_to_read: Maximum files to read
        max_bytes_to_read: Maximum total bytes to read
        max_web_sources: Maximum web sources to fetch
        max_tool_calls: Maximum tool calls allowed
        enable_web_search: Whether to enable web search
        enable_code_execution: Whether to enable code execution
        enable_file_write: Whether to enable file writes
        checkpoint_interval: Steps between checkpoints
    """
    name: ProfileType
    max_steps: int
    timeout_seconds: int
    max_files_to_read: int
    max_bytes_to_read: int
    max_web_sources: int
    max_tool_calls: int
    enable_web_search: bool
    enable_code_execution: bool
    enable_file_write: bool
    checkpoint_interval: int


# Fast profile: quick analysis, limited scope
FAST_PROFILE = Profile(
    name="fast",
    max_steps=20,
    timeout_seconds=300,
    max_files_to_read=50,
    max_bytes_to_read=5_000_000,
    max_web_sources=3,
    max_tool_calls=50,
    enable_web_search=True,
    enable_code_execution=False,
    enable_file_write=False,
    checkpoint_interval=10,
)

# Deep profile: thorough analysis, moderate scope
DEEP_PROFILE = Profile(
    name="deep",
    max_steps=50,
    timeout_seconds=1800,
    max_files_to_read=200,
    max_bytes_to_read=50_000_000,
    max_web_sources=10,
    max_tool_calls=200,
    enable_web_search=True,
    enable_code_execution=True,
    enable_file_write=True,
    checkpoint_interval=5,
)

# Audit profile: comprehensive analysis, full scope
AUDIT_PROFILE = Profile(
    name="audit",
    max_steps=100,
    timeout_seconds=3600,
    max_files_to_read=500,
    max_bytes_to_read=200_000_000,
    max_web_sources=20,
    max_tool_calls=500,
    enable_web_search=True,
    enable_code_execution=True,
    enable_file_write=True,
    checkpoint_interval=1,
)

# Profile registry
PROFILES: Dict[ProfileType, Profile] = {
    "fast": FAST_PROFILE,
    "deep": DEEP_PROFILE,
    "audit": AUDIT_PROFILE,
}


def get_profile(name: ProfileType) -> Profile:
    """Get profile by name.

    Args:
        name: Profile name (fast, deep, audit)

    Returns:
        Profile object

    Raises:
        ValueError: If profile name not found
    """
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}. Available: {list(PROFILES.keys())}")
    return PROFILES[name]


def list_profiles() -> Dict[str, Profile]:
    """List all available profiles.

    Returns:
        Dict of profile_name -> Profile
    """
    return PROFILES.copy()
