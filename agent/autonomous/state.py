"""
Agent State - Unified state object for the ReAct loop.

This module defines the single source of truth for agent state during execution.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .models import Observation, Plan, Reflection, Step, ToolResult
from .pydantic_compat import model_dump, model_validate


class StopReason(str, Enum):
    """Reasons for stopping agent execution."""
    NONE = "none"                    # Still running
    GOAL_COMPLETE = "goal_complete"  # finish action called
    MAX_STEPS = "max_steps"          # Hit step limit
    MAX_TIME = "max_time"            # Hit timeout
    MAX_ERRORS = "max_errors"        # Too many consecutive errors
    USER_STOPPED = "user_stopped"    # User cancelled
    STUCK = "stuck"                  # No progress detected
    ERROR = "error"                  # Fatal error


@dataclass
class StepRecord:
    """Record of a single agent step."""
    step_number: int
    action: str
    action_input: Dict[str, Any]
    reasoning: str
    observation: Optional[Observation] = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0


def _sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8", errors="replace")).hexdigest()


@dataclass
class AgentState:
    task: str
    rolling_summary: str = ""
    observations: List[Observation] = field(default_factory=list)
    current_plan: Optional[Plan] = None
    current_step_idx: int = 0
    last_action_signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "rolling_summary": self.rolling_summary,
            "observations": [model_dump(o) for o in self.observations],
            "current_plan": model_dump(self.current_plan) if self.current_plan else None,
            "current_step_idx": self.current_step_idx,
            "last_action_signature": self.last_action_signature,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AgentState":
        task = str(data.get("task") or "")
        state = AgentState(task=task)
        state.rolling_summary = str(data.get("rolling_summary") or "")
        obs = data.get("observations") or []
        if isinstance(obs, list):
            for o in obs:
                try:
                    state.observations.append(model_validate(Observation, o))
                except Exception:
                    pass
        plan = data.get("current_plan")
        if isinstance(plan, dict):
            try:
                state.current_plan = model_validate(Plan, plan)
            except Exception:
                state.current_plan = None
        state.current_step_idx = int(data.get("current_step_idx") or 0)
        state.last_action_signature = data.get("last_action_signature")
        return state

    def add_observation(self, obs: Observation) -> None:
        self.observations.append(obs)

    def compact(self, *, keep_last: int = 12, max_total: int = 40) -> None:
        if len(self.observations) <= max_total:
            return
        old = self.observations[:-keep_last]
        keep = self.observations[-keep_last:]
        facts: List[str] = []
        for o in old:
            facts.extend(o.salient_facts[:2] or [])
        summary = "\n".join(facts[-200:])  # cap
        if summary:
            self.rolling_summary = (self.rolling_summary + "\n" + summary).strip()
            self.rolling_summary = self.rolling_summary[-8000:]
        self.observations = keep

    def state_fingerprint(self) -> str:
        last_obs = self.observations[-1] if self.observations else None
        last_obs_sig = None
        if last_obs is not None:
            last_obs_sig = {
                "source": last_obs.source,
                "errors": last_obs.errors,
                "salient_facts": last_obs.salient_facts,
                "parsed": last_obs.parsed,
            }
        payload: Dict[str, Any] = {
            "summary_tail": self.rolling_summary[-800:],
            "last_obs": last_obs_sig,
        }
        return _sha256_json(payload)


@dataclass
class UnifiedAgentState:
    """
    Complete unified state for the agent during execution.

    This is the new single source of truth for the ReAct loop.
    Replaces fragmented state across multiple objects.
    """
    # Identity
    run_id: str = field(default_factory=lambda: uuid4().hex[:12])
    run_dir: Optional[Path] = None

    # Goal
    goal: str = ""
    original_input: str = ""

    # Progress (uses existing AgentState for backward compat)
    _legacy_state: Optional[AgentState] = field(default=None, repr=False)
    step: int = 0
    history: List[StepRecord] = field(default_factory=list)

    # Context
    working_summary: str = ""
    memories: List[str] = field(default_factory=list)

    # Budgets
    max_steps: int = 30
    max_time_seconds: int = 600
    max_consecutive_errors: int = 3

    # Tracking
    start_time: datetime = field(default_factory=datetime.now)
    consecutive_errors: int = 0
    total_errors: int = 0
    files_read: Dict[str, int] = field(default_factory=dict)

    # Termination
    stop_reason: StopReason = StopReason.NONE
    final_result: Optional[str] = None

    def __post_init__(self):
        """Initialize legacy state for backward compatibility."""
        if self._legacy_state is None:
            self._legacy_state = AgentState(task=self.goal)

    @property
    def is_running(self) -> bool:
        return self.stop_reason == StopReason.NONE

    @property
    def elapsed_seconds(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def remaining_steps(self) -> int:
        return max(0, self.max_steps - self.step)

    def should_stop(self) -> StopReason:
        """Check if agent should stop and why."""
        if self.step >= self.max_steps:
            return StopReason.MAX_STEPS
        if self.elapsed_seconds >= self.max_time_seconds:
            return StopReason.MAX_TIME
        if self.consecutive_errors >= self.max_consecutive_errors:
            return StopReason.MAX_ERRORS
        return StopReason.NONE

    def record_step(
        self,
        action: str,
        action_input: Dict[str, Any],
        reasoning: str,
        observation: Optional[Observation] = None,
        duration: float = 0.0,
    ) -> StepRecord:
        """Record a completed step."""
        record = StepRecord(
            step_number=self.step,
            action=action,
            action_input=action_input,
            reasoning=reasoning,
            observation=observation,
            duration_seconds=duration,
        )
        self.history.append(record)
        self.step += 1

        # Update legacy state
        if observation and self._legacy_state:
            self._legacy_state.add_observation(observation)

        if observation:
            if not observation.errors:
                self.consecutive_errors = 0
            else:
                self.consecutive_errors += 1
                self.total_errors += 1

        return record

    def record_file_read(self, path: str) -> int:
        """Track file reads for anti-thrash detection."""
        count = self.files_read.get(path, 0) + 1
        self.files_read[path] = count
        return count

    def finish(self, summary: str, success: bool = True) -> None:
        """Mark agent as finished."""
        self.stop_reason = StopReason.GOAL_COMPLETE if success else StopReason.ERROR
        self.final_result = summary

    def stop(self, reason: StopReason, message: str = "") -> None:
        """Stop agent with specified reason."""
        self.stop_reason = reason
        self.final_result = message

    def get_recent_history(self, n: int = 5) -> List[StepRecord]:
        """Get last N steps."""
        return self.history[-n:] if self.history else []

    def format_history_for_prompt(self, n: int = 5) -> str:
        """Format recent history for inclusion in prompts."""
        recent = self.get_recent_history(n)
        if not recent:
            return "No previous actions."

        lines = []
        for step in recent:
            obs_text = step.observation.raw[:200] if step.observation else ""
            if step.observation and len(step.observation.raw) > 200:
                obs_text += "..."
            lines.append(
                f"Step {step.step_number}: {step.action}({step.action_input})\n"
                f"  Reasoning: {step.reasoning}\n"
                f"  Result: {obs_text}"
            )
        return "\n\n".join(lines)


def create_unified_state(
    goal: str,
    *,
    run_dir: Optional[Path] = None,
    max_steps: int = 30,
    max_time_seconds: int = 600,
) -> UnifiedAgentState:
    """Create initial unified agent state for a new task."""
    return UnifiedAgentState(
        goal=goal,
        original_input=goal,
        run_dir=run_dir,
        max_steps=max_steps,
        max_time_seconds=max_time_seconds,
    )


__all__ = [
    "AgentState",
    "UnifiedAgentState",
    "StepRecord",
    "StopReason",
    "create_unified_state",
]
