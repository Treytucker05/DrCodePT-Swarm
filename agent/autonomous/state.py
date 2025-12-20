from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import Observation, Plan, Reflection, Step, ToolResult


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
