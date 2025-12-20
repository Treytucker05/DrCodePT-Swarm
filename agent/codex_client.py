from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.llm import (
    CodexCliAuthError,
    CodexCliClient,
    CodexCliExecutionError,
    CodexCliNotFoundError,
    CodexCliOutputError,
    schemas as llm_schemas,
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class CodexTaskClient:
    """
    High-level, structured helper around Codex CLI inference for legacy workflows:
    - YAML plan generation
    - failure analysis
    - pattern extraction
    - code review
    - research summarization
    """

    llm: CodexCliClient
    planner_system_prompt_path: Path
    max_retries: int = 2
    retry_backoff_seconds: float = 1.0

    @staticmethod
    def from_env(*, planner_system_prompt_path: Optional[Path] = None) -> "CodexTaskClient":
        root = Path(__file__).resolve().parent
        return CodexTaskClient(
            llm=CodexCliClient.from_env(),
            planner_system_prompt_path=planner_system_prompt_path
            or (root / "planner_system_prompt.txt").resolve(),
        )

    def _call_json(self, prompt: str, *, schema_path: Path, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                data = self.llm.reason_json(prompt, schema_path=schema_path, timeout_seconds=timeout_seconds)
                if not isinstance(data, dict):
                    raise CodexCliOutputError(f"Expected JSON object, got: {type(data).__name__}")
                return data
            except (CodexCliNotFoundError, CodexCliAuthError):
                raise
            except (CodexCliExecutionError, CodexCliOutputError) as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    raise
                time.sleep(self.retry_backoff_seconds * (2**attempt))
        raise CodexCliExecutionError("CodexTaskClient failed unexpectedly") from last_exc

    def generate_yaml_plan(
        self,
        goal: str,
        *,
        context: str = "",
        previous_yaml: str = "",
        failure_analysis: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        system_prompt = _read_text(self.planner_system_prompt_path)
        prompt = (
            "Output ONLY JSON that conforms to the provided schema. No prose.\n"
            "You are generating a YAML task plan that conforms to TaskDefinition.\n\n"
            f"SYSTEM_PROMPT:\n{system_prompt}\n\n"
            f"GOAL:\n{goal}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"PREVIOUS_YAML:\n{previous_yaml}\n\n"
            f"FAILURE_ANALYSIS_JSON:\n{json.dumps(failure_analysis or {}, ensure_ascii=False)}\n"
        )
        return self._call_json(prompt, schema_path=llm_schemas.YAML_PLAN, timeout_seconds=timeout_seconds)

    def analyze_failure(
        self,
        *,
        goal: str,
        task_yaml: str,
        error: str,
        recent_events: Optional[List[Dict[str, Any]]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        prompt = (
            "Output ONLY JSON that conforms to the provided schema. No prose.\n"
            "You are analyzing why a task failed and proposing concrete fixes.\n"
            "Be specific and actionable (selectors, timeouts, tool swaps, verifier changes).\n\n"
            f"GOAL:\n{goal}\n\n"
            f"FAILED_TASK_YAML:\n{task_yaml}\n\n"
            f"ERROR:\n{error}\n\n"
            f"RECENT_EVENTS_JSON:\n{json.dumps(recent_events or [], ensure_ascii=False)[:12000]}\n"
        )
        return self._call_json(prompt, schema_path=llm_schemas.FAILURE_ANALYSIS, timeout_seconds=timeout_seconds)

    def extract_patterns(
        self,
        *,
        trajectories: List[Dict[str, Any]],
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        prompt = (
            "Output ONLY JSON that conforms to the provided schema. No prose.\n"
            "Extract reusable patterns and procedures from the following successful/failed trajectories.\n\n"
            f"TRAJECTORIES_JSON:\n{json.dumps(trajectories, ensure_ascii=False)[:12000]}\n"
        )
        return self._call_json(prompt, schema_path=llm_schemas.PATTERN_EXTRACTION, timeout_seconds=timeout_seconds)

    def review_code(self, *, code: str, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        prompt = (
            "Output ONLY JSON that conforms to the provided schema. No prose.\n"
            "You are a senior code reviewer.\n\n"
            f"CODE:\n{code}\n"
        )
        return self._call_json(prompt, schema_path=llm_schemas.CODE_REVIEW, timeout_seconds=timeout_seconds)

    def summarize_research(
        self,
        *,
        sources: List[Dict[str, Any]],
        question: str = "",
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        prompt = (
            "Output ONLY JSON that conforms to the provided schema. No prose.\n"
            "Summarize the sources into a concise Markdown report with key findings and citations.\n\n"
            f"QUESTION:\n{question}\n\n"
            f"SOURCES_JSON:\n{json.dumps(sources, ensure_ascii=False)[:12000]}\n"
        )
        return self._call_json(prompt, schema_path=llm_schemas.RESEARCH_SUMMARY, timeout_seconds=timeout_seconds)


__all__ = ["CodexTaskClient"]
