from __future__ import annotations

import textwrap
from typing import List

from agent.llm.base import LLMClient
from agent.llm import schemas as llm_schemas

from ..jsonio import dumps_compact
from ..models import Observation, Plan, Reflection, Step, ToolResult
from ..pydantic_compat import model_dump, model_validate
from ..tools.registry import ToolRegistry
from .base import Planner
from .utils import coerce_plan_dict


class ReActPlanner(Planner):
    def __init__(self, *, llm: LLMClient, tools: ToolRegistry, unsafe_mode: bool):
        self._llm = llm
        self._tools = tools
        self._unsafe_mode = unsafe_mode

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

        recent_obs = [model_dump(o) for o in observations[-12:]]
        prompt = textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            You are an autonomous agent planner operating in a closed-loop.

            Choose EXACTLY ONE next step to execute using an available tool.
            - If the goal is already satisfied, output a single step using tool_name="finish" with a short summary.
            - Do not use dangerous tools unless unsafe_mode=true.
            - Prefer minimal, testable actions and specify success_criteria.
            - tool_args must be a list of {{"key":"...","value":"..."}} pairs (values as strings; encode JSON if needed).

            Available tools (name/description/schema):
            {dumps_compact(tool_catalog)}

            Retrieved long-term memory (keyword+recency):
            {dumps_compact(memories)}

            Recent observations:
            {dumps_compact(recent_obs)}

            Return STRICT JSON matching:
              {{
                "goal": "<string>",
                "steps": [
                  {{
                    "id":"<string>",
                    "goal":"<string>",
                    "rationale_short":"<string>",
                    "tool_name":"<string>",
                    "tool_args":[{{"key":"arg_name","value":"arg_value"}}],
                    "success_criteria":["..."]
                  }}
                ]
              }}
            Return JSON only. No markdown, no prose.
            """
        ).strip()

        data = self._llm.complete_json(prompt, schema_path=llm_schemas.PLAN_NEXT_STEP)
        data = coerce_plan_dict(data)
        plan = model_validate(Plan, data)

        # Ensure tool exists; if not, force a replan by returning a finish step with error (runner will treat as failure).
        if not plan.steps:
            return Plan(goal=task, steps=[Step(goal="No step produced; ask human.", tool_name="human_ask", tool_args={"question": "Planner returned no steps. Provide guidance?"})])
        step = plan.steps[0]
        if not self._tools.has_tool(step.tool_name):
            return Plan(goal=task, steps=[Step(goal="Unknown tool; ask human.", tool_name="human_ask", tool_args={"question": f"Planner selected unknown tool: {step.tool_name}. What should it do instead?"})])
        return Plan(goal=task, steps=[step])

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
        # In ReAct mode, repair == replan with failure context.
        recent_obs = [model_dump(o) for o in observations[-12:]]
        failure = {
            "failed_step": model_dump(failed_step),
            "tool_result": model_dump(tool_result),
            "reflection": model_dump(reflection),
        }
        prompt = textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            The last step failed or needs repair. Propose ONE next step.

            Failure context:
            {dumps_compact(failure)}

            Retrieved long-term memory:
            {dumps_compact(memories)}

            Recent observations:
            {dumps_compact(recent_obs)}

            Return STRICT JSON Plan with exactly one step (or finish).
            """
        ).strip()
        data = self._llm.complete_json(prompt, schema_path=llm_schemas.PLAN_NEXT_STEP)
        data = coerce_plan_dict(data)
        plan = model_validate(Plan, data)
        if plan.steps:
            return Plan(goal=task, steps=[plan.steps[0]])
        return None
