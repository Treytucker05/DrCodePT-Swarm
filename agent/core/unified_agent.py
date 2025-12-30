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
import os
import re
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
                # Let the hybrid executor manage its own LLM selection
                self._executor = get_hybrid_executor()
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
            result = self._execute_strategy(request, strategy, context, run_id=run_id)
            result.run_id = run_id

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
        *,
        run_id: str,
    ) -> AgentResult:
        """
        Execute based on the selected strategy.

        Routes to appropriate execution method based on the strategy.
        """
        start_time = time.time()

        # Simple, no-tool requests
        if not strategy.needs_tools:
            return self._handle_simple_request(request, strategy)

        fast_result = self._try_fast_file_task(request)
        if fast_result is not None:
            return fast_result

        # Calendar skill
        if strategy.preferred_skill == "calendar":
            return self._execute_calendar(request, strategy)

        # Desktop UI automation
        if strategy.needs_ui_automation or strategy.preferred_skill == "desktop":
            return self._execute_ui_automation(request, strategy, context)

        # Tool-driven tasks (planning, research, filesystem, API, etc.)
        return self._execute_runner(request, strategy, context, run_id=run_id)

    def _try_fast_file_task(self, request: str) -> AgentResult | None:
        """Fast path for trivial file-write/read tasks to avoid long planning."""
        req = request or ""

        # Fast read path
        read_pattern = re.compile(
            r"\b(?:read|open|show)\b\s+(?:the\s+file\s+)?(?P<name>[^\s]+)(?:\s+(?:and|then)\s+(?:tell\s+me\s+)?(?:its\s+)?contents?)?",
            re.IGNORECASE,
        )
        read_match = read_pattern.search(req)
        if read_match:
            filename = read_match.group("name").strip().strip("\"'")
            if not filename or any(sep in filename for sep in ("/", "\\")) or ".." in filename:
                return None
            target = (Path.cwd() / filename).resolve()
            if target.exists():
                try:
                    content = target.read_text(encoding="utf-8")
                    return AgentResult(
                        success=True,
                        summary=f"Contents of {target}: {content!r}",
                        strategy=None,
                        steps_taken=1,
                    )
                except Exception as exc:
                    return AgentResult(
                        success=False,
                        summary=f"Read failed for {target}: {exc}",
                        error=str(exc),
                        steps_taken=1,
                    )
            content_hint = None
            hint_match = re.search(r"create it with (?:the )?text [\'\"](?P<content>.*?)[\'\"]", req, re.IGNORECASE)
            if hint_match:
                content_hint = hint_match.group("content")
            if content_hint:
                try:
                    target.write_text(content_hint, encoding="utf-8")
                    confirmed = target.read_text(encoding="utf-8")
                    return AgentResult(
                        success=True,
                        summary=f"Created {target} with content: {confirmed!r}",
                        strategy=None,
                        steps_taken=1,
                    )
                except Exception as exc:
                    return AgentResult(
                        success=False,
                        summary=f"Create/read failed for {target}: {exc}",
                        error=str(exc),
                        steps_taken=1,
                    )
            answer = self._ask_user(
                f"{filename} not found in {Path.cwd()}. Provide full path, or type 'create' to create it."
            )
            if not answer:
                return AgentResult(
                    success=False,
                    summary=f"File not found: {target}",
                    error="file_not_found",
                    steps_taken=1,
                )
            ans = answer.strip().strip("\"'")
            if ans.lower() in {"create", "yes", "y"}:
                content = self._ask_user("What content should I write into it? (leave blank for empty)") or ""
                try:
                    target.write_text(content, encoding="utf-8")
                    confirmed = target.read_text(encoding="utf-8")
                    return AgentResult(
                        success=True,
                        summary=f"Created {target} with content: {confirmed!r}",
                        strategy=None,
                        steps_taken=1,
                    )
                except Exception as exc:
                    return AgentResult(
                        success=False,
                        summary=f"Create/read failed for {target}: {exc}",
                        error=str(exc),
                        steps_taken=1,
                    )
            else:
                alt = Path(ans).expanduser()
                if not alt.is_absolute():
                    alt = (Path.cwd() / alt).resolve()
                if not alt.exists():
                    return AgentResult(
                        success=False,
                        summary=f"File not found: {alt}",
                        error="file_not_found",
                        steps_taken=1,
                    )
                try:
                    content = alt.read_text(encoding="utf-8")
                    return AgentResult(
                        success=True,
                        summary=f"Contents of {alt}: {content!r}",
                        strategy=None,
                        steps_taken=1,
                    )
                except Exception as exc:
                    return AgentResult(
                        success=False,
                        summary=f"Read failed for {alt}: {exc}",
                        error=str(exc),
                        steps_taken=1,
                    )

        # Fast write path
        pattern = re.compile(
            r"create (?:a )?file (?:named|called) (?P<name>[^\s]+) and put (?P<quote>['\"])(?P<content>.*?)(?P=quote) inside it",
            re.IGNORECASE,
        )
        match = pattern.search(req)
        if not match:
            return None
        filename = match.group("name").strip()
        if not filename or any(sep in filename for sep in ("/", "\\")) or ".." in filename:
            return None
        content = match.group("content")
        try:
            self._status(f"Fast path: writing {filename}...")
            target = (Path.cwd() / filename).resolve()
            target.write_text(content, encoding="utf-8")
            try:
                confirmed = target.read_text(encoding="utf-8")
            except Exception:
                confirmed = None
            open_after = os.getenv("TREYS_AGENT_OPEN_CREATED_FILE", "1").strip().lower() not in {"0", "false", "no", "off"}
            if re.search(r"\b(open|show)\b", req, re.IGNORECASE):
                open_after = True
            open_note = ""
            if open_after:
                try:
                    os.startfile(str(target))
                    open_note = " Opened the file."
                except Exception as exc:
                    open_note = f" Tried to open but failed: {exc}"
            if confirmed is not None and confirmed != content:
                summary = f"Created {target}. Verification failed: content mismatch.{open_note}"
            elif confirmed is None:
                summary = f"Created {target}. Verification unavailable.{open_note}"
            else:
                summary = f"Created {target} with content: {content!r}.{open_note}"
            return AgentResult(
                success=True,
                summary=summary,
                strategy=None,
                steps_taken=1,
            )
        except Exception as exc:
            return AgentResult(
                success=False,
                summary=f"Fast path write failed: {exc}",
                error=str(exc),
                steps_taken=1,
            )


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
            content = getattr(response, "content", response)

            return AgentResult(
                success=True,
                summary=str(content),
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
                if result.get("needs_auth") or "credentials" in error.lower() or "auth" in error.lower():
                    consent = self._ask_user(
                        "Google Calendar isn't configured. I can run OAuth setup now (opens a browser). Proceed? (yes/no)"
                    )
                    if consent and consent.strip().lower() in {"yes", "y"}:
                        try:
                            from agent.tools.google_setup import setup_google_apis, SetupGoogleArgs
                            calendar_scopes = [
                                "https://www.googleapis.com/auth/calendar",
                                "https://www.googleapis.com/auth/calendar.events",
                            ]
                            setup_result = setup_google_apis(None, SetupGoogleArgs(scopes=calendar_scopes))
                        except Exception as exc:
                            return AgentResult(
                                success=False,
                                summary=f"Calendar setup failed: {exc}",
                                error=str(exc),
                                strategy=strategy,
                            )
                        if getattr(setup_result, "success", False):
                            retry = get_calendar_events(None, args)
                            if retry.get("success"):
                                events = retry.get("events", [])
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
                            retry_error = retry.get("error", "Calendar setup completed, but fetching events failed")
                            return AgentResult(
                                success=False,
                                summary=retry_error,
                                error=retry_error,
                                strategy=strategy,
                            )
                        setup_error = getattr(setup_result, "error", None) or "OAuth setup failed"
                        return AgentResult(
                            success=False,
                            summary=setup_error,
                            error=setup_error,
                            strategy=strategy,
                        )
                    if setup_guide:
                        return AgentResult(
                            success=False,
                            summary=setup_guide,
                            error=error,
                            strategy=strategy,
                        )
                    return AgentResult(
                        success=False,
                        summary="Calendar requires OAuth setup before it can be used.",
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

    def _execute_runner(
        self,
        request: str,
        strategy: Strategy,
        context: Optional[str],
        *,
        run_id: str,
    ) -> AgentResult:
        """Execute tool-driven tasks using the autonomous runner."""
        self._status("Planning and executing task...")

        try:
            from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
            from agent.autonomous.runner import AgentRunner
            from agent.config.profile import resolve_profile
            from agent.llm.base import get_default_llm
        except Exception as exc:
            return AgentResult(
                success=False,
                summary=f"Runner unavailable: {exc}",
                error=str(exc),
                strategy=strategy,
            )

        repo_root = Path(__file__).resolve().parents[2]
        run_dir = repo_root / "runs" / "unified" / run_id

        # Allow configurable safety controls
        unsafe_mode = os.getenv("AGENT_UNSAFE_MODE", "").strip().lower() in {"1", "true", "yes", "y", "on"}
        allow_fs_anywhere = os.getenv("AGENT_ALLOW_FS_ANYWHERE", "").strip().lower() in {"1", "true", "yes", "y", "on"}

        profile = resolve_profile(None, env_keys=("AGENT_PROFILE", "AUTO_PROFILE"))
        agent_cfg = AgentConfig(
            unsafe_mode=unsafe_mode,
            enable_web_gui=True,
            enable_desktop=True,
            allow_human_ask=True,
            allow_fs_anywhere=allow_fs_anywhere or unsafe_mode,
            profile=profile,
        )
        planner_mode = "plan_first" if strategy.complexity.value == "complex" else "react"
        planner_cfg = PlannerConfig(mode=planner_mode, num_candidates=1, max_plan_steps=6)
        runner_cfg = RunnerConfig(
            max_steps=int(os.getenv("AGENT_MAX_STEPS", "30")),
            timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", "600")),
        )

        llm = get_default_llm()
        task_text = request
        if context:
            task_text = f"{request}\n\nContext:\n{context}"

        runner = AgentRunner(
            cfg=runner_cfg,
            agent_cfg=agent_cfg,
            planner_cfg=planner_cfg,
            llm=llm,
            run_dir=run_dir,
            mode_name="unified",
            agent_id=run_id,
        )
        result = runner.run(task_text)
        summary = self._summarize_trace(result.trace_path, request, llm)
        if not summary:
            summary = f"Run completed with stop_reason={result.stop_reason}"

        return AgentResult(
            success=bool(result.success),
            summary=summary,
            steps_taken=int(result.steps_executed),
            error=None if result.success else result.stop_reason,
            strategy=strategy,
            run_id=run_id,
        )

    def _summarize_trace(
        self,
        trace_path: Optional[str],
        request: str,
        llm,
    ) -> str:
        """Summarize a runner trace into a user-facing response."""
        if not trace_path:
            return ""
        path = Path(trace_path)
        if not path.exists():
            return ""
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return ""
        if not lines:
            return ""
        tail = "\n".join(lines[-200:])[:12000]
        prompt = (
            "Summarize the outcome of this autonomous task for the user. "
            "Be concise, concrete, and include any errors and next steps.\n\n"
            f"TASK:\n{request}\n\nTRACE_TAIL:\n{tail}\n"
        )
        try:
            if hasattr(llm, "generate_text"):
                return llm.generate_text(prompt, system="You are a concise summarizer.")
            if hasattr(llm, "chat"):
                try:
                    return llm.chat(prompt, timeout_seconds=60) or ""
                except TypeError:
                    return llm.chat(prompt) or ""
        except Exception:
            return ""
        return ""

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
