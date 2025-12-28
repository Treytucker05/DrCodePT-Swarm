from __future__ import annotations

from pathlib import Path


SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"

PLAN_NEXT_STEP = SCHEMAS_DIR / "plan_next_step.schema.json"
PLAN = SCHEMAS_DIR / "plan.schema.json"
PLAN_CANDIDATES = SCHEMAS_DIR / "plan_candidates.schema.json"
REACT_PLAN = SCHEMAS_DIR / "react_plan.schema.json"
REACT_ACTION = SCHEMAS_DIR / "react_action.schema.json"
REACT_REFLECTION = SCHEMAS_DIR / "react_reflection.schema.json"
REACT_FAILURE = SCHEMAS_DIR / "react_failure.schema.json"
REFLECTION = SCHEMAS_DIR / "reflection.schema.json"
PREMORTEM = SCHEMAS_DIR / "premortem.schema.json"
COMPACTION = SCHEMAS_DIR / "compaction.schema.json"
CONDITION_CHECK = SCHEMAS_DIR / "condition_check.schema.json"
TASK_DECOMPOSITION = SCHEMAS_DIR / "task_decomposition.schema.json"
CODE_REVIEW = SCHEMAS_DIR / "code_review.schema.json"
RESEARCH_SUMMARY = SCHEMAS_DIR / "research_summary.schema.json"
YAML_PLAN = SCHEMAS_DIR / "yaml_plan.schema.json"
FAILURE_ANALYSIS = SCHEMAS_DIR / "failure_analysis.schema.json"
PATTERN_EXTRACTION = SCHEMAS_DIR / "pattern_extraction.schema.json"
COLLAB_PLAN = SCHEMAS_DIR / "collab_plan.schema.json"
CHAT_RESPONSE = SCHEMAS_DIR / "chat_response.schema.json"
MAIL_AGENT = SCHEMAS_DIR / "mail_agent.schema.json"
GRADE = SCHEMAS_DIR / "grade.schema.json"
CLARIFY = SCHEMAS_DIR / "clarify.schema.json"
