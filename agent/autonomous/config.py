from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Tuple


@dataclass(frozen=True)
class AgentConfig:
    unsafe_mode: bool = False
    enable_web_gui: bool = False
    enable_desktop: bool = False
    allow_user_info_storage: bool = False
    memory_db_path: Optional[Path] = None
    pre_mortem_enabled: bool = False
    allow_human_ask: bool = False
    allow_fs_anywhere: bool = False
    fs_allowed_roots: Tuple[Path, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RunnerConfig:
    max_steps: int = 30
    timeout_seconds: int = 600
    cost_budget_usd: Optional[float] = None
    loop_repeat_threshold: int = 3
    loop_window: int = 8
    tool_max_retries: int = 2
    tool_retry_backoff_seconds: float = 0.8
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 1.2


@dataclass(frozen=True)
class PlannerConfig:
    mode: Literal["react", "plan_first"] = "react"
    num_candidates: int = 1
    max_plan_steps: int = 6


@dataclass(frozen=True)
class RunContext:
    run_id: str
    run_dir: Path
    workspace_dir: Path
