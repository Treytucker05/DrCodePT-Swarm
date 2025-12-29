"""
Reflector - Learn from task executions and store lessons.

This module provides reflection capabilities that:
- Analyze task execution outcomes
- Generate lessons learned
- Store lessons to persistent memory
- Retrieve relevant lessons for future tasks
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .unified_memory import get_memory, store_lesson, store_experience

logger = logging.getLogger(__name__)


@dataclass
class TaskExecution:
    """Represents a completed task execution."""
    task: str
    result: str
    success: bool
    steps: List[Dict[str, Any]]
    errors: List[str]
    duration_seconds: float
    tools_used: List[str]


@dataclass
class Reflection:
    """A reflection on a task execution."""
    task: str
    outcome: str  # "success" | "failure" | "partial"
    lesson: str
    what_worked: List[str]
    what_failed: List[str]
    improvement: str
    confidence: float  # 0-1, how confident in the lesson


class Reflector:
    """
    Generates and stores reflections from task executions.

    Uses LLM to analyze outcomes and extract lessons, then
    stores them to memory for future retrieval.
    """

    def __init__(self, llm_client=None):
        """
        Initialize reflector.

        Args:
            llm_client: Optional LLM client for generating reflections.
                       If None, uses simple heuristic-based reflection.
        """
        self._llm = llm_client

    def reflect(self, execution: TaskExecution) -> Reflection:
        """
        Generate a reflection from a task execution.

        Args:
            execution: The completed task execution

        Returns:
            Reflection with lessons learned
        """
        # Determine outcome
        if execution.success and not execution.errors:
            outcome = "success"
        elif execution.success and execution.errors:
            outcome = "partial"
        else:
            outcome = "failure"

        # Extract what worked/failed
        what_worked = []
        what_failed = []

        for step in execution.steps:
            if step.get("success", True):
                what_worked.append(step.get("action", "unknown action"))
            else:
                what_failed.append(step.get("action", "unknown action"))

        # Generate lesson
        if self._llm:
            reflection = self._reflect_with_llm(execution, outcome, what_worked, what_failed)
        else:
            reflection = self._reflect_heuristic(execution, outcome, what_worked, what_failed)

        # Store to memory
        self._store_reflection(reflection, execution)

        return reflection

    def _reflect_heuristic(
        self,
        execution: TaskExecution,
        outcome: str,
        what_worked: List[str],
        what_failed: List[str],
    ) -> Reflection:
        """Generate reflection using simple heuristics."""
        # Generate lesson based on outcome
        if outcome == "success":
            lesson = f"Successfully completed '{execution.task}' using {len(execution.tools_used)} tools."
            improvement = "Continue using this approach for similar tasks."
            confidence = 0.9
        elif outcome == "partial":
            lesson = f"Partially completed '{execution.task}' but encountered {len(execution.errors)} errors."
            improvement = "Handle errors more gracefully: " + (execution.errors[0] if execution.errors else "unknown")
            confidence = 0.6
        else:
            lesson = f"Failed to complete '{execution.task}'. Errors: {', '.join(execution.errors[:2])}"
            improvement = "Need to find alternative approach or fix underlying issues."
            confidence = 0.4

        return Reflection(
            task=execution.task,
            outcome=outcome,
            lesson=lesson,
            what_worked=what_worked,
            what_failed=what_failed,
            improvement=improvement,
            confidence=confidence,
        )

    def _reflect_with_llm(
        self,
        execution: TaskExecution,
        outcome: str,
        what_worked: List[str],
        what_failed: List[str],
    ) -> Reflection:
        """Generate reflection using LLM."""
        try:
            prompt = f"""Analyze this task execution and provide a brief lesson learned.

Task: {execution.task}
Outcome: {outcome}
Steps taken: {len(execution.steps)}
Tools used: {', '.join(execution.tools_used)}
Errors: {', '.join(execution.errors) if execution.errors else 'None'}
Duration: {execution.duration_seconds:.1f}s

Provide:
1. A concise lesson (1-2 sentences)
2. One specific improvement suggestion

Format: LESSON: <lesson>\nIMPROVEMENT: <suggestion>"""

            response = self._llm.chat(prompt)

            # Parse response
            lesson = ""
            improvement = ""
            for line in response.content.split("\n"):
                if line.startswith("LESSON:"):
                    lesson = line[7:].strip()
                elif line.startswith("IMPROVEMENT:"):
                    improvement = line[12:].strip()

            if not lesson:
                # Fallback to heuristic
                return self._reflect_heuristic(execution, outcome, what_worked, what_failed)

            return Reflection(
                task=execution.task,
                outcome=outcome,
                lesson=lesson,
                what_worked=what_worked,
                what_failed=what_failed,
                improvement=improvement,
                confidence=0.8,
            )
        except Exception as e:
            logger.warning(f"LLM reflection failed, using heuristic: {e}")
            return self._reflect_heuristic(execution, outcome, what_worked, what_failed)

    def _store_reflection(self, reflection: Reflection, execution: TaskExecution) -> None:
        """Store reflection to memory."""
        try:
            # Store the lesson
            store_lesson(
                lesson=reflection.lesson,
                context=f"Task: {reflection.task}, Outcome: {reflection.outcome}",
                tags=[reflection.outcome, *execution.tools_used[:3]],
            )

            # Store the experience
            store_experience(
                task=execution.task,
                result=execution.result,
                success=execution.success,
                duration_seconds=execution.duration_seconds,
                tools_used=execution.tools_used,
            )

            logger.info(f"Stored reflection for task: {execution.task[:50]}...")
        except Exception as e:
            logger.error(f"Failed to store reflection: {e}")


# Convenience functions

def reflect_on_task(
    task: str,
    result: str,
    success: bool,
    steps: Optional[List[Dict[str, Any]]] = None,
    errors: Optional[List[str]] = None,
    duration_seconds: float = 0.0,
    tools_used: Optional[List[str]] = None,
) -> Reflection:
    """
    Reflect on a completed task and store the lesson.

    Args:
        task: The task that was executed
        result: The outcome/result
        success: Whether it succeeded
        steps: List of execution steps
        errors: List of errors encountered
        duration_seconds: How long it took
        tools_used: Tools that were used

    Returns:
        Reflection with lessons learned
    """
    execution = TaskExecution(
        task=task,
        result=result,
        success=success,
        steps=steps or [],
        errors=errors or [],
        duration_seconds=duration_seconds,
        tools_used=tools_used or [],
    )

    reflector = Reflector()
    return reflector.reflect(execution)


def get_relevant_lessons(task: str, limit: int = 3) -> List[str]:
    """
    Retrieve relevant lessons for a task.

    Args:
        task: The task to find lessons for
        limit: Maximum number of lessons

    Returns:
        List of lesson strings
    """
    memory = get_memory()
    memories = memory.retrieve(
        task,
        kinds=["knowledge"],
        limit=limit,
    )

    lessons = []
    for m in memories:
        if "Lesson:" in m.content:
            # Extract just the lesson part
            lesson = m.content.split("Lesson:", 1)[1].split("\n")[0].strip()
            lessons.append(lesson)
        else:
            lessons.append(m.content)

    return lessons
