from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agent.llm.base import LLMClient
from agent.llm import schemas as llm_schemas


class ResearcherOutput(BaseModel):
    findings: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    recommended_steps: List[str] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)


class PlanStep(BaseModel):
    id: str
    description: str
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)
    success_check: str = ""
    fallback: str = ""


class PlannerOutput(BaseModel):
    next_steps: List[PlanStep] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)


class CriticOutput(BaseModel):
    decision: str
    rationale: str
    suggested_changes: List[str] = Field(default_factory=list)


def _write_schema(schema: Dict[str, Any]) -> Path:
    path = Path(tempfile.gettempdir()) / f"team_schema_{uuid.uuid4().hex}.json"
    path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    return path


def _run_llm_json(llm: LLMClient, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    schema_path = _write_schema(schema)
    try:
        return llm.reason_json(prompt, schema_path=schema_path, timeout_seconds=60)
    except Exception as exc:
        try:
            setattr(exc, "prompt_length", len(prompt))
            setattr(exc, "schema_path", str(schema_path))
        except Exception:
            pass
        raise
    finally:
        try:
            schema_path.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass


def _compact_planner_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "next_steps": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string"},
                        "description": {"type": "string"},
                        "tool": {"type": "string"},
                        "args": {"type": "object"},
                    },
                    "required": ["id", "description", "tool", "args"],
                },
            },
            "questions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["next_steps", "questions"],
    }


def run_researcher(
    llm: LLMClient,
    *,
    objective: str,
    context: str,
    unknowns: Optional[List[str]] = None,
) -> ResearcherOutput:
    prompt = (
        "You are Researcher. Identify key facts, assumptions, and citations.\n"
        "Return JSON only with findings, sources, recommended_steps, caveats.\n"
        f"Objective: {objective}\n"
        f"Context: {context}\n"
        f"Unknowns: {json.dumps(unknowns or [])}\n"
    )
    schema = ResearcherOutput.model_json_schema()
    data = _run_llm_json(llm, prompt, schema)
    return ResearcherOutput.model_validate(data)


def run_planner(
    llm: LLMClient,
    *,
    objective: str,
    context: str,
    tools: List[Dict[str, Any]],
    reflexions: Optional[List[str]] = None,
) -> PlannerOutput:
    lessons = "\n".join(reflexions or [])
    prompt = (
        "You are Planner. Produce 1-3 actionable next steps (max 3).\n"
        "If you need missing info, return questions instead of steps.\n"
        "Use tool names provided; args must be a JSON object.\n"
        "Keep tool usage minimal and safe.\n"
        "Previous failures & lessons:\n"
        f"{lessons if lessons else '(none)'}\n"
        f"Objective: {objective}\n"
        f"Context: {context}\n"
        f"Tools: {json.dumps(tools)}\n"
        "Return JSON: {next_steps:[{id, description, tool, args, success_check, fallback}], questions:[...]}\n"
    )
    schema = PlannerOutput.model_json_schema()
    try:
        data = _run_llm_json(llm, prompt, schema)
        return PlannerOutput.model_validate(data)
    except Exception:
        compact_prompt = (
            "Planner: Provide up to 3 next steps OR questions.\n"
            f"Objective: {objective}\n"
            f"Context: {context[:1200]}\n"
            f"Tools: {[t.get('name') for t in tools][:30]}\n"
            "Return JSON with next_steps and questions."
        )
        data = _run_llm_json(llm, compact_prompt, _compact_planner_schema())
        return PlannerOutput.model_validate(data)


def run_planner_fallback_text(llm: LLMClient, prompt: str) -> PlannerOutput:
    text = ""
    try:
        data = llm.reason_json(prompt, schema_path=llm_schemas.CHAT_RESPONSE, timeout_seconds=60)
        if isinstance(data, dict):
            text = str(data.get("response") or "")
    except Exception:
        text = ""
    note = text.strip() or "Planner JSON failed. Ask user to retry or reduce the task."
    return PlannerOutput(
        next_steps=[
            PlanStep(
                id="ask_user",
                description="Ask user to retry or reduce the task",
                tool="human_ask",
                args={"question": note},
                success_check="",
                fallback=note,
            )
        ],
        questions=[],
    )


def run_critic(
    llm: LLMClient,
    *,
    objective: str,
    context: str,
    error: str,
    last_step: Optional[Dict[str, Any]] = None,
) -> CriticOutput:
    prompt = (
        "You are Critic. Decide next action: continue|retry|research|ask_user|pivot|abort.\n"
        "Return JSON only with decision, rationale, suggested_changes.\n"
        f"Objective: {objective}\n"
        f"Context: {context}\n"
        f"Error: {error}\n"
        f"LastStep: {json.dumps(last_step or {})}\n"
    )
    schema = CriticOutput.model_json_schema()
    data = _run_llm_json(llm, prompt, schema)
    return CriticOutput.model_validate(data)
