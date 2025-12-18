from __future__ import annotations

"""
Pydantic task schema for DrCodePT Agent.
Supports task types: browser | shell | python | fs | api | composite | desktop | screen_recorder | vision | notify | code_review | research.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, root_validator, validator


class TaskType(str, Enum):
    browser = "browser"
    shell = "shell"
    python = "python"
    fs = "fs"
    api = "api"
    composite = "composite"
    desktop = "desktop"
    screen_recorder = "screen_recorder"
    vision = "vision"
    notify = "notify"
    code_review = "code_review"
    research = "research"


class OnFailAction(str, Enum):
    retry = "retry"
    escalate = "escalate"
    abort = "abort"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class VerifyConfig(BaseModel):
    id: str = Field(..., description="Verifier name")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the verifier")

    class Config:
        extra = "forbid"


class StopRules(BaseModel):
    max_attempts: int = Field(..., gt=0)
    max_minutes: int = Field(..., gt=0)
    max_tool_calls: int = Field(..., gt=0)

    class Config:
        extra = "forbid"


class TaskDefinition(BaseModel):
    # Required
    id: str
    name: str
    type: TaskType
    goal: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    definition_of_done: str
    verify: List[VerifyConfig] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=list)
    tools_allowed: List[str] = Field(default_factory=list)
    stop_rules: StopRules
    on_fail: OnFailAction

    # Optional / type-specific
    url: Optional[str] = None
    login_site: Optional[str] = None
    command: Optional[str] = None
    script: Optional[str] = None
    path: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[HttpMethod] = None
    steps: Optional[List["TaskDefinition"]] = None
    timeout_seconds: Optional[int] = Field(default=None, gt=0)
    requires_human: Optional[bool] = False
    session_state_path: Optional[str] = None

    class Config:
        extra = "forbid"

    @validator("allowed_paths", "tools_allowed", pre=True)
    def ensure_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v

    @root_validator(skip_on_failure=True)
    def validate_type_specific_fields(cls, values):
        t_type: TaskType = values.get("type")
        command = values.get("command")
        url = values.get("url")
        endpoint = values.get("endpoint")
        method = values.get("method")
        steps = values.get("steps")
        inputs = values.get("inputs") or {}
        login_site = values.get("login_site")

        if t_type == TaskType.shell and not command:
            raise ValueError("Shell tasks require a 'command'.")
        if t_type == TaskType.browser and not (url or inputs.get("steps") or login_site):
            raise ValueError("Browser tasks require a 'url', inputs.steps, or login_site.")
        if t_type == TaskType.api:
            if not endpoint:
                raise ValueError("API tasks require an 'endpoint'.")
            if not method:
                raise ValueError("API tasks require an HTTP 'method'.")
        if t_type == TaskType.composite:
            if not steps or len(steps) == 0:
                raise ValueError("Composite tasks require a non-empty 'steps' list.")
        else:
            if steps:
                raise ValueError("'steps' is only allowed for composite tasks.")

        tools_allowed = values.get("tools_allowed") or []
        if t_type and tools_allowed and t_type.value not in tools_allowed:
            # Encourage explicit permission for the primary tool
            raise ValueError(f"Primary tool '{t_type.value}' must be included in tools_allowed.")

        return values


def load_task_from_yaml(path: str) -> TaskDefinition:
    """
    Load a task YAML file and validate it against the TaskDefinition schema.
    """
    task_path = Path(path)
    if not task_path.is_file():
        raise FileNotFoundError(f"Task file not found: {path}")

    with task_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return TaskDefinition.parse_obj(data)


# Enable recursive TaskDefinition references
TaskDefinition.update_forward_refs()

__all__ = [
    "TaskType",
    "OnFailAction",
    "HttpMethod",
    "VerifyConfig",
    "StopRules",
    "TaskDefinition",
    "Task",
    "load_task_from_yaml",
]

# For compatibility with usage examples expecting Task
Task = TaskDefinition
