from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional
import os


ProfileName = Literal["fast", "deep", "audit"]


@dataclass(frozen=True)
class ProfileConfig:
    name: ProfileName
    workers: int
    plan_timeout_s: int
    plan_retry_timeout_s: int
    heartbeat_s: int
    max_files_to_read: int
    max_total_bytes_to_read: int
    max_glob_results: int
    max_web_sources: int
    allow_interactive: bool
    stage_checkpoints: bool


@dataclass
class RunUsage:
    files_read: int = 0
    bytes_read: int = 0
    glob_results: int = 0
    web_sources: int = 0

    def remaining_bytes(self, limit: int) -> int:
        return max(0, limit - self.bytes_read)

    def can_read_file(self, max_files: int) -> bool:
        return self.files_read < max_files

    def consume_file(self, bytes_read: int) -> None:
        self.files_read += 1
        self.bytes_read += max(0, int(bytes_read))

    def consume_glob(self, count: int) -> None:
        self.glob_results += max(0, int(count))

    def consume_web(self) -> None:
        self.web_sources += 1


_PROFILE_DEFAULTS: dict[ProfileName, ProfileConfig] = {
    "fast": ProfileConfig(
        name="fast",
        workers=2,
        plan_timeout_s=360,
        plan_retry_timeout_s=90,
        heartbeat_s=5,
        max_files_to_read=20,
        max_total_bytes_to_read=2_000_000,
        max_glob_results=200,
        max_web_sources=5,
        allow_interactive=False,
        stage_checkpoints=True,
    ),
    "deep": ProfileConfig(
        name="deep",
        workers=2,
        plan_timeout_s=900,
        plan_retry_timeout_s=240,
        heartbeat_s=5,
        max_files_to_read=100,
        max_total_bytes_to_read=20_000_000,
        max_glob_results=2000,
        max_web_sources=12,
        allow_interactive=False,
        stage_checkpoints=True,
    ),
    "audit": ProfileConfig(
        name="audit",
        workers=1,
        plan_timeout_s=1800,
        plan_retry_timeout_s=300,
        heartbeat_s=5,
        max_files_to_read=500,
        max_total_bytes_to_read=80_000_000,
        max_glob_results=10000,
        max_web_sources=25,
        allow_interactive=False,
        stage_checkpoints=True,
    ),
}


def resolve_profile(
    name: Optional[str] = None,
    *,
    env_keys: tuple[str, ...] = ("AUTO_PROFILE", "SWARM_PROFILE", "AGENT_PROFILE"),
) -> ProfileConfig:
    selected = (name or "").strip().lower()
    if not selected:
        for key in env_keys:
            val = os.getenv(key, "").strip().lower()
            if val:
                selected = val
                break
    if selected not in _PROFILE_DEFAULTS:
        selected = "fast"
    return _PROFILE_DEFAULTS[selected]
