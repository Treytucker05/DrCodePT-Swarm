from __future__ import annotations

import json
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

_TOOL_ALIASES = {
    "functions.exec_command": "shell_exec",
    "exec_command": "shell_exec",
    "shell": "shell_exec",
    "shell_exec": "shell_exec",
    "write_file": "file_write",
    "file_write": "file_write",
    "read_file": "file_read",
    "file_read": "file_read",
    "list_directory": "list_dir",
    "list_dir": "list_dir",
    "list_files": "list_dir",
    "dir_list": "list_dir",
    "python": "python_exec",
    "python_exec": "python_exec",
    "search_files": "file_search",
    "file_search": "file_search",
    "glob": "glob_paths",
    "glob_paths": "glob_paths",
    "web_search": "web_search",
    "web_fetch": "web_fetch",
    "search_memory": "memory_search",
    "memory_search": "memory_search",
    "memory_store": "memory_store",
}


def _normalize_tool_name(tool_name: str) -> str:
    if not tool_name:
        return tool_name
    return _TOOL_ALIASES.get(tool_name, tool_name)


def _normalize_tool_args(tool_name: str, tool_args: dict) -> dict:
    if isinstance(tool_args, list):
        normalized: Dict[str, Any] = {}
        for item in tool_args:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            if not isinstance(key, str) or not key:
                continue
            normalized[key] = item.get("value")
        tool_args = normalized
    if not isinstance(tool_args, dict):
        return {}
    args = dict(tool_args)
    if tool_name == "shell_exec":
        if "cmd" in args and "command" not in args:
            args["command"] = args.pop("cmd")
        if "workdir" in args and "cwd" not in args:
            args["cwd"] = args.pop("workdir")
        if "timeout" in args and "timeout_seconds" not in args:
            args["timeout_seconds"] = args.pop("timeout")
    elif tool_name == "file_write":
        if "file_path" in args and "path" not in args:
            args["path"] = args.pop("file_path")
        if "filename" in args and "path" not in args:
            args["path"] = args.pop("filename")
        if "text" in args and "content" not in args:
            args["content"] = args.pop("text")
        content = args.get("content")
        if isinstance(content, (dict, list)):
            args["content"] = json.dumps(content, ensure_ascii=False)
        elif content is None:
            args["content"] = ""
        elif not isinstance(content, str):
            args["content"] = str(content)
    elif tool_name == "file_read":
        if "file_path" in args and "path" not in args:
            args["path"] = args.pop("file_path")
        if "filename" in args and "path" not in args:
            args["path"] = args.pop("filename")
    elif tool_name == "list_dir":
        if "dir" in args and "path" not in args:
            args["path"] = args.pop("dir")
        if "directory" in args and "path" not in args:
            args["path"] = args.pop("directory")
    elif tool_name == "python_exec":
        if "script" in args and "code" not in args:
            args["code"] = args.pop("script")
    elif tool_name == "file_search":
        if "path" in args and "root" not in args:
            args["root"] = args.pop("path")
        if "text" in args and "query" not in args:
            args["query"] = args.pop("text")
    elif tool_name == "glob_paths":
        if "path" in args and "root" not in args:
            args["root"] = args.pop("path")
        if "glob" in args and "pattern" not in args:
            args["pattern"] = args.pop("glob")
    return args



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
            - If the last step already succeeded, do NOT repeat the same tool + args. Move forward (verify or finish).
            - For file_write: content MUST be a string. If writing JSON, use json.dumps(...) or a literal like "[]".
            - If the task asks to search/retrieve memory, you MUST call memory_search after memory_store.
            - If the task asks to write retrieved results to a file, you MUST include a file_write step with the actual content.
            - If unsafe_mode is false, avoid shell_exec unless necessary; prefer file tools.
            - IMPORTANT: tool_name must match exactly one of the available tools listed below.

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
        step.tool_name = _normalize_tool_name(step.tool_name)
        step.tool_args = _normalize_tool_args(step.tool_name, step.tool_args)
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
