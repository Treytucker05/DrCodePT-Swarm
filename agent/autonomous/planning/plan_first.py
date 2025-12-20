from __future__ import annotations

import textwrap
from typing import Any, Dict, List, Optional

from agent.llm.base import LLMClient
from agent.llm import schemas as llm_schemas

from ..jsonio import dumps_compact
from ..models import Observation, Plan, Reflection, Step, ToolResult
from ..pydantic_compat import model_dump, model_validate
from ..tools.registry import ToolRegistry
from .base import Planner
from .utils import coerce_plan_candidates_dict, coerce_plan_dict


class PlanFirstPlanner(Planner):
    def __init__(
        self,
        *,
        llm: LLMClient,
        tools: ToolRegistry,
        unsafe_mode: bool,
        num_candidates: int = 1,
        max_steps: int = 6,
        use_dppm: bool = True,
        use_tot: bool = True,
    ):
        self._llm = llm
        self._tools = tools
        self._unsafe_mode = unsafe_mode
        self._num_candidates = max(1, num_candidates)
        self._max_steps = max(1, max_steps)
        self._use_dppm = use_dppm
        self._use_tot = use_tot
        self._fallback_plan: Optional[Plan] = None

    def plan(self, *, task: str, observations: List[Observation], memories: List[dict]) -> Plan:
        tool_catalog = [
            {
                "name": spec.name,
                "description": spec.description,
                "dangerous": spec.dangerous,
                "args_schema": self._tools.tool_args_schema(spec.name),
            }
            for spec in self._tools.list_tools()
        ]
        recent_obs = [model_dump(o) for o in observations[-18:]]
        dppm_plan = None
        if self._use_dppm:
            dppm_plan = self._plan_via_dppm(task, tool_catalog, memories, recent_obs)

        if self._use_tot:
            candidates = self._plan_candidates(task, tool_catalog, memories, recent_obs)
            if dppm_plan is not None:
                candidates.append(
                    {
                        "plan": model_dump(dppm_plan),
                        "scores": {
                            "grounding_confidence": 6,
                            "tool_feasibility": 6,
                            "destructiveness": 3,
                            "length": len(dppm_plan.steps),
                        },
                    }
                )
            best, fallback = self._pick_best_candidate(candidates)
            self._fallback_plan = fallback
            if best is not None:
                return best

        if dppm_plan is not None:
            return dppm_plan

        return self._plan_direct(task, tool_catalog, memories, recent_obs)

    def fallback_plan(self) -> Optional[Plan]:
        return self._fallback_plan

    def consume_fallback(self) -> Optional[Plan]:
        plan = self._fallback_plan
        self._fallback_plan = None
        return plan

    def _plan_direct(self, task: str, tool_catalog: List[dict], memories: List[dict], recent_obs: List[dict]) -> Plan:
        prompt = textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            Create a concise multi-step plan (<= {self._max_steps} steps) and end with a finish step.
            - Do not use dangerous tools unless unsafe_mode=true.
            - Prefer writing only inside the run workspace unless unsafe_mode=true.
            - Include preconditions/postconditions when useful.
            - tool_args must be a list of {{"key":"...","value":"..."}} pairs (values as strings; encode JSON if needed).

            Available tools:
            {dumps_compact(tool_catalog)}

            Retrieved long-term memory:
            {dumps_compact(memories)}

            Recent observations:
            {dumps_compact(recent_obs)}

            Return STRICT JSON Plan only:
              {{"goal":"...", "steps":[{{"id":"...","goal":"...","rationale_short":"...","tool_name":"...","tool_args":[{{"key":"arg_name","value":"arg_value"}}],"success_criteria":["..."],"preconditions":["..."],"postconditions":["..."]}}]}}
            """
        ).strip()
        data = self._llm.reason_json(prompt, schema_path=llm_schemas.PLAN)
        data = coerce_plan_dict(data)
        return model_validate(Plan, data)

    def _plan_candidates(self, task: str, tool_catalog: List[dict], memories: List[dict], recent_obs: List[dict]) -> List[dict]:
        count = max(3, self._num_candidates)
        prompt = textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            Generate {count} candidate plans.
            - Each plan should have <= {self._max_steps} steps and end with a finish step.
            - Do not use dangerous tools unless unsafe_mode=true.
            - Include preconditions/postconditions when useful.
            - tool_args must be a list of {{"key":"...","value":"..."}} pairs (values as strings; encode JSON if needed).

            Score each plan (1-10) on:
            - grounding_confidence (higher = more grounded in available observations)
            - tool_feasibility (higher = tools likely available/valid)
            - destructiveness (higher = more destructive; avoid)
            - length (higher = longer; avoid)

            Available tools:
            {dumps_compact(tool_catalog)}

            Retrieved long-term memory:
            {dumps_compact(memories)}

            Recent observations:
            {dumps_compact(recent_obs)}

            Return STRICT JSON:
              {{
                "plans": [
                  {{
                    "score": 1,
                    "scores": {{
                      "grounding_confidence": 1,
                      "tool_feasibility": 1,
                      "destructiveness": 1,
                      "length": 1
                    }},
                    "plan": {{
                      "goal": "...",
                      "steps": [
                        {{
                          "id":"...",
                          "goal":"...",
                          "rationale_short":"...",
                          "tool_name":"...",
                          "tool_args":[{{"key":"arg_name","value":"arg_value"}}],
                          "success_criteria":["..."],
                          "preconditions":["..."],
                          "postconditions":["..."]
                        }}
                      ]
                    }},
                    "notes": "..."
                  }}
                ]
              }}
            Return JSON only.
            """
        ).strip()
        data = self._llm.reason_json(prompt, schema_path=llm_schemas.PLAN_CANDIDATES)
        data = coerce_plan_candidates_dict(data)
        plans = data.get("plans") if isinstance(data, dict) else None
        if not isinstance(plans, list):
            return []
        return plans

    def _plan_via_dppm(self, task: str, tool_catalog: List[dict], memories: List[dict], recent_obs: List[dict]) -> Optional[Plan]:
        prompt = textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            Decompose the task into 2-5 subtasks with dependencies (DPPM-lite).
            Each subtask should be short and verifiable.

            Available tools:
            {dumps_compact(tool_catalog)}

            Retrieved long-term memory:
            {dumps_compact(memories)}

            Recent observations:
            {dumps_compact(recent_obs)}

            Return STRICT JSON:
              {{"subtasks":[{{"id":"t1","goal":"...","depends_on":["t0"],"notes":"..."}}]}}
            """
        ).strip()
        try:
            data = self._llm.reason_json(prompt, schema_path=llm_schemas.TASK_DECOMPOSITION)
        except Exception:
            return None
        subtasks = data.get("subtasks") if isinstance(data, dict) else None
        if not isinstance(subtasks, list) or not subtasks:
            return None

        ordered = self._order_subtasks(subtasks)
        subplans: List[Plan] = []
        for st in ordered:
            goal = st.get("goal") if isinstance(st, dict) else None
            if not isinstance(goal, str) or not goal.strip():
                continue
            try:
                subplan = self._plan_direct(goal.strip(), tool_catalog, memories, recent_obs)
                subplans.append(subplan)
            except Exception:
                continue
        if not subplans:
            return None
        return self._merge_subplans(task, subplans)

    def _order_subtasks(self, subtasks: List[dict]) -> List[dict]:
        # Simple topological ordering by depends_on (best-effort).
        remaining = list(subtasks)
        ordered: List[dict] = []
        seen: set[str] = set()
        for _ in range(len(subtasks) * 2):
            progressed = False
            for st in list(remaining):
                sid = str(st.get("id") or "")
                deps = st.get("depends_on") or []
                if not deps or all(str(d) in seen for d in deps):
                    ordered.append(st)
                    seen.add(sid)
                    remaining.remove(st)
                    progressed = True
            if not progressed:
                break
        ordered.extend(remaining)
        return ordered

    def _merge_subplans(self, task: str, plans: List[Plan]) -> Plan:
        steps: List[Step] = []
        for plan in plans:
            for step in plan.steps:
                if step.tool_name == "finish":
                    continue
                steps.append(step)
        # Trim to max_steps - 1 to leave room for finish
        if len(steps) >= self._max_steps:
            steps = steps[: max(1, self._max_steps - 1)]
        steps.append(Step(goal="Finish task", tool_name="finish", tool_args={"summary": task}))
        return Plan(goal=task, steps=steps)

    def _score_candidate(self, scores: Dict[str, Any], plan: Plan) -> float:
        def _norm(value: Any, default: int = 5) -> int:
            try:
                v = int(value)
            except Exception:
                v = default
            return max(1, min(10, v))

        ground = _norm(scores.get("grounding_confidence"))
        feas = _norm(scores.get("tool_feasibility"))
        destr = _norm(scores.get("destructiveness"))
        length_raw = _norm(scores.get("length"), default=len(plan.steps))
        length_score = max(1, 11 - length_raw)
        destr_score = max(1, 11 - destr)
        return (0.35 * ground) + (0.35 * feas) + (0.2 * length_score) + (0.1 * destr_score)

    def _pick_best_candidate(self, candidates: List[dict]) -> tuple[Optional[Plan], Optional[Plan]]:
        scored: List[tuple[float, Plan]] = []
        for item in candidates:
            if not isinstance(item, dict):
                continue
            plan_data = item.get("plan")
            scores = item.get("scores") or {}
            if not isinstance(plan_data, dict):
                continue
            try:
                plan = model_validate(Plan, plan_data)
            except Exception:
                continue
            score_val = self._score_candidate(scores if isinstance(scores, dict) else {}, plan)
            scored.append((score_val, plan))
        if not scored:
            return None, None
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]
        fallback = scored[1][1] if len(scored) > 1 else None
        return best, fallback

    def repair(
        self,
        *,
        task: str,
        observations: List[Observation],
        memories: List[dict],
        failed_step: Step,
        tool_result: ToolResult,
        reflection: Reflection,
    ) -> Plan | None:
        tool_catalog = [
            {
                "name": spec.name,
                "description": spec.description,
                "dangerous": spec.dangerous,
                "args_schema": self._tools.tool_args_schema(spec.name),
            }
            for spec in self._tools.list_tools()
        ]
        recent_obs = [model_dump(o) for o in observations[-18:]]
        failure = {
            "failed_step": model_dump(failed_step),
            "tool_result": model_dump(tool_result),
            "reflection": model_dump(reflection),
        }
        prompt = textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            The plan step failed. Decide one:
            - retry same step with adjusted args
            - swap tool
            - regenerate this step
            - regenerate a new full plan

            Failure context:
            {dumps_compact(failure)}

            Available tools:
            {dumps_compact(tool_catalog)}

            Retrieved long-term memory:
            {dumps_compact(memories)}

            Recent observations:
            {dumps_compact(recent_obs)}

            Return STRICT JSON Plan. Keep it <= {self._max_steps} steps and end with finish if appropriate.
            Include preconditions/postconditions when useful.
            """
        ).strip()
        data = self._llm.reason_json(prompt, schema_path=llm_schemas.PLAN)
        data = coerce_plan_dict(data)
        try:
            return model_validate(Plan, data)
        except Exception:
            return None
