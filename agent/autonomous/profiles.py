from dataclasses import dataclass
from typing import Dict, Literal

ProfileType = Literal["fast", "deep", "audit"]

@dataclass
class Profile:
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

FAST_PROFILE = Profile("fast", 20, 300, 50, 5_000_000, 3, 50, True, False, False, 10)
DEEP_PROFILE = Profile("deep", 50, 1800, 200, 50_000_000, 10, 200, True, True, True, 5)
AUDIT_PROFILE = Profile("audit", 100, 3600, 500, 200_000_000, 20, 500, True, True, True, 1)

PROFILES: Dict[ProfileType, Profile] = {"fast": FAST_PROFILE, "deep": DEEP_PROFILE, "audit": AUDIT_PROFILE}

def get_profile(name: ProfileType) -> Profile:
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}")
    return PROFILES[name]


def list_profiles() -> list[str]:
    """Return available profile names."""
    return list(PROFILES.keys())
