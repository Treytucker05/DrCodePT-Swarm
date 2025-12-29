"""
Unified Agent - Single entry point for all task execution.

This is the main agent class that coordinates:
1. Orchestrator (strategy selection)
2. Planning (ReAct or Plan-First)
3. Tool execution
4. Memory and reflection
5. Safety checks

It replaces the fragmented multi-mode system with a unified approach.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .intelligent_orchestrator import IntelligentOrchestrator, Strategy, RiskLevel

logger = logging.getLogger(__name__)


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    summary: str
    steps_taken: int = 0
    actions: List[Dict[str, Any]] = field(default_factory=list)
    strategy: Optional[Strategy] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    run_id: str = field(default_factory=lambda: uuid4().hex[:12])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "summary": self.summary,
            "steps_taken": self.steps_taken,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "run_id": self.run_id,
            "strategy": self.strategy.model_dump() if self.strategy else None,
        }


# =============================================================================
# Unified Agent
# =============================================================================

class UnifiedAgent:
    """
    The unified agent that handles all task execution.

    This is the single entry point that replaces the multi-mode system.
    It uses the intelligent orchestrator for strategy selection and
    coordinates all execution through a consistent interface.
    """

    def __init__(
        self,
        llm_client=None,
        on_status: Optional[Callable[[str], None]] = None,
        on_user_input: Optional[Callable[[str], str]] = None,
        approval_required: bool = True,
    ):
        """
        Initialize the unified agent.

        Args:
            llm_client: LLM client to use. If None, will get from adapters.
            on_status: Callback for status updates
            on_user_input: Callback to get user input
            approval_required: Whether to require approval for risky operations
        """
        self._llm = llm_client
        self._orchestrator = IntelligentOrchestrator(llm_client)
        self._executor = None  # Lazy init
        self._memory = None    # Lazy init

        # Callbacks
        self.on_status = on_status
        self.on_user_input = on_user_input
        self.approval_required = approval_required

        # State
        self._initialized = False

    def _status(self, message: str) -> None:
        """Report status update."""
        logger.info(message)
        if self.on_status:
            self.on_status(message)

    def _ask_user(self, question: str) -> Optional[str]:
        """Ask user for input."""
        if self.on_user_input:
            return self.on_user_input(question)
        return None

    def _get_llm(self):
        """Get or create LLM client."""
        if self._llm is None:
            from agent.adapters import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    def _get_executor(self):
        """Get or create the hybrid executor."""
        if self._executor is None:
            try:
                from agent.autonomous.hybrid_executor import get_hybrid_executor
                self._executor = get_hybrid_executor(self._get_llm())
                self._executor.initialize()
            except Exception as e:
                logger.warning(f"Could not initialize hybrid executor: {e}")
                # Fall back to basic executor
                self._executor = None
        return self._executor

    def _get_memory(self):
        """Get or create memory store."""
        if self._memory is None:
            try:
                from agent.memory.memory_manager import MemoryManager
                self._memory = MemoryManager()
            except Exception as e:
                logger.debug(f"Could not initialize memory: {e}")
        return self._memory

    def run(
        self,
        request: str,
        context: Optional[str] = None,
    ) -> AgentResult:
        """
        Execute a user request.

        This is the main entry point. It:
        1. Analyzes the request with the orchestrator
        2. Gets clarification if needed
        3. Gets approval for risky operations
        4. Executes using the appropriate strategy
        5. Stores results and lessons in memory

        Args:
            request: The user's request
            context: Optional additional context

        Returns:
            AgentResult with the outcome
        """
        start_time = time.time()
        run_id = uuid4().hex[:12]

        self._status(f"[{run_id}] Processing: {request[:100]}...")

        try:
            # =================================================================
            # Step 1: Analyze with Orchestrator
            # =================================================================
            self._status("Analyzing request...")
            strategy = self._orchestrator.analyze(request, context)

            self._status(f"  Strategy: {strategy.intent} (confidence: {strategy.confidence:.0%})")
            self._status(f"  Skill: {strategy.preferred_skill or 'auto'}")
            self._status(f"  Risk: {strategy.risk_level.value}")

            # =================================================================
            # Step 2: Handle Clarification
            # =================================================================
            if self._orchestrator.requires_clarification(strategy):
                if strategy.clarification_questions:
                    self._status("Need clarification...")
                    for question in strategy.clarification_questions:
                        answer = self._ask_user(question)
                        if answer:
                            # Re-analyze with additional context
                            context = f"{context or ''}\nUser clarified: {answer}"
                            strategy = self._orchestrator.analyze(request, context)
                elif strategy.confidence < 0.6:
                    # Low confidence - ask for confirmation
                    confirm = self._ask_user(
                        f"I'm going to try: {strategy.reasoning}\n"
                        f"Is this what you want? (yes/no)"
                    )
                    if confirm and confirm.lower() not in ("yes", "y"):
                        return AgentResult(
                            success=False,
                            summary="User declined to proceed",
                            strategy=strategy,
                            duration_seconds=time.time() - start_time,
                            run_id=run_id,
                        )

            # =================================================================
            # Step 3: Handle Approval for Risky Operations
            # =================================================================
            if self.approval_required and self._orchestrator.requires_approval(strategy):
                self._status(f"This operation is {strategy.risk_level.value} risk")
                approval = self._ask_user(
                    f"This operation may {self._risk_description(strategy.risk_level)}.\n"
                    f"Do you want to proceed? (yes/no)"
                )
                if not approval or approval.lower() not in ("yes", "y"):
                    return AgentResult(
                        success=False,
                        summary="User did not approve operation",
                        strategy=strategy,
                        duration_seconds=time.time() - start_time,
                        run_id=run_id,
                    )

            # =================================================================
            # Step 4: Execute Based on Strategy
            # =================================================================
            result = self._execute_strategy(request, strategy, context)

            # =================================================================
            # Step 5: Store Results and Lessons
            # =================================================================
            self._store_results(request, strategy, result)

            return result

        except Exception as e:
            logger.exception(f"Agent execution failed: {e}")
            return AgentResult(
                success=False,
                summary=f"Execution failed: {str(e)}",
                error=str(e),
                duration_seconds=time.time() - start_time,
                run_id=run_id,
            )

    def _risk_description(self, risk_level: RiskLevel) -> str:
        """Get human-readable risk description."""
        descriptions = {
            RiskLevel.NONE: "have no side effects",
            RiskLevel.LOW: "make minor changes that can be undone",
            RiskLevel.MEDIUM: "make significant changes to your system",
            RiskLevel.HIGH: "make destructive or irreversible changes",
        }
        return descriptions.get(risk_level, "have unknown effects")

    def _execute_strategy(
        self,
        request: str,
        strategy: Strategy,
        context: Optional[str],
    ) -> AgentResult:
        """
        Execute based on the selected strategy.

        Routes to appropriate execution method based on the strategy.
        """
        start_time = time.time()

        # Simple, no-tool requests
        if not strategy.needs_tools:
            return self._handle_simple_request(request, strategy)

        # Calendar skill
        if strategy.preferred_skill == "calendar":
            return self._execute_calendar(request, strategy)

        # Desktop UI automation
        if strategy.needs_ui_automation or strategy.preferred_skill == "desktop":
            return self._execute_ui_automation(request, strategy, context)

        # Web browsing
        if strategy.needs_web or strategy.preferred_skill == "browser":
            return self._execute_web(request, strategy, context)

        # Default: Use hybrid executor for general tasks
        return self._execute_hybrid(request, strategy, context)

    def _handle_simple_request(
        self,
        request: str,
        strategy: Strategy,
    ) -> AgentResult:
        """Handle requests that don't need tools (help, info, etc.)."""
        llm = self._get_llm()

        try:
            response = llm.chat(
                request,
                system_prompt="You are a helpful assistant. Answer the user's question directly.",
                timeout=30,
            )

            return AgentResult(
                success=True,
                summary=response.content,
                strategy=strategy,
                steps_taken=1,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                summary=f"Failed to respond: {e}",
                error=str(e),
                strategy=strategy,
            )

    def _execute_calendar(
        self,
        request: str,
        strategy: Strategy,
    ) -> AgentResult:
        """Execute calendar-related requests."""
        self._status("Checking calendar...")

        try:
            # Try to use calendar skill
            from agent.tools.calendar import get_calendar_events, CalendarEventsArgs
            from datetime import date, timedelta

            # Determine time range from entities
            time_range = strategy.entities.get("time_range", "today")

            if time_range == "today":
                start = date.today()
                end = start + timedelta(days=1)
            elif time_range == "tomorrow":
                start = date.today() + timedelta(days=1)
                end = start + timedelta(days=1)
            elif time_range == "this_week":
                start = date.today()
                end = start + timedelta(days=7)
            else:
                start = date.today()
                end = start + timedelta(days=7)

            args = CalendarEventsArgs(
                start_date=start.isoformat(),
                end_date=end.isoformat(),
            )

            result = get_calendar_events(None, args)

            if result.get("success"):
                events = result.get("events", [])
                if events:
                    def _format_event(evt):
                        start = evt.get("start", {})
                        when = start.get("dateTime") or start.get("date") or "unknown time"
                        return f"- {evt.get('summary', 'Untitled')} at {when}"

                    event_list = "\n".join(_format_event(e) for e in events[:10])
                    summary = f"Found {len(events)} events:\n{event_list}"
                else:
                    summary = f"No events found for {time_range}"

                return AgentResult(
                    success=True,
                    summary=summary,
                    strategy=strategy,
                    steps_taken=1,
                )
            else:
                error = result.get("error", "Unknown error")
                setup_guide = result.get("setup_guide")
                if setup_guide:
                    return AgentResult(
                        success=False,
                        summary=setup_guide,
                        error=error,
                        strategy=strategy,
                    )
                if "credentials" in error.lower() or "auth" in error.lower():
                    return AgentResult(
                        success=False,
                        summary="Calendar not authenticated. Please set up Google Calendar credentials.",
                        error=error,
                        strategy=strategy,
                    )
                return AgentResult(
                    success=False,
                    summary=f"Calendar error: {error}",
                    error=error,
                    strategy=strategy,
                )

        except ImportError:
            return AgentResult(
                success=False,
                summary="Calendar skill not available",
                error="Calendar module not found",
                strategy=strategy,
            )
        except Exception as e:
            logger.exception(f"Calendar execution failed: {e}")
            return AgentResult(
                success=False,
                summary=f"Calendar error: {e}",
                error=str(e),
                strategy=strategy,
            )

    def _execute_ui_automation(
        self,
        request: str,
        strategy: Strategy,
        context: Optional[str],
    ) -> AgentResult:
        """Execute UI automation tasks."""
        self._status("Running UI automation...")

        executor = self._get_executor()
        if not executor:
            return AgentResult(
                success=False,
                summary="UI automation not available",
                error="Could not initialize executor",
                strategy=strategy,
            )

        try:
            result = executor.run_task(
                objective=request,
                context=context or "",
                on_step=lambda s: self._status(f"  Step: {s.get('action', {}).get('reasoning', '')[:60]}"),
                on_user_input=self._ask_user,
            )

            return AgentResult(
                success=result.get("success", False),
                summary=result.get("summary", ""),
                steps_taken=result.get("steps_taken", 0),
                actions=result.get("actions", []),
                error=result.get("last_error"),
                strategy=strategy,
            )

        except Exception as e:
            logger.exception(f"UI automation failed: {e}")
            return AgentResult(
                success=False,
                summary=f"UI automation failed: {e}",
                error=str(e),
                strategy=strategy,
            )

    def _execute_web(
        self,
        request: str,
        strategy: Strategy,
        context: Optional[str],
    ) -> AgentResult:
        """Execute web browsing tasks."""
        self._status("Browsing web...")

        # For now, delegate to hybrid executor with web context
        executor = self._get_executor()
        if not executor:
            return AgentResult(
                success=False,
                summary="Web automation not available",
                error="Could not initialize executor",
                strategy=strategy,
            )

        try:
            result = executor.run_task(
                objective=f"Web task: {request}",
                context=f"{context or ''}\nThis is a web browsing task.",
                on_step=lambda s: self._status(f"  Step: {s.get('action', {}).get('reasoning', '')[:60]}"),
                on_user_input=self._ask_user,
            )

            return AgentResult(
                success=result.get("success", False),
                summary=result.get("summary", ""),
                steps_taken=result.get("steps_taken", 0),
                actions=result.get("actions", []),
                error=result.get("last_error"),
                strategy=strategy,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                summary=f"Web task failed: {e}",
                error=str(e),
                strategy=strategy,
            )

    def _execute_hybrid(
        self,
        request: str,
        strategy: Strategy,
        context: Optional[str],
    ) -> AgentResult:
        """Execute using the hybrid executor (general tasks)."""
        self._status("Executing task...")

        executor = self._get_executor()
        if not executor:
            # Fallback to simple LLM response
            return self._handle_simple_request(request, strategy)

        try:
            result = executor.run_task(
                objective=request,
                context=context or "",
                on_step=lambda s: self._status(f"  Step: {s.get('action', {}).get('reasoning', '')[:60]}"),
                on_user_input=self._ask_user,
            )

            return AgentResult(
                success=result.get("success", False),
                summary=result.get("summary", ""),
                steps_taken=result.get("steps_taken", 0),
                actions=result.get("actions", []),
                error=result.get("last_error"),
                strategy=strategy,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                summary=f"Task failed: {e}",
                error=str(e),
                strategy=strategy,
            )

    def _store_results(
        self,
        request: str,
        strategy: Strategy,
        result: AgentResult,
    ) -> None:
        """Store execution results and lessons in memory."""
        memory = self._get_memory()
        if not memory:
            return

        try:
            # Store as completed task
            memory.add_completed_task({
                "request": request,
                "intent": strategy.intent,
                "success": result.success,
                "summary": result.summary,
                "steps": result.steps_taken,
                "timestamp": datetime.now().isoformat(),
            })

            # If failed, store as lesson
            if not result.success and result.error:
                memory.add_fact(
                    f"Task '{strategy.intent}' failed: {result.error}",
                    category="lessons",
                )

        except Exception as e:
            logger.debug(f"Could not store results: {e}")


# =============================================================================
# Factory Function
# =============================================================================

def get_unified_agent(**kwargs) -> UnifiedAgent:
    """Get a unified agent instance."""
    return UnifiedAgent(**kwargs)
