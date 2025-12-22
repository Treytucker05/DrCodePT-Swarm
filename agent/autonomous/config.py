from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Tuple

from agent.config.profile import ProfileConfig, RunUsage, resolve_profile
from .exceptions import ConfigurationError


@dataclass(frozen=True)
class AgentConfig:
    unsafe_mode: bool = False
    enable_web_gui: bool = False
    enable_desktop: bool = False
    allow_user_info_storage: bool = False
    allow_interactive_tools: bool = True
    """Whether to allow interactive tools (human_ask, etc.).

    In swarm mode, this should be False to prevent workers from blocking.
    """
    memory_db_path: Optional[Path] = None
    pre_mortem_enabled: bool = False
    allow_human_ask: bool = False
    allow_fs_anywhere: bool = False
    fs_allowed_roots: Tuple[Path, ...] = field(default_factory=tuple)
    profile: ProfileConfig = field(default_factory=resolve_profile)


@dataclass(frozen=True)
class RunnerConfig:
    max_steps: int = 30
    timeout_seconds: int = 600
    profile: str = "deep"
    """Execution profile: fast, deep, or audit."""
    cost_budget_usd: Optional[float] = None
    llm_heartbeat_seconds: Optional[float] = None
    llm_plan_timeout_seconds: Optional[int] = 360
    llm_plan_retry_timeout_seconds: Optional[int] = 90
    loop_repeat_threshold: int = 3
    loop_window: int = 8
    no_state_change_threshold: int = 3
    tool_max_retries: int = 2
    tool_retry_backoff_seconds: float = 0.8
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 1.2

    def __post_init__(self) -> None:
        if self.max_steps <= 0:
            raise ConfigurationError("max_steps must be > 0")
        if self.timeout_seconds <= 0:
            raise ConfigurationError("timeout_seconds must be > 0")
        if self.llm_plan_timeout_seconds is not None and self.llm_plan_timeout_seconds <= 0:
            raise ConfigurationError("llm_plan_timeout_seconds must be > 0")
        if self.llm_plan_retry_timeout_seconds is not None and self.llm_plan_retry_timeout_seconds <= 0:
            raise ConfigurationError("llm_plan_retry_timeout_seconds must be > 0")
        if self.llm_heartbeat_seconds is not None and self.llm_heartbeat_seconds < 0:
            raise ConfigurationError("llm_heartbeat_seconds must be >= 0")


@dataclass(frozen=True)
class PlannerConfig:
    mode: Literal["react", "plan_first"] = "react"
    num_candidates: int = 3
    max_plan_steps: int = 6
    use_dppm: bool = True
    use_tot: bool = True


@dataclass(frozen=True)
class RunContext:
    run_id: str
    run_dir: Path
    workspace_dir: Path
    profile: Optional[ProfileConfig] = None
    usage: Optional[RunUsage] = None
