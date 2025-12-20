from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from agent.codex_client import CodexTaskClient
from agent.llm import schemas as llm_schemas


class _StubLLM:
    def __init__(self):
        self.calls: List[Path] = []

    def complete_json(self, prompt: str, *, schema_path: Path, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:  # noqa: ARG002
        self.calls.append(schema_path)
        name = schema_path.name
        if name == llm_schemas.YAML_PLAN.name:
            return {"yaml": "id: stub\nname: stub\ntype: shell\ngoal: stub\ndefinition_of_done: ok\nstop_rules: {max_attempts: 1, max_minutes: 1, max_tool_calls: 1}\non_fail: abort\ncommand: exit 0\n"}
        if name == llm_schemas.FAILURE_ANALYSIS.name:
            return {
                "root_cause": "stub",
                "explanation_short": "stub",
                "suggested_tool_or_step_changes": ["stub"],
                "stop_condition_if_applicable": None,
            }
        if name == llm_schemas.PATTERN_EXTRACTION.name:
            return {"patterns": ["p1"], "procedures": ["proc1"]}
        if name == llm_schemas.CODE_REVIEW.name:
            return {"improved_code": "x", "changes": ["c"], "explanation": "e"}
        if name == llm_schemas.RESEARCH_SUMMARY.name:
            return {"summary_md": "s", "key_findings": ["k"], "citations": [{"url": "u", "title": "t"}]}
        raise AssertionError(f"Unexpected schema: {schema_path}")


def test_codex_task_client_uses_expected_schemas(tmp_path: Path):
    prompt_path = tmp_path / "planner_system_prompt.txt"
    prompt_path.write_text("SYSTEM PROMPT STUB", encoding="utf-8")

    llm = _StubLLM()
    client = CodexTaskClient(llm=llm, planner_system_prompt_path=prompt_path)

    _ = client.generate_yaml_plan("goal")
    _ = client.analyze_failure(goal="g", task_yaml="id: x", error="err")
    _ = client.extract_patterns(trajectories=[{"ok": True}])
    _ = client.review_code(code="print('x')")
    _ = client.summarize_research(sources=[{"url": "u", "title": "t", "content": "c"}])

    assert [p.name for p in llm.calls] == [
        llm_schemas.YAML_PLAN.name,
        llm_schemas.FAILURE_ANALYSIS.name,
        llm_schemas.PATTERN_EXTRACTION.name,
        llm_schemas.CODE_REVIEW.name,
        llm_schemas.RESEARCH_SUMMARY.name,
    ]

