from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agent.llm.backend import LLMBackend, RunConfig
from agent.llm import schemas as llm_schemas


@dataclass
class ClarifyResult:
    ready_to_run: bool
    normalized_objective: str
    task_type: str
    search_terms: List[str]
    glob_patterns: List[str]
    candidate_roots: List[str]
    blocking_questions: List[Dict[str, Any]]
    assumptions_if_no_answer: List[str]
    expected_output: str


def _fallback_clarify(objective: str) -> ClarifyResult:
    return ClarifyResult(
        ready_to_run=False,
        normalized_objective=objective.strip() or "Clarify objective",
        task_type="other",
        search_terms=[],
        glob_patterns=[],
        candidate_roots=[],
        blocking_questions=[
            {
                "id": "clarify",
                "question": "What is the exact outcome you want from this swarm run?",
                "why": "Need a clear target before spawning workers.",
                "default": None,
            }
        ],
        assumptions_if_no_answer=["Proceed with a high-level repo review using preflight repo_map."],
        expected_output="A concise, actionable response.",
    )


def _normalize_list(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(v) for v in val if isinstance(v, (str, int, float))]
    return []


def _normalize_questions(val: Any) -> List[Dict[str, Any]]:
    if not isinstance(val, list):
        return []
    out = []
    for entry in val:
        if not isinstance(entry, dict):
            continue
        out.append(
            {
                "id": str(entry.get("id") or ""),
                "question": str(entry.get("question") or ""),
                "why": str(entry.get("why") or ""),
                "default": entry.get("default"),
            }
        )
    return out


def parse_clarify(data: Dict[str, Any], *, objective: str) -> ClarifyResult:
    try:
        return ClarifyResult(
            ready_to_run=bool(data.get("ready_to_run")),
            normalized_objective=str(data.get("normalized_objective") or objective).strip() or objective,
            task_type=str(data.get("task_type") or "other"),
            search_terms=_normalize_list(data.get("search_terms")),
            glob_patterns=_normalize_list(data.get("glob_patterns")),
            candidate_roots=_normalize_list(data.get("candidate_roots")),
            blocking_questions=_normalize_questions(data.get("blocking_questions")),
            assumptions_if_no_answer=_normalize_list(data.get("assumptions_if_no_answer")),
            expected_output=str(data.get("expected_output") or ""),
        )
    except Exception:
        return _fallback_clarify(objective)


def run_clarifier(
    backend: LLMBackend,
    *,
    objective: str,
    root_listing: List[Dict[str, Any]],
    repo_map: List[Dict[str, Any]],
    run_dir,
    workdir,
    timeout_seconds: Optional[int] = None,
) -> ClarifyResult:
    prompt = f"""You are preparing a swarm run. Use the objective and preflight repo map to normalize the task.
Return ONLY JSON matching the schema.

Objective:
{objective}

Root listing (top-level):
{json.dumps(root_listing, ensure_ascii=False)}

Repo map (top files):
{json.dumps(repo_map, ensure_ascii=False)}
"""
    result = backend.run(
        prompt=prompt,
        workdir=workdir,
        run_dir=run_dir,
        config=RunConfig(schema_path=llm_schemas.CLARIFY, profile="reason", timeout_seconds=timeout_seconds),
    )
    if not isinstance(result.data, dict):
        return _fallback_clarify(objective)
    return parse_clarify(result.data, objective=objective)
