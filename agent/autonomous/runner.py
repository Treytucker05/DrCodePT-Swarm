from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from agent.llm.base import LLMClient
from agent.llm import schemas as llm_schemas

from .config import AgentConfig, PlannerConfig, RunContext, RunnerConfig
from .jsonio import dumps_compact
from .loop_detection import LoopDetector
from .memory.sqlite_store import SqliteMemoryStore
from .models import AgentRunResult, Observation, Plan, Reflection, Step, ToolResult
from .perception import Perceptor
from .planning.plan_first import PlanFirstPlanner
from .planning.react import ReActPlanner
from .reflection import Reflector
from .state import AgentState
from .tools.builtins import build_default_tool_registry
from .tools.registry import ToolRegistry
from .trace import JsonlTracer


def _utc_ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)


class TrackedLLM:
    def __init__(self, llm: LLMClient):
        self._llm = llm
        self.calls = 0
        self.estimated_tokens = 0.0
        self.estimated_cost_usd = 0.0
        self._tokens_per_char = float(os.getenv("LLM_TOKENS_PER_CHAR", "0.25"))
        cost_per_1k = os.getenv("LLM_COST_PER_1K_TOKENS_USD")
        self._cost_per_1k = float(cost_per_1k) if cost_per_1k else None
        self.default_timeout_seconds: Optional[int] = None

        self.provider = getattr(llm, "provider", "unknown")
        self.model = getattr(llm, "model", "unknown")

    @property
    def cost_per_1k(self) -> Optional[float]:
        return self._cost_per_1k

    def complete_json(self, prompt: str, *, schema_path: Path, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        if timeout_seconds is None and self.default_timeout_seconds is not None:
            timeout_seconds = self.default_timeout_seconds
        out = self._llm.complete_json(prompt, schema_path=schema_path, timeout_seconds=timeout_seconds)
        self.calls += 1
        out_str = json.dumps(out, ensure_ascii=False, sort_keys=True, default=str)
        chars = len(prompt) + len(out_str)
        tokens = chars * self._tokens_per_char
        self.estimated_tokens += tokens
        if self._cost_per_1k is not None:
            self.estimated_cost_usd += (tokens / 1000.0) * self._cost_per_1k
        return out

    def reason_json(self, prompt: str, *, schema_path: Path, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        if timeout_seconds is None and self.default_timeout_seconds is not None:
            timeout_seconds = self.default_timeout_seconds
        # Prefer a dedicated reasoning method if available.
        if hasattr(self._llm, "reason_json"):
            out = self._llm.reason_json(prompt, schema_path=schema_path, timeout_seconds=timeout_seconds)  # type: ignore[attr-defined]
        elif hasattr(self._llm, "complete_reasoning"):
            out = self._llm.complete_reasoning(prompt, schema_path=schema_path, timeout_seconds=timeout_seconds)  # type: ignore[attr-defined]
        else:
            out = self._llm.complete_json(prompt, schema_path=schema_path, timeout_seconds=timeout_seconds)
        self.calls += 1
        out_str = json.dumps(out, ensure_ascii=False, sort_keys=True, default=str)
        chars = len(prompt) + len(out_str)
        tokens = chars * self._tokens_per_char
        self.estimated_tokens += tokens
        if self._cost_per_1k is not None:
            self.estimated_cost_usd += (tokens / 1000.0) * self._cost_per_1k
        return out


@dataclass
class AgentRunner:
    cfg: RunnerConfig
    agent_cfg: AgentConfig
    planner_cfg: PlannerConfig
    llm: LLMClient
    tools: Optional[ToolRegistry] = None
    run_dir: Optional[Path] = None
    memory_store: Optional[SqliteMemoryStore] = None
    mode_name: str = "autonomous"
    agent_id: Optional[str] = None

    def run(self, task: str, *, resume_path: Optional[Path] = None) -> AgentRunResult:
        resume = self._load_checkpoint(resume_path) if resume_path else None
        if resume:
            run_id = resume.get("run_id") or f"{_utc_ts_id()}_{uuid4().hex[:8]}"
        else:
            run_id = f"{_utc_ts_id()}_{uuid4().hex[:8]}"
        repo_root = Path(__file__).resolve().parents[2]
        run_dir = self.run_dir or (repo_root / "runs" / "autonomous" / run_id)
        if resume and resume.get("run_dir"):
            try:
                run_dir = Path(resume.get("run_dir")).resolve()
            except Exception:
                pass
        run_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir = run_dir / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        ctx = RunContext(run_id=run_id, run_dir=run_dir, workspace_dir=workspace_dir)

        # trace.jsonl/result.json are the authoritative execution artifacts; stdout is for humans.
        tracer = JsonlTracer(run_dir / "trace.jsonl")
        perceptor = Perceptor()
        llm = self.llm
        try:
            from agent.llm.codex_cli_client import CodexCliClient

            if isinstance(llm, CodexCliClient):
                llm = llm.with_context(workdir=repo_root, log_dir=run_dir)
        except Exception:
            pass
        tracked_llm = TrackedLLM(llm)
        reflector = Reflector(llm=tracked_llm, pre_mortem_enabled=self.agent_cfg.pre_mortem_enabled)

        memory_store = self.memory_store or self._open_default_memory_store()
        tools = self.tools or build_default_tool_registry(self.agent_cfg, run_dir, memory_store=memory_store)
        tool_summary = ""
        if self.cfg.llm_heartbeat_seconds:
            tool_summary = self._describe_tools_for_humans(tools)
            print(f"[TOOLS] I can use: {tool_summary}.")
        heartbeat_label = self.cfg.llm_heartbeat_seconds
        plan_timeout = self.cfg.llm_plan_timeout_seconds
        retry_timeout = self.cfg.llm_plan_retry_timeout_seconds
        heartbeat_text = f"{heartbeat_label}s" if heartbeat_label else "off"
        print(
            f"[CONFIG] plan_timeout={plan_timeout}s plan_retry_timeout={retry_timeout}s heartbeat={heartbeat_text}"
        )
        self._stats = {"tool_calls": 0, "retries": 0}
        started_at = datetime.now(timezone.utc).isoformat()
        start = time.monotonic()

        state = AgentState(task=task)
        steps_executed = 0
        consecutive_no_progress = 0
        last_plan_hash: Optional[str] = None
        exploration_nudge_next = False
        exploration_reason = ""
        loop_nudge_used = False

        if self.cfg.cost_budget_usd is not None and tracked_llm.cost_per_1k is None:
            tracer.log(
                {
                    "type": "stop",
                    "reason": "cost_budget_requires_LLM_COST_PER_1K_TOKENS_USD",
                    "budget_usd": self.cfg.cost_budget_usd,
                }
            )
            return self._stop(
                tracer=tracer,
                memory_store=memory_store,
                success=False,
                reason="cost_budget_requires_LLM_COST_PER_1K_TOKENS_USD",
                steps=0,
                run_id=run_id,
                llm_stats=tracked_llm,
                task=task,
                state=state,
                run_dir=run_dir,
                started_at=started_at,
                started_monotonic=start,
            )

        planner = self._make_planner(tracked_llm, tools)

        if resume:
            try:
                state = AgentState.from_dict(resume.get("state") or {"task": task})
                if state.task:
                    task = state.task
                steps_executed = int(resume.get("steps_executed") or 0)
                consecutive_no_progress = int(resume.get("consecutive_no_progress") or 0)
                last_plan_hash = resume.get("last_plan_hash")
                exploration_nudge_next = bool(resume.get("exploration_nudge_next") or False)
                exploration_reason = str(resume.get("exploration_reason") or "")
                planner_mode = resume.get("planner_mode")
                if planner_mode in {"react", "plan_first"}:
                    self.planner_cfg = PlannerConfig(
                        mode=planner_mode,  # type: ignore[arg-type]
                        num_candidates=self.planner_cfg.num_candidates,
                        max_plan_steps=self.planner_cfg.max_plan_steps,
                        use_dppm=self.planner_cfg.use_dppm,
                        use_tot=self.planner_cfg.use_tot,
                    )
            except Exception:
                pass

        loop_detector = LoopDetector(window=self.cfg.loop_window, repeat_threshold=self.cfg.loop_repeat_threshold)

        if not state.observations:
            obs0 = perceptor.text_to_observation("task", task)
            state.add_observation(obs0)
            tracer.log({"type": "observation", "observation": self._dump(obs0)})

        last_state_fingerprint = state.state_fingerprint()
        same_state_steps = 0

        current_plan: Optional[Plan] = state.current_plan
        step_snapshots_taken: set[str] = set()

        self._save_checkpoint(
            run_dir,
            state=state,
            task=task,
            run_id=run_id,
            steps_executed=steps_executed,
            consecutive_no_progress=consecutive_no_progress,
            last_plan_hash=last_plan_hash,
            exploration_nudge_next=exploration_nudge_next,
            exploration_reason=exploration_reason,
        )

        try:
            while True:
                if self._kill_switch_triggered():
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="kill_switch",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )
                if steps_executed >= self.cfg.max_steps:
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="max_steps",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )
                if (time.monotonic() - start) >= self.cfg.timeout_seconds:      
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="timeout",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )
                if self.cfg.cost_budget_usd is not None and tracked_llm.estimated_cost_usd > self.cfg.cost_budget_usd:
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="budget_exceeded",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )

                self._maybe_compact_state(state, tracked_llm, tracer)

                extra_queries: List[str] = []
                if state.rolling_summary:
                    extra_queries.append(state.rolling_summary[:400])
                memories = self._retrieve_memories(memory_store, task, extra_queries=extra_queries)

                if self.planner_cfg.mode == "react":
                    nudge_task = task
                    if exploration_nudge_next:
                        nudge_task = (
                            task
                            + " Exploration nudge: take one lightweight exploration step "
                            + "(web: scroll/search/expand menus; desktop: scroll/alt-tab/resnapshot)."
                        )
                    plan_label = f"Planning next step ({self.planner_cfg.mode})"
                    if tool_summary:
                        plan_label = f"{plan_label} using {tool_summary}"

                    def _plan_call(compact: bool):
                        obs = state.observations if not compact else state.observations[-3:]
                        mem = memories if not compact else memories[:3]
                        timeout = self.cfg.llm_plan_timeout_seconds if not compact else self.cfg.llm_plan_retry_timeout_seconds
                        return self._with_llm_timeout(
                            tracked_llm,
                            timeout,
                            lambda: planner.plan(task=nudge_task, observations=obs, memories=mem),
                        )

                    plan = self._call_llm_with_retry(
                        tracer=tracer,
                        where="plan",
                        fn=lambda: _plan_call(False),
                        label=plan_label,
                        max_retries=0,
                        timeout_seconds=self.cfg.llm_plan_timeout_seconds,
                    )
                    if plan is None:
                        print("[THINKING] Planning is taking too long; trying a simpler, faster plan.")
                        plan = self._call_llm_with_retry(
                            tracer=tracer,
                            where="plan_fast",
                            fn=lambda: _plan_call(True),
                            label=f"{plan_label} (fast retry)",
                            max_retries=0,
                            timeout_seconds=self.cfg.llm_plan_retry_timeout_seconds,
                        )
                    if exploration_nudge_next and plan is not None:
                        tracer.log(
                            {
                                "type": "exploration_nudge",
                                "reason": exploration_reason or "stuck",
                                "planner_response": self._dump(plan),
                            }
                        )
                        exploration_nudge_next = False
                        exploration_reason = ""
                    if plan is None:
                        print("[THINKING] Still no plan. This may be a tool/setup issue or a flawed approach. Stopping to avoid a hang.")
                        return self._stop(
                            tracer=tracer,
                            memory_store=memory_store,
                            success=False,
                            reason="llm_plan_timeout",
                            steps=steps_executed,
                            run_id=run_id,
                            llm_stats=tracked_llm,
                            task=task,
                            state=state,
                            run_dir=run_dir,
                            started_at=started_at,
                            started_monotonic=start,
                        )
                    current_plan = plan
                    state.current_plan = current_plan
                    state.current_step_idx = 0
                else:
                    if current_plan is None or state.current_step_idx >= len(current_plan.steps):
                        plan_label = f"Planning next step ({self.planner_cfg.mode})"
                        if tool_summary:
                            plan_label = f"{plan_label} using {tool_summary}"

                        def _plan_call(compact: bool):
                            obs = state.observations if not compact else state.observations[-3:]
                            mem = memories if not compact else memories[:3]
                            timeout = self.cfg.llm_plan_timeout_seconds if not compact else self.cfg.llm_plan_retry_timeout_seconds
                            return self._with_llm_timeout(
                                tracked_llm,
                                timeout,
                                lambda: planner.plan(task=task, observations=obs, memories=mem),
                            )

                        current_plan = self._call_llm_with_retry(
                            tracer=tracer,
                            where="plan",
                            fn=lambda: _plan_call(False),
                            label=plan_label,
                            max_retries=0,
                            timeout_seconds=self.cfg.llm_plan_timeout_seconds,
                        )
                        if current_plan is None:
                            print("[THINKING] Planning is taking too long; trying a simpler, faster plan.")
                            current_plan = self._call_llm_with_retry(
                                tracer=tracer,
                                where="plan_fast",
                                fn=lambda: _plan_call(True),
                                label=f"{plan_label} (fast retry)",
                                max_retries=0,
                                timeout_seconds=self.cfg.llm_plan_retry_timeout_seconds,
                            )
                        if current_plan is None:
                            print("[THINKING] Still no plan. This may be a tool/setup issue or a flawed approach. Stopping to avoid a hang.")
                            return self._stop(
                                tracer=tracer,
                                memory_store=memory_store,
                                success=False,
                                reason="llm_plan_timeout",
                                steps=steps_executed,
                                run_id=run_id,
                                llm_stats=tracked_llm,
                                task=task,
                                state=state,
                                run_dir=run_dir,
                                started_at=started_at,
                                started_monotonic=start,
                            )
                        state.current_plan = current_plan
                        state.current_step_idx = 0
                    plan = current_plan

                plan_hash = json.dumps(self._dump(plan), sort_keys=True, default=str)
                if last_plan_hash == plan_hash:
                    pass
                last_plan_hash = plan_hash

                if not plan.steps:
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="planner_returned_no_steps",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )

                step = plan.steps[0] if self.planner_cfg.mode == "react" else plan.steps[state.current_step_idx]
                if self.cfg.llm_heartbeat_seconds:
                    print(f"[PLAN] Next tool: {step.tool_name} - {step.goal}")

                preempted_tool_result: Optional[ToolResult] = None
                # Approval gate for tools that require explicit confirmation
                if tools.requires_approval(step.tool_name):
                    approval_event = {"step_id": step.id, "tool_name": step.tool_name}
                    approval_error = None
                    answer = ""
                    if tools.has_tool("human_ask"):
                        prompt = f"Approve tool '{step.tool_name}' for step '{step.goal}'? (y/n)"
                        resp = tools.call("human_ask", {"question": prompt}, ctx)
                        if not resp.success:
                            approval_error = resp.error or "approval_failed"
                        if isinstance(resp.output, dict):
                            answer = (resp.output.get("answer") or "").strip().lower()
                        if answer not in {"y", "yes"} and approval_error is None:
                            approval_error = "approval_denied"
                        tracer.log(
                            {
                                "type": "approval",
                                "status": "approved" if approval_error is None else "denied",
                                "answer": answer,
                                "error": approval_error,
                                **approval_event,
                            }
                        )
                    else:
                        approval_error = "no_human_ask"
                        tracer.log({"type": "approval", "status": "no_human_ask", **approval_event})
                    if approval_error is not None:
                        preempted_tool_result = ToolResult(
                            success=False,
                            error=approval_error,
                            metadata={
                                "approval_required": True,
                                "approval_answer": answer,
                                "approval_error": approval_error,
                                "suggested_reflection": "replan",
                            },
                        )
                        tracer.log(
                            {
                                "type": "error_report",
                                "step_id": step.id,
                                "status": "blocked" if approval_error in {"approval_denied", "no_human_ask"} else "failed",
                                "reason": "approval_required",
                                "data": {"tool_name": step.tool_name, "answer": answer, "error": approval_error},
                            }
                        )

                if preempted_tool_result is None and self.agent_cfg.pre_mortem_enabled:
                    prem = self._call_llm_with_retry(
                        tracer=tracer,
                        where="premortem",
                        fn=lambda: reflector.pre_mortem(task=task, step=step, observation=state.observations[-1]),
                        allow_none=True,
                    )
                    tracer.log({"type": "premortem", "step_id": step.id, "data": prem})

                if preempted_tool_result is None:
                    # Preconditions check (if provided)
                    pre_ok, pre_report = self._check_conditions(
                        llm=tracked_llm,
                        kind="preconditions",
                        conditions=step.preconditions,
                        step=step,
                        observation=state.observations[-1],
                    )
                    if not pre_ok:
                        recovered_obs = self._attempt_recovery(tools=tools, ctx=ctx, step=step, tracer=tracer)
                        if recovered_obs is not None:
                            state.add_observation(recovered_obs)
                            pre_ok, pre_report = self._check_conditions(
                                llm=tracked_llm,
                                kind="preconditions",
                                conditions=step.preconditions,
                                step=step,
                                observation=recovered_obs,
                            )

                    if not pre_ok:
                        severity = "minor_repair"
                        if isinstance(pre_report, dict):
                            failed = pre_report.get("failed") or []
                            if isinstance(failed, list) and len(failed) > 2:
                                severity = "replan"
                        tool_result = ToolResult(
                            success=False,
                            output=pre_report,
                            error="preconditions_failed",
                            metadata={
                                "preconditions_failed": True,
                                "condition_report": pre_report,
                                "suggested_reflection": severity,
                            },
                        )
                        tracer.log(
                            {
                                "type": "condition_check",
                                "step_id": step.id,
                                "kind": "preconditions",
                                "report": pre_report,
                            }
                        )
                        tracer.log(
                            {
                                "type": "error_report",
                                "step_id": step.id,
                                "status": "failed",
                                "reason": "preconditions_failed",
                                "data": pre_report,
                            }
                        )
                    else:
                        tool_result = self._call_tool_with_retry(tools, ctx, step.tool_name, step.tool_args, tracer)

                        # Postconditions check (if provided)
                        post_ok, post_report = self._check_conditions(
                            llm=tracked_llm,
                            kind="postconditions",
                            conditions=step.postconditions,
                            step=step,
                            observation=perceptor.tool_result_to_observation(step.tool_name, tool_result),
                        )
                        if not post_ok:
                            recovered_obs = self._attempt_recovery(tools=tools, ctx=ctx, step=step, tracer=tracer)
                            if recovered_obs is not None:
                                state.add_observation(recovered_obs)
                                post_ok, post_report = self._check_conditions(
                                    llm=tracked_llm,
                                    kind="postconditions",
                                    conditions=step.postconditions,
                                    step=step,
                                    observation=recovered_obs,
                                )
                        if not post_ok:
                            severity = "minor_repair"
                            if isinstance(post_report, dict):
                                failed = post_report.get("failed") or []
                                if isinstance(failed, list) and len(failed) > 2:
                                    severity = "replan"
                            tool_result = ToolResult(
                                success=False,
                                output=tool_result.output,
                                error="postconditions_failed",
                                metadata={
                                    "postconditions_failed": True,
                                    "condition_report": post_report,
                                    "suggested_reflection": severity,
                                },
                            )
                            tracer.log(
                                {
                                    "type": "condition_check",
                                    "step_id": step.id,
                                    "kind": "postconditions",
                                    "report": post_report,
                                }
                            )
                            tracer.log(
                                {
                                    "type": "error_report",
                                    "step_id": step.id,
                                    "status": "failed",
                                    "reason": "postconditions_failed",
                                    "data": post_report,
                                }
                            )
                else:
                    tool_result = preempted_tool_result

                # Capture UI snapshot for web/desktop steps or on failure (once per step).
                snapshot = self._maybe_capture_ui_snapshot(
                    tools=tools,
                    ctx=ctx,
                    step=step,
                    tool_result=tool_result,
                    tracer=tracer,
                    step_snapshots_taken=step_snapshots_taken,
                )
                if snapshot is not None:
                    # Store only a lightweight reference to avoid circular nesting
                    tool_result.metadata["ui_snapshot"] = {
                        "step_id": snapshot.get("step_id"),
                        "tool_category": snapshot.get("tool_category"),
                        "has_screenshot": bool(snapshot.get("ui_snapshot", {}).get("screenshot")),
                    }

                obs = perceptor.tool_result_to_observation(step.tool_name, tool_result)
                state.add_observation(obs)
                self._save_checkpoint(
                    run_dir,
                    state=state,
                    task=task,
                    run_id=run_id,
                    steps_executed=steps_executed,
                    consecutive_no_progress=consecutive_no_progress,
                    last_plan_hash=last_plan_hash,
                    exploration_nudge_next=exploration_nudge_next,
                    exploration_reason=exploration_reason,
                )

                if tool_result.metadata.get("approval_required") and "suggested_reflection" not in tool_result.metadata:
                    tool_result.metadata["suggested_reflection"] = "replan"

                if tool_result.metadata.get("unsafe_blocked") is True:
                    tracer.log(
                        {
                            "type": "step",
                            "step_index": steps_executed,
                            "plan": self._dump(plan),
                            "action": {"tool_name": step.tool_name, "tool_args": step.tool_args},
                            "result": self._dump(tool_result),
                            "observation": self._dump(obs),
                            "reflection": {
                                "status": "replan",
                                "explanation_short": "approval_required" if tool_result.metadata.get("approval_required") else "unsafe_blocked",
                                "next_hint": tool_result.error or "",
                            },
                        }
                    )
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="unsafe_action_blocked",
                        steps=steps_executed + 1,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )

                reflection = self._call_llm_with_retry(
                    tracer=tracer,
                    where="reflection",
                    fn=lambda: reflector.reflect(task=task, step=step, tool_result=tool_result, observation=obs),
                )
                if reflection is None:
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="llm_error",
                        steps=steps_executed + 1,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )

                if tool_result.metadata.get("suggested_reflection") in {"minor_repair", "replan"}:
                    reflection.status = tool_result.metadata["suggested_reflection"]

                tracer.log(
                    {
                        "type": "step",
                        "step_index": steps_executed,
                        "plan": self._dump(plan),
                        "action": {"tool_name": step.tool_name, "tool_args": step.tool_args, "step": self._dump(step)},
                        "result": self._dump(tool_result),
                        "observation": self._dump(obs),
                        "reflection": self._dump(reflection),
                        "llm": {
                            "provider": tracked_llm.provider,
                            "model": tracked_llm.model,
                            "calls": tracked_llm.calls,
                            "estimated_cost_usd": tracked_llm.estimated_cost_usd,
                            "estimated_tokens": tracked_llm.estimated_tokens,
                        },
                    }
                )

                steps_executed += 1
                self._save_checkpoint(
                    run_dir,
                    state=state,
                    task=task,
                    run_id=run_id,
                    steps_executed=steps_executed,
                    consecutive_no_progress=consecutive_no_progress,
                    last_plan_hash=last_plan_hash,
                    exploration_nudge_next=exploration_nudge_next,
                    exploration_reason=exploration_reason,
                )

                # Stuck detection: no state change across steps
                current_fp = state.state_fingerprint()
                if current_fp == last_state_fingerprint:
                    same_state_steps += 1
                else:
                    same_state_steps = 0
                    last_state_fingerprint = current_fp
                if same_state_steps == max(1, self.cfg.no_state_change_threshold - 1):
                    if self.planner_cfg.mode == "react":
                        exploration_nudge_next = True
                        exploration_reason = "no_state_change"
                if same_state_steps >= self.cfg.no_state_change_threshold:
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="no_state_change",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )

                self._memory_updates(memory_store, task, step, tool_result, obs, reflection, run_id, tracer)

                action_signature = f"{step.tool_name}:{_json_dumps(step.tool_args)}"
                if loop_detector.update(action_signature, state.state_fingerprint()):
                    if self.planner_cfg.mode == "react" and not loop_nudge_used:
                        exploration_nudge_next = True
                        exploration_reason = "loop_detected"
                        loop_nudge_used = True
                    else:
                        return self._stop(
                            tracer=tracer,
                            memory_store=memory_store,
                            success=False,
                            reason="loop_detected",
                            steps=steps_executed,
                            run_id=run_id,
                            llm_stats=tracked_llm,
                            task=task,
                            state=state,
                            run_dir=run_dir,
                            started_at=started_at,
                            started_monotonic=start,
                        )

                if step.tool_name == "finish" and tool_result.success:
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=True,
                        reason="goal_achieved",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        plan=plan,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )

                if reflection.status == "success":
                    consecutive_no_progress = 0
                    if self.planner_cfg.mode == "plan_first":
                        state.current_step_idx += 1
                    continue

                # Use fallback plan if available (ToT-lite)
                if hasattr(planner, "consume_fallback"):
                    try:
                        fallback = planner.consume_fallback()  # type: ignore[attr-defined]
                    except Exception:
                        fallback = None
                    if fallback is not None:
                        current_plan = fallback
                        state.current_plan = fallback
                        state.current_step_idx = 0
                        continue

                consecutive_no_progress += 1
                if consecutive_no_progress >= 6:
                    return self._stop(
                        tracer=tracer,
                        memory_store=memory_store,
                        success=False,
                        reason="no_progress",
                        steps=steps_executed,
                        run_id=run_id,
                        llm_stats=tracked_llm,
                        task=task,
                        state=state,
                        run_dir=run_dir,
                        started_at=started_at,
                        started_monotonic=start,
                    )

                if reflection.status == "minor_repair":
                    repaired = self._call_llm_with_retry(
                        tracer=tracer,
                        where="repair",
                        fn=lambda: planner.repair(
                            task=task,
                            observations=state.observations,
                            memories=memories,
                            failed_step=step,
                            tool_result=tool_result,
                            reflection=reflection,
                        ),
                        allow_none=True,
                    )
                    if repaired is not None:
                        current_plan = repaired
                        state.current_plan = repaired
                        state.current_step_idx = 0
                    else:
                        current_plan = None
                        state.current_plan = None
                        state.current_step_idx = 0
                else:
                    current_plan = None
                    state.current_plan = None
                    state.current_step_idx = 0

        finally:
            try:
                if self.memory_store is None and memory_store is not None:
                    memory_store.close()
            except Exception:
                pass

    def _make_planner(self, llm: LLMClient, tools: ToolRegistry) -> Any:
        if self.planner_cfg.mode == "plan_first":
            return PlanFirstPlanner(
                llm=llm,
                tools=tools,
                unsafe_mode=self.agent_cfg.unsafe_mode,
                num_candidates=self.planner_cfg.num_candidates,
                max_steps=self.planner_cfg.max_plan_steps,
                use_dppm=self.planner_cfg.use_dppm,
                use_tot=self.planner_cfg.use_tot,
            )
        return ReActPlanner(llm=llm, tools=tools, unsafe_mode=self.agent_cfg.unsafe_mode)

    def _open_default_memory_store(self) -> Optional[SqliteMemoryStore]:
        path = self.agent_cfg.memory_db_path
        if path is None:
            agent_root = Path(__file__).resolve().parents[1]
            path = agent_root / "memory" / "autonomous_memory.sqlite3"
        try:
            return SqliteMemoryStore(path)
        except Exception:
            return None

    def _kill_switch_triggered(self) -> bool:
        if os.getenv("AGENT_KILL_SWITCH", "").strip().lower() in {"1", "true", "yes", "y"}:
            return True
        kill_path = os.getenv("AGENT_KILL_FILE")
        if kill_path:
            try:
                return Path(kill_path).exists()
            except Exception:
                return False
        # Default kill switch file at repo root
        try:
            repo_root = Path(__file__).resolve().parents[2]
            return (repo_root / "kill.switch").exists()
        except Exception:
            return False

    def _retrieve_memories(
        self,
        store: Optional[SqliteMemoryStore],
        task: str,
        *,
        extra_queries: Optional[List[str]] = None,
    ) -> List[dict]:
        if store is None:
            return []
        try:
            queries = [task]
            if extra_queries:
                queries.extend([q for q in extra_queries if q])
            seen: set[int] = set()
            out: List[dict] = []
            for q in queries:
                results = store.search(q, limit=6)
                for r in results:
                    if r.id in seen:
                        continue
                    seen.add(r.id)
                    out.append(
                        {
                            "kind": r.kind,
                            "key": r.key,
                            "content": r.content[:2000],
                            "metadata": r.metadata,
                            "updated_at": r.updated_at,
                        }
                    )
                    if len(out) >= 12:
                        break
                if len(out) >= 12:
                    break
            return out
        except Exception:
            return []

    @staticmethod
    def _checkpoint_path(run_dir: Path) -> Path:
        return run_dir / "checkpoint.json"

    def _save_checkpoint(
        self,
        run_dir: Path,
        *,
        state: AgentState,
        task: str,
        run_id: str,
        steps_executed: int,
        consecutive_no_progress: int,
        last_plan_hash: Optional[str],
        exploration_nudge_next: bool,
        exploration_reason: str,
    ) -> None:
        payload = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "task": task,
            "state": state.to_dict(),
            "steps_executed": steps_executed,
            "consecutive_no_progress": consecutive_no_progress,
            "last_plan_hash": last_plan_hash,
            "exploration_nudge_next": exploration_nudge_next,
            "exploration_reason": exploration_reason,
            "planner_mode": self.planner_cfg.mode,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            path = self._checkpoint_path(run_dir)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _load_checkpoint(path: Optional[Path]) -> Optional[Dict[str, Any]]:
        if path is None:
            return None
        try:
            if path.is_dir():
                path = path / "checkpoint.json"
            if not path.is_file():
                return None
            raw = path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(raw)
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def _maybe_compact_state(self, state: AgentState, llm: LLMClient, tracer: JsonlTracer) -> None:
        # LLM-backed memory compaction (structured output); fallback to heuristic compaction on failure.
        max_total = 40
        keep_last = 12
        if len(state.observations) <= max_total:
            return

        old = state.observations[:-keep_last]
        keep = state.observations[-keep_last:]
        payload = {
            "task": state.task,
            "existing_rolling_summary": state.rolling_summary,
            "observations_to_compact": [self._dump(o) for o in old],
        }
        prompt = (
            "You are compacting an agent's short-term memory to fit a small context window.\n"
            "Output ONLY JSON that conforms to the schema. No prose.\n\n"
            "Write a concise rolling_summary that preserves key decisions, failures, constraints, and progress.\n"
            "Keep it short but actionable for future planning.\n\n"
            f"INPUT:\n{dumps_compact(payload)}\n"
        )
        def _compact() -> dict:
            return llm.reason_json(prompt, schema_path=llm_schemas.COMPACTION)

        data = self._call_llm_with_retry(tracer=tracer, where="compaction", fn=_compact, allow_none=True)
        if isinstance(data, dict):
            new_summary = (data.get("rolling_summary") or "").strip()
            if new_summary:
                state.rolling_summary = new_summary[-8000:]
            state.observations = keep
            tracer.log({"type": "compaction", "kept": len(keep), "dropped": len(old)})
        else:
            state.compact(keep_last=keep_last, max_total=max_total)

    def _call_tool_with_retry(
        self,
        tools: ToolRegistry,
        ctx: RunContext,
        tool_name: str,
        tool_args: Dict[str, Any],
        tracer: JsonlTracer,
    ) -> ToolResult:
        last: Optional[ToolResult] = None
        for attempt in range(self.cfg.tool_max_retries + 1):
            if self.cfg.llm_heartbeat_seconds and attempt == 0:
                print(f"[TOOL] {tool_name} {self._format_tool_args(tool_args)}")
            if isinstance(getattr(self, "_stats", None), dict):
                self._stats["tool_calls"] = self._stats.get("tool_calls", 0) + 1
            result = tools.call(tool_name, tool_args, ctx)
            last = result
            if result.success or not result.retryable or attempt >= self.cfg.tool_max_retries:
                return result
            if isinstance(getattr(self, "_stats", None), dict):
                self._stats["retries"] = self._stats.get("retries", 0) + 1
            tracer.log(
                {
                    "type": "tool_retry",
                    "tool_name": tool_name,
                    "attempt": attempt + 1,
                    "error": result.error,
                }
            )
            time.sleep(self.cfg.tool_retry_backoff_seconds * (attempt + 1))
        return last or ToolResult(success=False, error="tool_failed")

    def _check_conditions(
        self,
        *,
        llm: TrackedLLM,
        kind: str,
        conditions: List[str],
        step: Step,
        observation: Observation,
    ) -> tuple[bool, Dict[str, Any]]:
        if os.getenv("AGENT_SKIP_PRECONDITIONS", "").lower() in {"1", "true", "yes"}:
            return True, {"ok": True, "failed": []}
        if not conditions:
            return True, {"ok": True, "failed": []}
        obs_view = {
            "source": observation.source,
            "errors": observation.errors,
            "salient_facts": observation.salient_facts[:5],
            "parsed": observation.parsed,
        }
        payload = {
            "kind": kind,
            "conditions": conditions,
            "step": self._dump(step),
            "observation": obs_view,
        }
        prompt = (
            "Evaluate whether the listed conditions are satisfied given the observation.\n"
            "Return JSON only.\n\n"
            f"INPUT:\n{dumps_compact(payload)}\n"
        )
        try:
            data = llm.reason_json(prompt, schema_path=llm_schemas.CONDITION_CHECK)
            ok = bool(data.get("ok"))
            failed = data.get("failed") or []
            if not isinstance(failed, list):
                failed = []
            report = {"ok": ok, "failed": failed}
            return ok, report
        except Exception:
            return True, {"ok": True, "failed": []}

    def _attempt_recovery(
        self,
        *,
        tools: ToolRegistry,
        ctx: RunContext,
        step: Step,
        tracer: JsonlTracer,
    ) -> Optional[Observation]:
        # Try pop-up handler, then lightweight exploration.
        obs = None
        if tools.has_tool("web_close_modal"):
            result = tools.call("web_close_modal", {}, ctx)
            obs = Perceptor().tool_result_to_observation("web_close_modal", result)
            tracer.log({"type": "recovery", "tool": "web_close_modal", "result": self._dump(result)})
        if tools.has_tool("web_find_elements"):
            query = None
            if isinstance(step.tool_args, dict):
                query = step.tool_args.get("query") or step.tool_args.get("text")
            if isinstance(query, str) and query:
                result = tools.call("web_find_elements", {"query": query}, ctx)
                obs = Perceptor().tool_result_to_observation("web_find_elements", result)
                tracer.log({"type": "recovery", "tool": "web_find_elements", "result": self._dump(result)})
        if tools.has_tool("web_scroll"):
            result = tools.call("web_scroll", {"delta_y": 800}, ctx)
            obs = Perceptor().tool_result_to_observation("web_scroll", result)
            tracer.log({"type": "recovery", "tool": "web_scroll", "result": self._dump(result)})
        if tools.has_tool("web_gui_snapshot"):
            # Attempt to refresh the grounding view if a URL is available.
            url = None
            if isinstance(step.tool_args, dict):
                url = step.tool_args.get("url")
            if isinstance(url, str) and url:
                result = tools.call("web_gui_snapshot", {"url": url}, ctx)
                obs = Perceptor().tool_result_to_observation("web_gui_snapshot", result)
                tracer.log({"type": "recovery", "tool": "web_gui_snapshot", "result": self._dump(result)})
        if tools.has_tool("desktop_som_snapshot"):
            try:
                result = tools.call("desktop_som_snapshot", {}, ctx)
                obs = Perceptor().tool_result_to_observation("desktop_som_snapshot", result)
                tracer.log({"type": "recovery", "tool": "desktop_som_snapshot", "result": self._dump(result)})
            except Exception as e:
                tracer.log({"type": "recovery_failed", "tool": "desktop_som_snapshot", "error": str(e)})
        if tools.has_tool("desktop"):
            try:
                # Gentle exploration: scroll a bit and rescan.
                tools.call("desktop", {"action": "scroll", "params": {"clicks": -400}}, ctx)
                result = tools.call("desktop", {"action": "hotkey", "params": {"keys": ["alt", "tab"]}}, ctx)
                obs = Perceptor().tool_result_to_observation("desktop", result)
                tracer.log({"type": "recovery", "tool": "desktop", "result": self._dump(result)})
            except Exception as e:
                tracer.log({"type": "recovery_failed", "tool": "desktop", "error": str(e)})
        return obs

    def _tool_category(self, tool_name: str) -> Optional[str]:
        if tool_name.startswith("web_"):
            return "web"
        if tool_name.startswith("desktop"):
            return "desktop"
        return None

    def _format_tool_list(self, tools: ToolRegistry, *, max_items: int = 10) -> str:
        names = [spec.name for spec in tools.list_tools()]
        if len(names) <= max_items:
            return ",".join(names)
        head = ",".join(names[:max_items])
        return f"{head},...(+{len(names) - max_items})"

    def _format_tool_args(self, args: Dict[str, Any], *, limit: int = 120) -> str:
        if not args:
            return ""
        try:
            text = json.dumps(args, ensure_ascii=False)
        except Exception:
            text = str(args)
        if len(text) > limit:
            text = text[: limit - 3] + "..."
        return text

    def _describe_tools_for_humans(self, tools: ToolRegistry) -> str:
        names = {spec.name for spec in tools.list_tools()}
        parts: List[str] = []
        if {"file_read", "file_write", "file_search", "list_dir", "glob_paths"} & names:
            parts.append("files")
        if "python_exec" in names:
            parts.append("python")
        if {"web_fetch", "web_search"} & names:
            parts.append("web")
        if {"memory_store", "memory_search"} & names:
            parts.append("memory")
        if "mail" in names:
            parts.append("mail")
        if {"web_gui_snapshot", "web_find_elements", "web_click", "web_type", "web_scroll"} & names:
            parts.append("browser automation")
        if {"desktop", "desktop_som_snapshot", "desktop_click"} & names:
            parts.append("desktop automation")
        if "shell_exec" in names:
            parts.append("shell")
        return ", ".join(parts) if parts else "basic tools"

    def _maybe_capture_ui_snapshot(
        self,
        *,
        tools: ToolRegistry,
        ctx: RunContext,
        step: Step,
        tool_result: ToolResult,
        tracer: JsonlTracer,
        step_snapshots_taken: set[str],
    ) -> Optional[Dict[str, Any]]:
        if step.id in step_snapshots_taken:
            return None
        category = self._tool_category(step.tool_name)
        if category is None:
            return None
        # Capture once per step; prefer existing screenshot paths if provided.
        snapshot = None
        if isinstance(tool_result.output, dict):
            if tool_result.output.get("screenshot"):
                snapshot = tool_result.output
        if snapshot is None:
            if category == "web" and tools.has_tool("web_gui_snapshot"):
                url = None
                if isinstance(step.tool_args, dict):
                    url = step.tool_args.get("url")
                if isinstance(url, str) and url:
                    result = tools.call("web_gui_snapshot", {"url": url, "include_screenshot": True}, ctx)
                    snapshot = result.output if isinstance(result.output, dict) else {"error": result.error}
            if category == "desktop" and tools.has_tool("desktop_som_snapshot"):
                try:
                    result = tools.call("desktop_som_snapshot", {}, ctx)
                    snapshot = result.output if isinstance(result.output, dict) else {"error": result.error}
                except Exception:
                    snapshot = None
        if snapshot is None:
            return None
        step_snapshots_taken.add(step.id)
        event = {"step_id": step.id, "tool_category": category, "ui_snapshot": snapshot}
        tracer.log({"type": "ui_snapshot", **event})
        return event

    def _call_llm_with_retry(
        self,
        *,
        tracer: JsonlTracer,
        where: str,
        fn,
        allow_none: bool = False,
        label: Optional[str] = None,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ):
        last_exc: Optional[Exception] = None
        retries = self.cfg.llm_max_retries if max_retries is None else max_retries
        for attempt in range(retries + 1):
            try:
                return self._call_llm_with_heartbeat(
                    fn,
                    label=label or where,
                    heartbeat_seconds=self.cfg.llm_heartbeat_seconds,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as exc:
                last_exc = exc
                tracer.log(
                    {
                        "type": "llm_retry",
                        "where": where,
                        "attempt": attempt + 1,
                        "error": str(exc),
                        "exc_type": type(exc).__name__,
                    }
                )
                if attempt >= retries:
                    break
                if isinstance(getattr(self, "_stats", None), dict):
                    self._stats["retries"] = self._stats.get("retries", 0) + 1
                time.sleep(self.cfg.llm_retry_backoff_seconds * (attempt + 1))
        if not allow_none:
            tracer.log({"type": "llm_error", "where": where, "error": str(last_exc), "exc_type": type(last_exc).__name__})
        return None

    def _call_llm_with_heartbeat(
        self,
        fn,
        *,
        label: str,
        heartbeat_seconds: Optional[float],
        timeout_seconds: Optional[int] = None,
    ):
        if not heartbeat_seconds or heartbeat_seconds <= 0:
            return fn()
        done = threading.Event()
        result: Dict[str, Any] = {}
        error: Dict[str, BaseException] = {}

        def _target() -> None:
            try:
                result["value"] = fn()
            except BaseException as exc:  # noqa: BLE001
                error["exc"] = exc
            finally:
                done.set()

        label_msg = label or "Thinking"
        print(f"[THINKING] {label_msg}")
        if timeout_seconds:
            print(f"[THINKING] Time limit: {timeout_seconds}s. If it takes longer, I will switch to a simpler approach.")
        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        start = time.monotonic()
        while not done.wait(timeout=heartbeat_seconds):
            elapsed = time.monotonic() - start
            print(f"[THINKING] Still working on {label_msg}... elapsed={elapsed:.1f}s")
        if error:
            raise error["exc"]
        return result.get("value")

    def _with_llm_timeout(self, llm: TrackedLLM, timeout_seconds: Optional[int], fn):
        prev = llm.default_timeout_seconds
        if timeout_seconds is not None:
            llm.default_timeout_seconds = timeout_seconds
        try:
            return fn()
        finally:
            llm.default_timeout_seconds = prev

    def _memory_updates(
        self,
        store: Optional[SqliteMemoryStore],
        task: str,
        step: Step,
        tool_result: ToolResult,
        obs: Observation,
        reflection: Reflection,
        run_id: str,
        tracer: JsonlTracer,
    ) -> None:
        if store is None:
            return
        allowed_kinds = {"experience", "procedure", "knowledge", "user_info"}
        try:
            if step.tool_name == "web_fetch" and tool_result.success and isinstance(tool_result.output, dict):
                url = tool_result.output.get("url")
                text = tool_result.output.get("text") or ""
                if url and text:
                    rec_id = store.upsert(
                        kind="knowledge",
                        key=str(url),
                        content=str(text)[:4000],
                        metadata={"source": "web_fetch", "task": task, "run_id": run_id},
                    )
                    tracer.log(
                        {
                            "type": "memory_write",
                            "status": "stored",
                            "step_id": step.id,
                            "kind": "knowledge",
                            "key": str(url),
                            "record_id": rec_id,
                            "source": "web_fetch",
                        }
                    )
            if reflection.memory_write and isinstance(reflection.memory_write, dict):
                payload = reflection.memory_write
                kind = payload.get("kind") or "knowledge"
                content = payload.get("content") or ""
                if kind not in allowed_kinds:
                    tracer.log(
                        {
                            "type": "memory_write",
                            "status": "skipped",
                            "step_id": step.id,
                            "reason": "invalid_kind",
                            "data": {"kind": kind},
                        }
                    )
                elif kind == "user_info" and not self.agent_cfg.allow_user_info_storage:
                    tracer.log(
                        {
                            "type": "memory_write",
                            "status": "skipped",
                            "step_id": step.id,
                            "reason": "user_info_disabled",
                            "data": {"kind": kind},
                        }
                    )
                elif content:
                    rec_id = store.upsert(
                        kind=kind,
                        key=payload.get("key"),
                        content=str(content)[:8000],
                        metadata=payload.get("metadata") or {"task": task, "run_id": run_id},
                    )
                    tracer.log(
                        {
                            "type": "memory_write",
                            "status": "stored",
                            "step_id": step.id,
                            "kind": kind,
                            "key": payload.get("key"),
                            "record_id": rec_id,
                        }
                    )
            elif reflection.lesson:
                rec_id = store.upsert(
                    kind="procedure",
                    key=f"lesson:{task[:120]}",
                    content=str(reflection.lesson)[:4000],
                    metadata={"task": task, "run_id": run_id},
                )
                tracer.log(
                    {
                        "type": "memory_write",
                        "status": "stored",
                        "step_id": step.id,
                        "kind": "procedure",
                        "key": f"lesson:{task[:120]}",
                        "record_id": rec_id,
                    }
                )
        except Exception as exc:
            tracer.log({"type": "memory_error", "error": str(exc)})

    def _stop(
        self,
        *,
        tracer: JsonlTracer,
        memory_store: Optional[SqliteMemoryStore],
        success: bool,
        reason: str,
        steps: int,
        run_id: str,
        llm_stats: TrackedLLM,
        task: str,
        state: AgentState,
        plan: Optional[Plan] = None,
        run_dir: Optional[Path] = None,
        started_at: Optional[str] = None,
        started_monotonic: Optional[float] = None,
    ) -> AgentRunResult:
        tracer.log(
            {
                "type": "stop",
                "reason": reason,
                "success": success,
                "steps": steps,
                "llm": {
                    "provider": llm_stats.provider,
                    "model": llm_stats.model,
                    "calls": llm_stats.calls,
                    "estimated_cost_usd": llm_stats.estimated_cost_usd,
                    "estimated_tokens": llm_stats.estimated_tokens,
                },
            }
        )

        if memory_store is not None:
            try:
                summary = state.rolling_summary or (state.observations[-1].raw if state.observations else "")
                memory_store.upsert(
                    kind="experience",
                    key=task[:200],
                    content=str(summary)[:8000],
                    metadata={
                        "success": success,
                        "stop_reason": reason,
                        "run_id": run_id,
                        "steps": steps,
                        "trace_path": str(tracer.path),
                        "planner_mode": self.planner_cfg.mode,
                    },
                )
                if success and plan is not None:
                    memory_store.upsert(
                        kind="procedure",
                        key=f"procedure:{task[:120]}",
                        content=dumps_compact(self._dump(plan), max_chars=12_000),
                        metadata={"run_id": run_id},
                    )
            except Exception:
                pass

        if run_dir:
            try:
                ended_at = datetime.now(timezone.utc).isoformat()
                duration_s = None
                if started_monotonic is not None:
                    duration_s = time.monotonic() - started_monotonic
                error_obj = None
                if not success:
                    error_obj = {"message": reason, "type": "stop_reason", "traceback": None}
                result = {
                    "ok": success,
                    "mode": self.mode_name,
                    "agent_id": self.agent_id or run_id,
                    "run_id": run_id,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "duration_s": duration_s,
                    "final_answer": None,
                    "error": error_obj,
                    "stats": {
                        "tool_calls": int(self._stats.get("tool_calls", 0)) if hasattr(self, "_stats") else 0,
                        "llm_calls": int(llm_stats.calls),
                        "retries": int(self._stats.get("retries", 0)) if hasattr(self, "_stats") else 0,
                    },
                }
                Path(run_dir / "result.json").write_text(
                    json.dumps(result, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except Exception:
                pass

        return AgentRunResult(
            success=success,
            stop_reason=reason,
            steps_executed=steps,
            run_id=run_id,
            trace_path=str(tracer.path),
        )

    @staticmethod
    def _dump(obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()  # type: ignore[attr-defined]
        if hasattr(obj, "dict"):
            return obj.dict()  # type: ignore[attr-defined]
        return obj
