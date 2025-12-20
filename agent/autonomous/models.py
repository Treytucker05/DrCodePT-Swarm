from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Observation(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    source: str
    raw: Any = None
    parsed: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    salient_facts: List[str] = Field(default_factory=list)


class Step(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    goal: str
    rationale_short: str = ""
    tool_name: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    success_criteria: List[str] = Field(default_factory=list)


class Plan(BaseModel):
    goal: str
    steps: List[Step] = Field(default_factory=list)


ReflectionStatus = Literal["success", "minor_repair", "replan"]


class Reflection(BaseModel):
    status: ReflectionStatus
    explanation_short: str = ""
    next_hint: str = ""


class ToolResult(BaseModel):
    success: bool
    output: Any = None
    error: Optional[str] = None
    retryable: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRunResult(BaseModel):
    success: bool
    stop_reason: str
    steps_executed: int
    run_id: str
    trace_path: Optional[str] = None
