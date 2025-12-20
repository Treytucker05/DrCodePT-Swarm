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


class PlanFirstPlanner(Planner):
    def __init__(
        self,
        *,
        llm: LLMClient,
        tools: ToolRegistry,
        unsafe_mode: bool,
        num_candidates: int = 1,
        max_steps: int = 6,
    ):
        self._llm = llm
        self._tools = tools
        self._unsafe_mode = unsafe_mode
        self._num_candidates = max(1, num_candidates)
        self._max_steps = max(1, max_steps)

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

        if self._num_candidates > 1:
            prompt = textwrap.dedent(
                f"""
                Goal: {task}
                unsafe_mode: {self._unsafe_mode}

                Generate {self._num_candidates} candidate plans and score each 1-10.
                - Each plan should have <= {self._max_steps} steps and end with a finish step.
                - Do not use dangerous tools unless unsafe_mode=true.

                Available tools:
                {dumps_compact(tool_catalog)}

                Retrieved long-term memory:
                {dumps_compact(memories)}

                Recent observations:
                {dumps_compact(recent_obs)}

                Return STRICT JSON:
                  {{
                    "plans": [
                      {{"score": 1, "plan": {{"goal": "...", "steps": [ ... ]}}, "notes": "..." }}
                    ]
                  }}
                Return JSON only.
                """
            ).strip()
            data = self._llm.complete_json(prompt, schema_path=llm_schemas.PLAN_CANDIDATES)
            best = self._pick_best_candidate(data)
            if best is not None:
                return best

        prompt = textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            Create a concise multi-step plan (<= {self._max_steps} steps) and end with a finish step.
            - Do not use dangerous tools unless unsafe_mode=true.
            - Prefer writing only inside the run workspace unless unsafe_mode=true.

            Available tools:
            {dumps_compact(tool_catalog)}

            Retrieved long-term memory:
            {dumps_compact(memories)}

            Recent observations:
            {dumps_compact(recent_obs)}

            Return STRICT JSON Plan only:
              {{"goal":"...", "steps":[ ... ]}}
            """
        ).strip()
        data = self._llm.complete_json(prompt, schema_path=llm_schemas.PLAN)
        return model_validate(Plan, data)

    def _pick_best_candidate(self, data: Dict[str, Any]) -> Optional[Plan]:
        try:
            plans = data.get("plans") or []
            best_score = None
            best_plan = None
            for item in plans:
                score = item.get("score")
                plan_data = item.get("plan")
                if score is None or plan_data is None:
                    continue
                try:
                    plan = model_validate(Plan, plan_data)
                except Exception:
                    continue
                if best_score is None or score > best_score:
                    best_score = score
                    best_plan = plan
            return best_plan
        except Exception:
            return None

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
            """
        ).strip()
        data = self._llm.complete_json(prompt, schema_path=llm_schemas.PLAN)
        try:
            return model_validate(Plan, data)
        except Exception:
            return None
