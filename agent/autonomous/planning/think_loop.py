from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from agent.autonomous.config import AgentConfig
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm.base import LLMClient

from agent.autonomous.supervisor.roles import (
    CriticOutput,
    PlannerOutput,
    ResearcherOutput,
    run_critic,
    run_planner,
    run_researcher,
)


@dataclass
class ThinkConfig:
    max_rounds: int = 5


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _truncate(text: str, limit: int = 140) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _format_intent(plan: PlannerOutput) -> str:
    if plan.questions:
        return f"ask_user — {_truncate(plan.questions[0])}"
    if not plan.next_steps:
        return "no next steps"
    step = plan.next_steps[0]
    desc = step.description or step.id or "next step"
    return f"{step.tool} — {_truncate(desc)}"


def run_think_loop(
    objective: str,
    *,
    llm: Optional[LLMClient] = None,
    config: Optional[ThinkConfig] = None,
    run_dir: Optional[Path] = None,
    planner_fn: Callable[..., PlannerOutput] = run_planner,
    researcher_fn: Callable[..., ResearcherOutput] = run_researcher,
    critic_fn: Callable[..., CriticOutput] = run_critic,
    input_fn: Callable[[str], str] = input,
) -> int:
    if llm is None:
        try:
            llm = CodexCliClient.from_env()
        except CodexCliNotFoundError as exc:
            print(str(exc))
            return 2
        except CodexCliAuthError as exc:
            print(str(exc))
            return 2

    cfg = config or ThinkConfig()
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    base = _repo_root() / "runs" / "think"
    run_dir = run_dir or (base / run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    task_spec = {"objective": objective, "ts": _now_iso()}
    _write_json(run_dir / "task_spec.json", task_spec)

    rounds_log = run_dir / "rounds.jsonl"
    research_path = run_dir / "research.md"
    plan_path = run_dir / "plan.json"
    summary_path = run_dir / "summary.md"

    context = ""
    last_plan_text = ""
    researcher_notes: List[str] = []

    for round_idx in range(cfg.max_rounds):
        print(f"[THINK MODE] Round {round_idx + 1}/{cfg.max_rounds}")
        planner_out = planner_fn(
            llm,
            objective=objective,
            context=context,
            tools=[],
            reflexions=[],
        )
        print(f"[THINK MODE] Intent: {_format_intent(planner_out)}")
        _write_json(plan_path, planner_out.model_dump())

        if planner_out.questions:
            answers: List[str] = []
            for idx, q in enumerate(planner_out.questions):
                ans = ""
                while not ans.strip():
                    ans = input_fn(f"- q{idx+1}: {q} ").strip()
                answers.append(f"Q: {q}\nA: {ans}")
            context = context + "\n" + "\n".join(answers)
            continue

        plan_text = json.dumps(planner_out.model_dump(), sort_keys=True)
        critic_out = critic_fn(
            llm,
            objective=objective,
            context=context,
            error="",
            last_step=planner_out.next_steps[0].model_dump() if planner_out.next_steps else None,
        )

        _append_jsonl(
            rounds_log,
            {
                "round": round_idx + 1,
                "plan": planner_out.model_dump(),
                "critic": critic_out.model_dump(),
            },
        )

        if critic_out.decision == "research":
            research_out = researcher_fn(
                llm,
                objective=objective,
                context=context,
                unknowns=None,
            )
            researcher_notes = research_out.findings
            if researcher_notes:
                research_path.write_text("\n".join(researcher_notes), encoding="utf-8")
                context = context + "\n" + "\n".join(researcher_notes)
            continue

        if critic_out.decision == "continue":
            summary_path.write_text("status: converged\n", encoding="utf-8")
            return 0

        if plan_text == last_plan_text:
            summary_path.write_text("status: converged\n", encoding="utf-8")
            return 0

        last_plan_text = plan_text

    summary_path.write_text("status: max_rounds\n", encoding="utf-8")
    return 0
