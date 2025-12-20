from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
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

        self.provider = getattr(llm, "provider", "unknown")
        self.model = getattr(llm, "model", "unknown")

    @property
    def cost_per_1k(self) -> Optional[float]:
        return self._cost_per_1k

    def complete_json(self, prompt: str, *, schema_path: Path, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
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

    def run(self, task: str) -> AgentRunResult:
        run_id = f"{_utc_ts_id()}_{uuid4().hex[:8]}"
        repo_root = Path(__file__).resolve().parents[2]
        run_dir = self.run_dir or (repo_root / "runs" / "autonomous" / run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        workspace_dir = run_dir / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        ctx = RunContext(run_id=run_id, run_dir=run_dir, workspace_dir=workspace_dir)

        tracer = JsonlTracer(run_dir / "trace.jsonl")
        perceptor = Perceptor()
        tracked_llm = TrackedLLM(self.llm)
        reflector = Reflector(llm=tracked_llm, pre_mortem_enabled=self.agent_cfg.pre_mortem_enabled)

        memory_store = self.memory_store or self._open_default_memory_store()
        tools = self.tools or build_default_tool_registry(self.agent_cfg, run_dir, memory_store=memory_store)

        if self.cfg.cost_budget_usd is not None and tracked_llm.cost_per_1k is None:
            tracer.log(
                {
                    "type": "stop",
                    "reason": "cost_budget_requires_LLM_COST_PER_1K_TOKENS_USD",
                    "budget_usd": self.cfg.cost_budget_usd,
                }
            )
            return AgentRunResult(
                success=False,
                stop_reason="cost_budget_requires_LLM_COST_PER_1K_TOKENS_USD",
                steps_executed=0,
                run_id=run_id,
                trace_path=str(run_dir / "trace.jsonl"),
            )

        planner = self._make_planner(tracked_llm, tools)

        state = AgentState(task=task)
        loop_detector = LoopDetector(window=self.cfg.loop_window, repeat_threshold=self.cfg.loop_repeat_threshold)

        obs0 = perceptor.text_to_observation("task", task)
        state.add_observation(obs0)
        tracer.log({"type": "observation", "observation": self._dump(obs0)})

        start = time.monotonic()
        steps_executed = 0
        consecutive_no_progress = 0
        last_plan_hash: Optional[str] = None

        current_plan: Optional[Plan] = None

        try:
            while True:
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
                    )

                self._maybe_compact_state(state, tracked_llm, tracer)

                memories = self._retrieve_memories(memory_store, task)

                if self.planner_cfg.mode == "react":
                    try:
                        plan = planner.plan(task=task, observations=state.observations, memories=memories)
                    except Exception as exc:
                        tracer.log({"type": "llm_error", "where": "plan", "error": str(exc), "exc_type": type(exc).__name__})
                        return self._stop(
                            tracer=tracer,
                            memory_store=memory_store,
                            success=False,
                            reason="llm_error",
                            steps=steps_executed,
                            run_id=run_id,
                            llm_stats=tracked_llm,
                            task=task,
                            state=state,
                        )
                    current_plan = plan
                    state.current_plan = current_plan
                    state.current_step_idx = 0
                else:
                    if current_plan is None or state.current_step_idx >= len(current_plan.steps):
                        try:
                            current_plan = planner.plan(task=task, observations=state.observations, memories=memories)
                        except Exception as exc:
                            tracer.log({"type": "llm_error", "where": "plan", "error": str(exc), "exc_type": type(exc).__name__})
                            return self._stop(
                                tracer=tracer,
                                memory_store=memory_store,
                                success=False,
                                reason="llm_error",
                                steps=steps_executed,
                                run_id=run_id,
                                llm_stats=tracked_llm,
                                task=task,
                                state=state,
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
                    )

                step = plan.steps[0] if self.planner_cfg.mode == "react" else plan.steps[state.current_step_idx]

                if self.agent_cfg.pre_mortem_enabled:
                    prem = reflector.pre_mortem(task=task, step=step, observation=state.observations[-1])
                    tracer.log({"type": "premortem", "step_id": step.id, "data": prem})

                tool_result = self._call_tool_with_retry(tools, ctx, step.tool_name, step.tool_args, tracer)
                obs = perceptor.tool_result_to_observation(step.tool_name, tool_result)
                state.add_observation(obs)

                if tool_result.metadata.get("unsafe_blocked") is True:
                    tracer.log(
                        {
                            "type": "step",
                            "step_index": steps_executed,
                            "plan": self._dump(plan),
                            "action": {"tool_name": step.tool_name, "tool_args": step.tool_args},
                            "result": self._dump(tool_result),
                            "observation": self._dump(obs),
                            "reflection": {"status": "replan", "explanation_short": "unsafe_blocked", "next_hint": tool_result.error or ""},
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
                    )

                reflection = reflector.reflect(task=task, step=step, tool_result=tool_result, observation=obs)

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

                self._memory_updates(memory_store, task, step, tool_result, obs, run_id, tracer)

                action_signature = f"{step.tool_name}:{_json_dumps(step.tool_args)}"
                if loop_detector.update(action_signature, state.state_fingerprint()):
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
                    )

                if reflection.status == "success":
                    consecutive_no_progress = 0
                    if self.planner_cfg.mode == "plan_first":
                        state.current_step_idx += 1
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
                    )

                if reflection.status == "minor_repair":
                    try:
                        repaired = planner.repair(
                            task=task,
                            observations=state.observations,
                            memories=memories,
                            failed_step=step,
                            tool_result=tool_result,
                            reflection=reflection,
                        )
                    except Exception as exc:
                        tracer.log({"type": "llm_error", "where": "repair", "error": str(exc), "exc_type": type(exc).__name__})
                        repaired = None
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

    def _retrieve_memories(self, store: Optional[SqliteMemoryStore], task: str) -> List[dict]:
        if store is None:
            return []
        try:
            results = store.search(task, limit=8)
            return [
                {
                    "kind": r.kind,
                    "key": r.key,
                    "content": r.content[:2000],
                    "metadata": r.metadata,
                    "updated_at": r.updated_at,
                }
                for r in results
            ]
        except Exception:
            return []

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
        try:
            data = llm.complete_json(prompt, schema_path=llm_schemas.COMPACTION)
            new_summary = (data.get("rolling_summary") or "").strip()
            if new_summary:
                state.rolling_summary = new_summary[-8000:]
            state.observations = keep
            tracer.log({"type": "compaction", "kept": len(keep), "dropped": len(old)})
        except Exception as exc:
            tracer.log({"type": "compaction_error", "error": str(exc), "exc_type": type(exc).__name__})
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
            result = tools.call(tool_name, tool_args, ctx)
            last = result
            if result.success or not result.retryable or attempt >= self.cfg.tool_max_retries:
                return result
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

    def _memory_updates(
        self,
        store: Optional[SqliteMemoryStore],
        task: str,
        step: Step,
        tool_result: ToolResult,
        obs: Observation,
        run_id: str,
        tracer: JsonlTracer,
    ) -> None:
        if store is None:
            return
        try:
            if step.tool_name == "web_fetch" and tool_result.success and isinstance(tool_result.output, dict):
                url = tool_result.output.get("url")
                text = tool_result.output.get("text") or ""
                if url and text:
                    store.upsert(
                        kind="knowledge",
                        key=str(url),
                        content=str(text)[:4000],
                        metadata={"source": "web_fetch", "task": task, "run_id": run_id},
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
