"""
Anti-Thrash Guards - Prevents the agent from getting stuck in loops.

This module detects and handles:
1. Repeated action detector - same action called multiple times
2. Repeated file-read detector - reading same file over and over
3. No-progress detector - steps that don't advance the goal
4. Escalation rules - switch strategy or ask user

These guards prevent the "stuck reading CONTINUITY.md" behavior.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .state import StepRecord, StopReason, UnifiedAgentState

logger = logging.getLogger(__name__)


class ThrashType(str, Enum):
    """Types of thrashing behavior detected."""
    NONE = "none"
    REPEATED_ACTION = "repeated_action"
    REPEATED_FILE_READ = "repeated_file_read"
    NO_PROGRESS = "no_progress"
    SAME_ERROR = "same_error"


class EscalationAction(str, Enum):
    """Actions to take when thrashing is detected."""
    CONTINUE = "continue"           # Keep going (no thrash detected)
    WARN = "warn"                   # Log warning but continue
    SWITCH_STRATEGY = "switch"      # Try a different approach
    USE_CODEX = "use_codex"         # Hand off to Codex
    ASK_USER = "ask_user"           # Request human help
    STOP = "stop"                   # Stop execution


@dataclass
class ThrashDetection:
    """Result of thrash detection."""
    detected: bool
    thrash_type: ThrashType = ThrashType.NONE
    severity: int = 0  # 0-10, 10 is worst
    details: str = ""
    suggested_action: EscalationAction = EscalationAction.CONTINUE


@dataclass
class GuardConfig:
    """Configuration for guards."""
    # Thresholds
    max_repeated_actions: int = 3       # Same action in a row
    max_file_reads: int = 3             # Same file read count
    max_steps_no_progress: int = 5      # Steps without progress
    max_same_errors: int = 2            # Same error message

    # Behavior
    auto_escalate: bool = True          # Automatically escalate
    codex_fallback: bool = True         # Use Codex as fallback
    ask_user_enabled: bool = True       # Can ask user for help


class ThrashGuard:
    """
    Guard against thrashing behavior in the agent loop.

    Usage:
        guard = ThrashGuard()

        for step in agent_loop:
            detection = guard.check(state)
            if detection.detected:
                action = guard.get_escalation(detection)
                # Handle escalation
    """

    def __init__(self, config: Optional[GuardConfig] = None):
        self.config = config or GuardConfig()
        self._action_history: List[str] = []
        self._file_read_counts: Dict[str, int] = {}
        self._last_summary_hash: Optional[str] = None
        self._steps_since_progress: int = 0
        self._last_errors: List[str] = []

    def check(self, state: UnifiedAgentState) -> ThrashDetection:
        """
        Check for thrashing behavior.

        Args:
            state: Current agent state

        Returns:
            ThrashDetection with results
        """
        # Check repeated actions
        detection = self._check_repeated_actions(state)
        if detection.detected:
            return detection

        # Check repeated file reads
        detection = self._check_repeated_file_reads(state)
        if detection.detected:
            return detection

        # Check no progress
        detection = self._check_no_progress(state)
        if detection.detected:
            return detection

        # Check repeated errors
        detection = self._check_repeated_errors(state)
        if detection.detected:
            return detection

        return ThrashDetection(detected=False)

    def _check_repeated_actions(self, state: UnifiedAgentState) -> ThrashDetection:
        """Check if the same action is being repeated."""
        if not state.history:
            return ThrashDetection(detected=False)

        recent = state.get_recent_history(self.config.max_repeated_actions + 1)
        if len(recent) < self.config.max_repeated_actions:
            return ThrashDetection(detected=False)

        # Get last N actions
        actions = [(s.action, str(s.action_input)) for s in recent[-self.config.max_repeated_actions:]]

        # Check if all are the same
        if len(set(actions)) == 1:
            action_name = actions[0][0]
            return ThrashDetection(
                detected=True,
                thrash_type=ThrashType.REPEATED_ACTION,
                severity=7,
                details=f"Action '{action_name}' repeated {len(actions)} times with same args",
                suggested_action=EscalationAction.SWITCH_STRATEGY,
            )

        return ThrashDetection(detected=False)

    def _check_repeated_file_reads(self, state: UnifiedAgentState) -> ThrashDetection:
        """Check if the same file is being read repeatedly."""
        # Check state's file_read tracking
        for path, count in state.files_read.items():
            if count >= self.config.max_file_reads:
                return ThrashDetection(
                    detected=True,
                    thrash_type=ThrashType.REPEATED_FILE_READ,
                    severity=6,
                    details=f"File '{path}' read {count} times",
                    suggested_action=EscalationAction.SWITCH_STRATEGY,
                )

        return ThrashDetection(detected=False)

    def _check_no_progress(self, state: UnifiedAgentState) -> ThrashDetection:
        """Check if the agent is making progress."""
        if len(state.history) < self.config.max_steps_no_progress:
            return ThrashDetection(detected=False)

        recent = state.get_recent_history(self.config.max_steps_no_progress)

        # Check if all recent steps had errors
        all_errors = all(
            s.observation and s.observation.errors
            for s in recent if s.observation
        )
        if all_errors:
            return ThrashDetection(
                detected=True,
                thrash_type=ThrashType.NO_PROGRESS,
                severity=8,
                details=f"Last {len(recent)} steps all failed",
                suggested_action=EscalationAction.ASK_USER,
            )

        # Check if working_summary hasn't changed
        # (This is a heuristic - real progress should update the summary)
        summary_hash = hash(state.working_summary)
        if self._last_summary_hash == summary_hash and len(state.history) > 5:
            self._steps_since_progress += 1
            if self._steps_since_progress >= self.config.max_steps_no_progress:
                return ThrashDetection(
                    detected=True,
                    thrash_type=ThrashType.NO_PROGRESS,
                    severity=5,
                    details=f"No progress in {self._steps_since_progress} steps",
                    suggested_action=EscalationAction.USE_CODEX,
                )
        else:
            self._last_summary_hash = summary_hash
            self._steps_since_progress = 0

        return ThrashDetection(detected=False)

    def _check_repeated_errors(self, state: UnifiedAgentState) -> ThrashDetection:
        """Check if the same error keeps occurring."""
        if not state.history:
            return ThrashDetection(detected=False)

        recent = state.get_recent_history(self.config.max_same_errors + 1)
        errors = []
        for step in recent:
            if step.observation and step.observation.errors:
                # Get first error message
                if isinstance(step.observation.errors, list):
                    errors.append(step.observation.errors[0] if step.observation.errors else "")
                else:
                    errors.append(str(step.observation.errors))

        if len(errors) >= self.config.max_same_errors:
            # Check if last N errors are the same
            recent_errors = errors[-self.config.max_same_errors:]
            if len(set(recent_errors)) == 1 and recent_errors[0]:
                return ThrashDetection(
                    detected=True,
                    thrash_type=ThrashType.SAME_ERROR,
                    severity=7,
                    details=f"Same error repeated: {recent_errors[0][:100]}",
                    suggested_action=EscalationAction.ASK_USER,
                )

        return ThrashDetection(detected=False)

    def get_escalation(self, detection: ThrashDetection) -> Tuple[EscalationAction, str]:
        """
        Determine escalation action based on detection.

        Returns:
            Tuple of (action, message for user/log)
        """
        if not detection.detected:
            return EscalationAction.CONTINUE, ""

        action = detection.suggested_action

        # Build message
        messages = {
            EscalationAction.WARN: f"Warning: {detection.details}",
            EscalationAction.SWITCH_STRATEGY: f"Switching strategy due to: {detection.details}",
            EscalationAction.USE_CODEX: f"Handing off to Codex: {detection.details}",
            EscalationAction.ASK_USER: f"Need help: {detection.details}",
            EscalationAction.STOP: f"Stopping: {detection.details}",
        }

        message = messages.get(action, detection.details)

        # Log
        if detection.severity >= 7:
            logger.warning(f"[GUARD] {message}")
        else:
            logger.info(f"[GUARD] {message}")

        return action, message

    def get_recovery_suggestion(self, detection: ThrashDetection) -> str:
        """Get a suggestion for how to recover from thrashing."""
        suggestions = {
            ThrashType.REPEATED_ACTION: (
                "Try a different approach. Instead of repeating the same action, "
                "consider: reading related files, searching for alternatives, "
                "or breaking the task into smaller steps."
            ),
            ThrashType.REPEATED_FILE_READ: (
                "You've read this file multiple times. The information you need "
                "might be elsewhere. Try: searching other files, checking imports, "
                "or summarizing what you've learned so far."
            ),
            ThrashType.NO_PROGRESS: (
                "No progress detected. Consider: clarifying the goal, "
                "breaking it into smaller tasks, or asking for help."
            ),
            ThrashType.SAME_ERROR: (
                "The same error keeps occurring. Try: a completely different approach, "
                "fixing the underlying issue, or escalating to Codex for code changes."
            ),
        }
        return suggestions.get(detection.thrash_type, "Try a different approach.")

    def should_stop(self, state: UnifiedAgentState) -> Tuple[bool, StopReason, str]:
        """
        Check if the agent should stop due to thrashing.

        Returns:
            Tuple of (should_stop, reason, message)
        """
        detection = self.check(state)

        if not detection.detected:
            return False, StopReason.NONE, ""

        if detection.severity >= 9:
            return True, StopReason.STUCK, detection.details

        action, message = self.get_escalation(detection)

        if action == EscalationAction.STOP:
            return True, StopReason.STUCK, message

        return False, StopReason.NONE, ""


def check_guards(state: UnifiedAgentState, config: Optional[GuardConfig] = None) -> ThrashDetection:
    """
    Convenience function to check guards with default config.

    Args:
        state: Current agent state
        config: Optional guard configuration

    Returns:
        ThrashDetection result
    """
    guard = ThrashGuard(config)
    return guard.check(state)


__all__ = [
    "ThrashGuard",
    "ThrashDetection",
    "ThrashType",
    "EscalationAction",
    "GuardConfig",
    "check_guards",
]
