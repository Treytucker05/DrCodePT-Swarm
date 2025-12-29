from __future__ import annotations

import logging
import textwrap
from typing import Any, Dict, List, Optional

from agent.llm.base import LLMClient
from agent.llm import schemas as llm_schemas

from ..jsonio import dumps_compact
from ..models import Observation, Plan, Reflection, Step, ToolResult
from ..pydantic_compat import model_dump, model_validate
from ..tools.registry import ToolRegistry
from .base import Planner
from .utils import coerce_plan_dict

logger = logging.getLogger(__name__)


class ReActPlanner(Planner):
    """
    ReAct (Reasoning + Acting) planner for single-step decisions.

    This planner implements the ReAct pattern:
    1. Observe the current state
    2. Think about what to do next
    3. Choose ONE action to execute
    4. Repeat

    It can optionally use a model router for LLM selection.
    """

    def __init__(
        self,
        *,
        llm: LLMClient,
        tools: ToolRegistry,
        unsafe_mode: bool,
        model_router: Optional[Any] = None,
    ):
        self._llm = llm
        self._tools = tools
        self._unsafe_mode = unsafe_mode
        self._model_router = model_router

    def _get_planning_llm(self) -> LLMClient:
        """Get the LLM to use for planning. Uses router if available."""
        if self._model_router is not None:
            try:
                routed_llm = self._model_router.get_llm_for_task("plan next step")
                if routed_llm is not None:
                    return routed_llm
            except Exception as e:
                logger.warning(f"Model router failed, using default: {e}")
        return self._llm

    def plan(self, *, task: str, observations: List[Observation], memories: List[dict]) -> Plan:
        """
        Plan the next single action to take.

        This is the core ReAct decision: given the current state, what ONE action should we take?
        """
        tool_catalog = self._build_tool_catalog()
        recent_obs = [model_dump(o) for o in observations[-12:]]

        prompt = self._build_plan_prompt(
            task=task,
            tool_catalog=tool_catalog,
            memories=memories,
            recent_obs=recent_obs,
        )

        # Use router-selected LLM if available
        llm = self._get_planning_llm()
        data = llm.reason_json(prompt, schema_path=llm_schemas.PLAN_NEXT_STEP)
        data = coerce_plan_dict(data)
        plan = model_validate(Plan, data)

        # Validate the plan
        return self._validate_plan(plan, task)

    def _build_tool_catalog(self) -> List[Dict[str, Any]]:
        """Build the tool catalog for the prompt."""
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "dangerous": spec.dangerous,
                "args_schema": self._tools.tool_args_schema(spec.name),
            }
            for spec in self._tools.list_tools()
        ]

    def _build_plan_prompt(
        self,
        *,
        task: str,
        tool_catalog: List[Dict[str, Any]],
        memories: List[dict],
        recent_obs: List[dict],
    ) -> str:
        """Build the planning prompt."""
        return textwrap.dedent(
            f"""
            Goal: {task}
            unsafe_mode: {self._unsafe_mode}

            You are an autonomous agent planner operating in a closed-loop.

            Choose EXACTLY ONE next step to execute using an available tool.
            - If the goal is already satisfied, output a single step using tool_name="finish" with a short summary.
            - Prefer minimal, testable actions and specify success_criteria.
            - Add preconditions and postconditions when useful (short, checkable).
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
                    "success_criteria":["..."],
                    "preconditions":["..."],
                    "postconditions":["..."]
                  }}
                ]
              }}
            Return JSON only. No markdown, no prose.
            """
        ).strip()

    def _validate_plan(self, plan: Plan, task: str) -> Plan:
        """Validate the plan and handle edge cases."""
        # Ensure tool exists; if not, force a replan
        if not plan.steps:
            return Plan(
                goal=task,
                steps=[Step(
                    goal="No step produced; ask human.",
                    tool_name="human_ask",
                    tool_args={"question": "Planner returned no steps. Provide guidance?"}
                )]
            )

        step = plan.steps[0]
        if not self._tools.has_tool(step.tool_name):
            return Plan(
                goal=task,
                steps=[Step(
                    goal="Unknown tool; ask human.",
                    tool_name="human_ask",
                    tool_args={"question": f"Planner selected unknown tool: {step.tool_name}. What should it do instead?"}
                )]
            )

        # Return only the first step (ReAct is single-step)
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
        """
        Repair after a failed step by replanning with failure context.

        In ReAct mode, repair is essentially replanning with extra context
        about what went wrong.
        """
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

        # Use router-selected LLM if available
        llm = self._get_planning_llm()
        data = llm.reason_json(prompt, schema_path=llm_schemas.PLAN_NEXT_STEP)
        data = coerce_plan_dict(data)
        plan = model_validate(Plan, data)

        if plan.steps:
            return Plan(goal=task, steps=[plan.steps[0]])
        return None
