from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import Observation, Plan, Reflection, Step, ToolResult
from .pydantic_compat import model_dump, model_validate


def _sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8", errors="replace")).hexdigest()


@dataclass
class AgentState:
    task: str
    rolling_summary: str = ""
    observations: List[Observation] = field(default_factory=list)
    current_plan: Optional[Plan] = None
    current_step_idx: int = 0
    last_action_signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "rolling_summary": self.rolling_summary,
            "observations": [model_dump(o) for o in self.observations],
            "current_plan": model_dump(self.current_plan) if self.current_plan else None,
            "current_step_idx": self.current_step_idx,
            "last_action_signature": self.last_action_signature,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AgentState":
        task = str(data.get("task") or "")
        state = AgentState(task=task)
        state.rolling_summary = str(data.get("rolling_summary") or "")
        obs = data.get("observations") or []
        if isinstance(obs, list):
            for o in obs:
                try:
                    state.observations.append(model_validate(Observation, o))
                except Exception:
                    pass
        plan = data.get("current_plan")
        if isinstance(plan, dict):
            try:
                state.current_plan = model_validate(Plan, plan)
            except Exception:
                state.current_plan = None
        state.current_step_idx = int(data.get("current_step_idx") or 0)
        state.last_action_signature = data.get("last_action_signature")
        return state

    def add_observation(self, obs: Observation) -> None:
        self.observations.append(obs)

    def compact(self, *, keep_last: int = 12, max_total: int = 40) -> None:
        if len(self.observations) <= max_total:
            return
        old = self.observations[:-keep_last]
        keep = self.observations[-keep_last:]
        facts: List[str] = []
        for o in old:
            facts.extend(o.salient_facts[:2] or [])
        summary = "\n".join(facts[-200:])  # cap
        if summary:
            self.rolling_summary = (self.rolling_summary + "\n" + summary).strip()
            self.rolling_summary = self.rolling_summary[-8000:]
        self.observations = keep

    def state_fingerprint(self) -> str:
        last_obs = self.observations[-1] if self.observations else None
        last_obs_sig = None
        if last_obs is not None:
            last_obs_sig = {
                "source": last_obs.source,
                "errors": last_obs.errors,
                "salient_facts": last_obs.salient_facts,
                "parsed": last_obs.parsed,
            }
        payload: Dict[str, Any] = {
            "summary_tail": self.rolling_summary[-800:],
            "last_obs": last_obs_sig,
        }
        return _sha256_json(payload)
