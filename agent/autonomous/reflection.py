from __future__ import annotations

import textwrap
from typing import Any, Optional

from agent.llm.base import LLMClient
from agent.llm import schemas as llm_schemas

from .jsonio import dumps_compact
from .models import Observation, Reflection, Step, ToolResult
from .pydantic_compat import model_validate


class Reflector:
    def __init__(self, *, llm: Optional[LLMClient] = None, pre_mortem_enabled: bool = False):
        self._llm = llm
        self._pre_mortem_enabled = pre_mortem_enabled

    def pre_mortem(self, *, task: str, step: Step, observation: Observation) -> Optional[dict]:
        if not self._llm or not self._pre_mortem_enabled:
            return None
        prompt = textwrap.dedent(
            f"""
            Task: {task}
            Upcoming step:
            {dumps_compact(step.model_dump() if hasattr(step, "model_dump") else step.dict())}

            Latest observation:
            {dumps_compact(observation.model_dump() if hasattr(observation, "model_dump") else observation.dict())}

            Return STRICT JSON:
              {{
                "likely_failure_modes": ["..."],
                "safer_alternative": {{"tool_name":"...", "tool_args":{{...}}, "why":"..."}}
              }}
            Return JSON only.
            """
        ).strip()
        try:
            return self._llm.complete_json(prompt, schema_path=llm_schemas.PREMORTEM)
        except Exception:
            # Don't block execution on pre-mortem failures.
            return None

    def reflect(
        self,
        *,
        task: str,
        step: Step,
        tool_result: ToolResult,
        observation: Observation,
    ) -> Reflection:
        if not self._llm:
            if tool_result.success:
                return Reflection(status="success", explanation_short="Tool succeeded.", next_hint="")
            return Reflection(status="replan", explanation_short="Tool failed.", next_hint=tool_result.error or "")

        payload = {
            "step": step.model_dump() if hasattr(step, "model_dump") else step.dict(),
            "tool_result": tool_result.model_dump() if hasattr(tool_result, "model_dump") else tool_result.dict(),
            "observation": observation.model_dump() if hasattr(observation, "model_dump") else observation.dict(),
        }
        prompt = textwrap.dedent(
            f"""
            Task: {task}

            Classify the outcome of the last action using evidence.

            Evidence:
            {dumps_compact(payload)}

            Return STRICT JSON:
              {{"status":"success|minor_repair|replan","explanation_short":"...","next_hint":"..."}}
            Return JSON only.
            """
        ).strip()
        try:
            data = self._llm.complete_json(prompt, schema_path=llm_schemas.REFLECTION)
            return model_validate(Reflection, data)
        except Exception:
            if tool_result.success:
                return Reflection(status="success", explanation_short="Tool succeeded.", next_hint="")
            return Reflection(status="replan", explanation_short="Tool failed.", next_hint=tool_result.error or "")
