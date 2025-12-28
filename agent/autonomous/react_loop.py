"""
ReAct + Reflexion Agent Loop
Based on arxiv.org/abs/2210.03629 (ReAct) and arxiv.org/abs/2303.11366 (Reflexion)

Core loop: Perception -> Decide Next Step -> Action -> Observation -> Reflection -> Memory -> Repeat
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

from agent.llm.codex_cli_client import CodexCliClient
from agent.memory.memory_manager import MemoryManager


@dataclass
class Step:
    """One step in the agent's execution."""

    thought: str  # What the agent is thinking
    action: str  # What tool/action to use
    action_input: Dict[str, Any]  # Arguments for the action
    observation: str  # Result of the action
    reflection: str  # Self-critique of this step
    success: bool  # Did this step succeed?


class ReActAgent:
    """Agent using ReAct + Reflexion architecture."""

    def __init__(
        self,
        tools: Dict[str, Any],
        memory: MemoryManager,
        *,
        tool_descriptions: Optional[Dict[str, str]] = None,
        llm: Optional[CodexCliClient] = None,
        run_dir: Optional[Path] = None,
        max_steps: int = 50,  # Increased from 15 to allow complex tasks
        max_retries: int = 3,
    ):
        base = llm or CodexCliClient.from_env()
        self.llm_quick = CodexCliClient(
            codex_bin=base.codex_bin,
            model=base.model,
            timeout_seconds=base.timeout_seconds,
            profile_reason="react",
            profile_exec=base.profile_exec,
            workdir=base.workdir,
            log_dir=base.log_dir,
        )
        self.llm_reason = CodexCliClient(
            codex_bin=base.codex_bin,
            model=base.model,
            timeout_seconds=base.timeout_seconds,
            profile_reason="reason",
            profile_exec=base.profile_exec,
            workdir=base.workdir,
            log_dir=base.log_dir,
        )
        self.tools = tools  # Dict of tool_name -> callable
        self.tool_descriptions = tool_descriptions or {}
        self.memory = memory
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.run_dir = run_dir

    def execute_task(self, user_request: str) -> str:
        """Main entry point - execute a task autonomously."""

        # PERCEPTION: Understand the task and search for solutions
        context = self._perceive(user_request)

        # Store goal in memory
        self.memory.store("current_goal", user_request)

        # Track execution
        trajectory: List[Step] = []
        failures = 0

        for step_idx in range(1, self.max_steps + 1):
            thought, action, action_input = self._decide_next_step(
                user_request, context, trajectory
            )
            print(f"\n[STEP {step_idx}] {action}")
            print(f"[THOUGHT] {thought}")
            print(f"[ACTION] {action}({action_input})")

            observation, success = self._execute_action(action, action_input)
            print(f"[OBSERVATION] {observation[:200]}...")

            reflection = self._reflect_on_step(thought, action, observation, success)
            print(f"[REFLECTION] {reflection}")

            trajectory.append(
                Step(
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=observation,
                    reflection=reflection,
                    success=success,
                )
            )

            if self._is_task_complete(trajectory):
                print("[SUCCESS] Task completed!")
                self._store_success(user_request, trajectory)
                return observation

            if not success:
                failures += 1
                should_retry, adjusted_context = self._reflect_on_failure(
                    user_request, trajectory, failures
                )
                if adjusted_context:
                    context.update(adjusted_context)
                if not should_retry or failures >= self.max_retries:
                    print("[FAILED] Task failed after reflection analysis")
                    self._store_failure(user_request, trajectory)
                    return (
                        f"Unable to complete task after {failures} failures. "
                        f"Last error: {observation}"
                    )

        return f"Task failed after {self.max_steps} steps"

    def _perceive(self, user_request: str) -> Dict[str, Any]:
        """Perception phase: understand task and gather context."""

        # Check if we've done similar tasks before
        similar_tasks = self.memory.retrieve_similar(user_request, k=1)
        summarized_tasks: List[Dict[str, Any]] = []
        for task in similar_tasks:
            if not isinstance(task, dict):
                continue
            key = task.get("key")
            content = task.get("content")
            if isinstance(content, str) and len(content) > 240:
                content = content[:240] + "..."
            summarized_tasks.append({"key": key, "content": content})

        # Web search for solution approaches (if not in memory)
        search_results = None
        if not similar_tasks:
            if "web_search" in self.tools:
                query = f"how to {user_request} step by step"
                try:
                    search_results = self.tools["web_search"](query=query)
                except Exception as exc:
                    search_results = {"error": str(exc)}

        return {
            "user_request": user_request,
            "similar_tasks": summarized_tasks,
            "search_results": self._normalize_observation(search_results),
        }

    def _decide_next_step(
        self, goal: str, context: Dict[str, Any], trajectory: List[Step]
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Decide the single next action to take."""

        relevant_tools = self._get_relevant_tools(goal)
        tool_names = list(relevant_tools.keys())

        prompt = f"""You are an autonomous agent. Decide the ONE next action that moves the goal forward.

GOAL: {goal}

AVAILABLE TOOLS:
{self._format_tools(tool_names)}

CONTEXT:
{json.dumps(context, indent=2)}

RECENT TRAJECTORY:
{self._format_trajectory(trajectory[-3:])}

Return JSON with:
1. thought: your reasoning
2. action: which tool to use next
3. action_input: arguments to pass

If the task is already complete, set action to "finish" and include a brief summary in action_input.
"""

        print("[REACT] Prompt length:", len(prompt))
        print("[REACT] Tools listed:", len(tool_names))
        print("[REACT] Prompt:\n" + prompt)

        response = self.llm_quick.chat_simple(prompt, timeout_seconds=15)
        if not response:
            return self._fallback_action("decide_next_step", "timeout or empty response")
        if not isinstance(response, dict):
            return self._fallback_action("decide_next_step", "invalid response")
        thought, action, action_input = self._parse_action_decision(response)
        if not action or action not in self.tools:
            return self._fallback_action("decide_next_step", "missing action")
        return thought, action, action_input

    def _execute_action(self, action: str, action_input: Dict[str, Any]) -> Tuple[str, bool]:
        """Execute the chosen action and return observation."""

        if action not in self.tools:
            return f"Error: Tool '{action}' not available", False

        try:
            result = self.tools[action](**(action_input or {}))
        except Exception as exc:
            return f"Error executing {action}: {exc}", False

        return self._normalize_tool_result(result)

    def _reflect_on_step(self, thought: str, action: str, observation: str, success: bool) -> str:
        """Reflect on whether this step was good."""

        prompt = f"""Analyze this execution step:

THOUGHT: {thought}
ACTION: {action}
OBSERVATION: {observation[:500]}
SUCCESS: {success}

Provide a brief critique. Return JSON with:
- reflection: what worked/didn't
- critical: true if this failure blocks progress
- next: recommended next move
"""

        response = self._call_llm_json(prompt, timeout_seconds=20, llm=self.llm_quick)
        if not isinstance(response, dict):
            response = {"reflection": "No reflection", "critical": False, "next": ""}
        reflection = response.get("reflection", "No reflection")
        critical = bool(response.get("critical"))
        next_hint = response.get("next", "")
        if critical and "critical" not in reflection.lower():
            reflection = f"[CRITICAL] {reflection}"
        if next_hint:
            reflection = f"{reflection} Next: {next_hint}"
        return reflection

    def _reflect_on_failure(
        self, goal: str, trajectory: List[Step], attempt: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Deep reflection on why the attempt failed."""

        prompt = f"""Analyze why this attempt failed:

GOAL: {goal}
ATTEMPT: {attempt}

FULL TRAJECTORY:
{self._format_trajectory(trajectory)}

Determine:
1. Root cause of failure
2. Should we retry with a different approach?
3. If yes, what should change in the next attempt?
"""

        response = self._call_llm_json(prompt, timeout_seconds=30, llm=self.llm_reason)
        if not isinstance(response, dict):
            return False, {"error": "invalid reflection response"}
        should_retry = bool(response.get("should_retry"))
        adjusted_context = response.get("adjusted_approach", {}) or {}
        return should_retry, adjusted_context

    def _is_task_complete(self, trajectory: List[Step]) -> bool:
        """Check if the task is complete based on trajectory."""

        if not trajectory:
            return False

        last_step = trajectory[-1]
        if last_step.success and (
            "complete" in last_step.reflection.lower() or last_step.action == "finish"
        ):
            return True

        return False

    def _store_success(self, task: str, trajectory: List[Step]) -> None:
        """Store successful pattern in memory."""

        self.memory.store(
            f"success_{task}",
            {
                "task": task,
                "trajectory": [
                    {"action": s.action, "input": s.action_input} for s in trajectory
                ],
            },
        )

    def _store_failure(self, task: str, trajectory: List[Step]) -> None:
        """Store failure pattern in memory."""

        self.memory.store(
            f"failure_{task}",
            {
                "task": task,
                "error": trajectory[-1].observation if trajectory else "Unknown",
            },
        )

    def _format_tools(self, tool_names: Optional[List[str]] = None) -> str:
        lines = []
        names = tool_names if tool_names is not None else list(self.tools.keys())
        for name in sorted(names):
            desc = self.tool_descriptions.get(name, "")
            if desc:
                lines.append(f"- {name}: {desc}")
            else:
                lines.append(f"- {name}")
        return "\n".join(lines)

    def _get_relevant_tools(self, user_request: str) -> Dict[str, Any]:
        """Return only tools relevant to this request."""

        core_tools = ["web_search", "web_fetch", "read_file", "write_file", "finish"]
        lowered = (user_request or "").lower()
        if "calendar" in lowered:
            core_tools.extend(["create_calendar_event", "list_calendar_events"])
        if "task" in lowered:
            core_tools.extend(["create_task", "list_all_tasks"])
        if "email" in lowered or "mail" in lowered:
            core_tools.append("mail")
        return {k: v for k, v in self.tools.items() if k in core_tools}

    def _format_trajectory(self, trajectory: List[Step]) -> str:
        if not trajectory:
            return "(none)"
        return "\n".join(
            f"{i+1}. {s.action}: {s.observation[:100]}" for i, s in enumerate(trajectory)
        )

    def _parse_action_decision(self, response: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        if not isinstance(response, dict):
            return "", "", {}
        action_input = response.get("action_input", {}) or {}
        if isinstance(action_input, list):
            converted: Dict[str, Any] = {}
            for item in action_input:
                if not isinstance(item, dict):
                    continue
                key = item.get("key")
                value = item.get("value")
                if isinstance(key, str) and key:
                    converted[key] = value
            action_input = converted
        if not isinstance(action_input, dict):
            action_input = {}
        return (
            response.get("thought", ""),
            response.get("action", ""),
            action_input,
        )

    def _fallback_action(self, step_desc: str, error: str) -> Tuple[str, str, Dict[str, Any]]:
        thought = f"Fallback due to action selection error: {error}"
        if "scan_repo" in self.tools:
            return thought, "scan_repo", {"path": "."}
        if "list_dir" in self.tools:
            return thought, "list_dir", {"path": "."}
        if "file_read" in self.tools:
            return thought, "file_read", {"path": "README.md"}
        if self.tools:
            first = sorted(self.tools.keys())[0]
            return thought, first, {}
        return thought, "", {}

    def _call_llm_json(self, prompt: str, timeout_seconds: int, *, llm: CodexCliClient) -> Any:
        result = llm.call_codex(prompt, timeout_seconds=timeout_seconds)
        if not isinstance(result, dict):
            return {"_raw": str(result)}
        if "error" in result:
            return {"_error": result.get("error"), "_raw": result}
        raw = result.get("result") or ""
        parsed = self._try_parse_json(raw)
        if parsed is None:
            return {"_raw": raw}
        return parsed

    def _try_parse_json(self, raw: str) -> Optional[Any]:
        if not raw or not isinstance(raw, str):
            return None
        try:
            return json.loads(raw)
        except Exception:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                return json.loads(raw[start : end + 1])
            except Exception:
                return None

    def _normalize_observation(self, data: Any) -> Any:
        if data is None:
            return None
        if isinstance(data, str):
            return data
        try:
            return json.loads(json.dumps(data, default=str))
        except Exception:
            return str(data)

    def _normalize_tool_result(self, result: Any) -> Tuple[str, bool]:
        if result is None:
            return "No output", True
        if isinstance(result, dict) and "success" in result:
            success = bool(result.get("success"))
            output = result.get("output") or result.get("error") or result
            return self._stringify_output(output), success
        if hasattr(result, "success"):
            success = bool(getattr(result, "success"))
            output = getattr(result, "output", None)
            error = getattr(result, "error", None)
            return self._stringify_output(output or error or result), success
        return self._stringify_output(result), True

    def _stringify_output(self, output: Any) -> str:
        if output is None:
            return ""
        if isinstance(output, str):
            return output
        try:
            return json.dumps(output, ensure_ascii=False)
        except Exception:
            return str(output)


__all__ = ["ReActAgent", "Step"]
