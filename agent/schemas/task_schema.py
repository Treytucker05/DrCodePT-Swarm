from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    composite = "composite"
    shell = "shell"
    browser = "browser"
    python = "python"
    fs = "fs"
    api = "api"
    desktop = "desktop"
    vision = "vision"
    screen_recorder = "screen_recorder"
    notify = "notify"
    code_review = "code_review"
    research = "research"


class OnFailAction(str, Enum):
    retry = "retry"
    escalate = "escalate"
    abort = "abort"


class StopRules(BaseModel):
    max_attempts: int = Field(default=1, ge=1)
    max_minutes: int = Field(default=5, ge=1)
    max_tool_calls: int = Field(default=10, ge=1)


class VerifierSpec(BaseModel):
    id: str
    args: Dict[str, Any] = Field(default_factory=dict)


class TaskDefinition(BaseModel):
    # Required fields
    id: str
    name: str
    type: TaskType
    goal: str
    definition_of_done: str
    stop_rules: StopRules
    on_fail: OnFailAction

    # Optional common fields
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    verify: List[VerifierSpec] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=list)
    tools_allowed: List[str] = Field(default_factory=list)
    requires_human: bool = False

    # Type-specific fields
    steps: List["TaskDefinition"] = Field(default_factory=list)

    command: str = ""
    timeout_seconds: Optional[int] = None

    url: str = ""
    login_site: str = ""
    session_state_path: str = ""
    headless: Optional[bool] = None

    script: str = ""

    path: str = ""
    content: str = ""
    mode: str = ""  # e.g., overwrite|append|read

    endpoint: str = ""
    method: str = "GET"
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    body: Any = None

    def as_json(self) -> str:
        if hasattr(self, "model_dump_json"):
            return self.model_dump_json(indent=2)  # type: ignore[attr-defined]
        return json.dumps(self.dict(), indent=2)  # type: ignore[call-arg]


TaskDefinition.model_rebuild()


def load_task_from_yaml(path: str) -> TaskDefinition:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Task YAML must be a mapping/object")
    return TaskDefinition(**data)


# Backwards-compatible alias used by some legacy code.
Task = TaskDefinition


__all__ = [
    "TaskType",
    "OnFailAction",
    "StopRules",
    "VerifierSpec",
    "TaskDefinition",
    "Task",
    "load_task_from_yaml",
]

