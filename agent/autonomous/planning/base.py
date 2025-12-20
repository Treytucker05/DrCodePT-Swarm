from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models import Observation, Plan, Reflection, Step, ToolResult


class Planner(ABC):
    @abstractmethod
    def plan(self, *, task: str, observations: List[Observation], memories: List[dict]) -> Plan:
        raise NotImplementedError

    def repair(
        self,
        *,
        task: str,
        observations: List[Observation],
        memories: List[dict],
        failed_step: Step,
        tool_result: ToolResult,
        reflection: Reflection,
    ) -> Optional[Plan]:
        # Default: full replan.
        return None
