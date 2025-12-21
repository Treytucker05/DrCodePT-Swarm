from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from agent.autonomous.config import AgentConfig, RunContext
from agent.autonomous.loop_detection import LoopDetector
from agent.autonomous.memory.reflexion import ReflexionEntry, retrieve_reflexions, write_reflexion
from agent.autonomous.tools.builtins import build_default_tool_registry
from agent.autonomous.tools.registry import ToolRegistry
from agent.autonomous.models import ToolResult
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm.base import LLMClient

from .roles import CriticOutput, PlannerOutput, ResearcherOutput, run_critic, run_planner, run_researcher


class Phase(str, Enum):
    OBSERVE = "OBSERVE"
    RESEARCH = "RESEARCH"
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    REFLECT = "REFLECT"
    ASK_USER = "ASK_USER"
    DONE = "DONE"
    ABORT = "ABORT"


@dataclass
class OrchestratorConfig:
    max_steps: int = 30
    max_retries: int = 2
    heartbeat_seconds: float = 10.0
    parallel_research: bool = True
    allow_tool_execution: bool = True


@dataclass
class OrchestratorState:
    phase: Phase = Phase.OBSERVE
    step_index: int = 0
    retries: Dict[str, int] = field(default_factory=dict)
    last_error: str = ""
    last_tool: Optional[str] = None
    last_tool_result: Optional[ToolResult] = None
    last_plan: Optional[PlannerOutput] = None
    last_research: Optional[ResearcherOutput] = None
    qa_pairs: List[Dict[str, str]] = field(default_factory=list)
    context: str = ""
    context_fingerprint: str = ""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_context(text: str) -> str:
    return str(abs(hash(text)))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _phase_banner(phase: Phase) -> None:
    print(f"[TEAM MODE] Phase: {phase.value}")


def _with_heartbeat(fn: Callable[[], Any], *, heartbeat_seconds: float) -> Any:
    done = threading.Event()
    result: Dict[str, Any] = {}
    error: Dict[str, BaseException] = {}

    def _target() -> None:
        try:
            result["value"] = fn()
        except BaseException as exc:  # noqa: BLE001
            error["exc"] = exc
        finally:
            done.set()

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    start = time.monotonic()
    while not done.wait(timeout=heartbeat_seconds):
        elapsed = time.monotonic() - start
        print(f"[TEAM MODE] Still working... elapsed={elapsed:.1f}s")
    if error:
        raise error["exc"]
    return result.get("value")


def _tool_catalog(tools: ToolRegistry) -> List[Dict[str, Any]]:
    catalog = []
    for spec in tools.list_tools():
        catalog.append(
            {
                "name": spec.name,
                "description": spec.description,
                "args_schema": tools.tool_args_schema(spec.name),
            }
        )
    return catalog


class SupervisorOrchestrator:
    def __init__(
        self,
        *,
        objective: str,
        llm: LLMClient,
        agent_cfg: AgentConfig,
        run_dir: Path,
        tools: Optional[ToolRegistry] = None,
        loop_detector: Optional[LoopDetector] = None,
        config: Optional[OrchestratorConfig] = None,
        planner_fn: Callable[..., PlannerOutput] = run_planner,
        researcher_fn: Callable[..., ResearcherOutput] = run_researcher,
        critic_fn: Callable[..., CriticOutput] = run_critic,
        input_fn: Callable[[str], str] = input,
    ) -> None:
        self.objective = objective
        self.llm = llm
        self.agent_cfg = agent_cfg
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.tools = tools or build_default_tool_registry(agent_cfg, run_dir)
        self.loop_detector = loop_detector or LoopDetector()
        self.config = config or OrchestratorConfig()
        self.planner_fn = planner_fn
        self.researcher_fn = researcher_fn
        self.critic_fn = critic_fn
        self.input_fn = input_fn

        self.phase_log = self.run_dir / "phases.jsonl"
        self.execution_log = self.run_dir / "execution.jsonl"
        self.summary_path = self.run_dir / "summary.md"
        self.plan_path = self.run_dir / "plan.json"
        self.research_path = self.run_dir / "research.md"
        self.task_spec_path = self.run_dir / "task_spec.json"
        self.questions_path = self.run_dir / "questions.json"
        self.answers_path = self.run_dir / "answers.json"

        os.environ["REFLEXION_RUN_DIR"] = str(self.run_dir)

        self.ctx = RunContext(
            run_id=self.run_dir.name,
            run_dir=self.run_dir,
            workspace_dir=self.run_dir / "workspace",
        )
        self.ctx.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _log_phase(self, phase: Phase) -> None:
        _phase_banner(phase)
        _append_jsonl(self.phase_log, {"ts": _now_iso(), "phase": phase.value})

    def _observe(self, state: OrchestratorState) -> str:
        workspace = list(p.name for p in self.ctx.workspace_dir.iterdir())
        cwd_entries = list(p.name for p in Path.cwd().iterdir())
        snapshot = {
            "cwd": str(Path.cwd()),
            "workspace_entries": workspace[:50],
            "cwd_entries": cwd_entries[:50],
            "tools_available": [spec.name for spec in self.tools.list_tools()],
            "last_tool": state.last_tool,
            "last_tool_result": (state.last_tool_result.model_dump() if state.last_tool_result else None),
        }
        return json.dumps(snapshot, ensure_ascii=False)

    def _needs_research(self, objective: str, state: OrchestratorState) -> bool:
        lowered = objective.lower()
        if any(token in lowered for token in ("research", "compare", "overview", "explain")):
            return True
        if state.last_error and "unknown" in state.last_error.lower():
            return True
        return False

    def _ask_user(self, questions: List[str], state: OrchestratorState) -> None:
        payload = {
            "questions": [{"id": f"q{idx+1}", "text": q} for idx, q in enumerate(questions)]
        }
        _write_json(self.questions_path, payload)
        answers: Dict[str, str] = {}
        for q in payload["questions"]:
            qid = q["id"]
            text = q["text"]
            answer = ""
            while not answer.strip():
                answer = self.input_fn(f"- {qid}: {text} ").strip()
            answers[qid] = answer
            state.qa_pairs.append({"question": text, "answer": answer})
        _write_json(self.answers_path, {"answers": answers})
        if any("abort" in (a or "").lower() or "stop" in (a or "").lower() for a in answers.values()):
            state.phase = Phase.ABORT

    def _execute_step(self, step: Dict[str, Any]) -> ToolResult:
        tool = step.get("tool") or ""
        args = step.get("args") or {}
        result = self.tools.call(tool, args, self.ctx)
        _append_jsonl(
            self.execution_log,
            {"ts": _now_iso(), "tool": tool, "args": args, "result": result.model_dump()},
        )
        return result

    def _verify_step(self, step: Dict[str, Any], result: ToolResult) -> bool:
        if not result.success:
            return False
        check = (step.get("success_check") or "").strip()
        if not check:
            return True
        if check.lower().startswith("file exists:"):
            path = check.split(":", 1)[1].strip()
            return Path(path).exists()
        if check.lower().startswith("contains:"):
            needle = check.split(":", 1)[1].strip()
            hay = json.dumps(result.output, ensure_ascii=False) if result.output is not None else ""
            return needle in hay
        return True

    def _record_reflexion(self, state: OrchestratorState) -> None:
        entry = ReflexionEntry(
            id=str(uuid.uuid4()),
            timestamp=_now_iso(),
            objective=self.objective,
            context_fingerprint=state.context_fingerprint,
            phase=state.phase.value,
            tool_calls=[
                {"tool": state.last_tool, "result": state.last_tool_result.model_dump() if state.last_tool_result else {}}
            ],
            errors=[state.last_error] if state.last_error else [],
            reflection="Step failed; capture failure context for retry.",
            fix="Review failure and adjust plan/inputs before retry.",
            outcome="failure",
            tags=["team", "reflexion"],
        )
        write_reflexion(entry)

    def run(self) -> int:
        state = OrchestratorState()
        _write_json(self.task_spec_path, {"objective": self.objective, "ts": _now_iso()})
        steps_taken = 0

        while state.phase not in (Phase.DONE, Phase.ABORT):
            self._log_phase(state.phase)
            if steps_taken >= self.config.max_steps:
                state.phase = Phase.ABORT
                state.last_error = "max_steps_exceeded"
                continue

            if state.phase == Phase.OBSERVE:
                snapshot = self._observe(state)
                state.context = snapshot
                state.context_fingerprint = _hash_context(snapshot)
                if self._needs_research(self.objective, state) and self.config.parallel_research:
                    state.phase = Phase.PLAN
                else:
                    state.phase = Phase.RESEARCH if self._needs_research(self.objective, state) else Phase.PLAN
                continue

            if state.phase == Phase.RESEARCH:
                def _do_research():
                    return self.researcher_fn(
                        self.llm,
                        objective=self.objective,
                        context=state.context,
                        unknowns=None,
                    )

                try:
                    state.last_research = _with_heartbeat(
                        _do_research, heartbeat_seconds=self.config.heartbeat_seconds
                    )
                except Exception as exc:
                    state.last_error = f"research_error: {exc}"
                    state.last_research = ResearcherOutput()
                research_md = "\n".join(state.last_research.findings or [])
                self.research_path.write_text(research_md, encoding="utf-8")
                state.phase = Phase.PLAN
                continue

            if state.phase == Phase.PLAN:
                needs_research = self._needs_research(self.objective, state) and state.last_research is None
                reflexion_notes = []
                if state.last_error:
                    reflexions = retrieve_reflexions(self.objective, state.last_error, k=5)
                    reflexion_notes = [f"- {r.reflection} | fix: {r.fix}" for r in reflexions]

                tool_catalog = _tool_catalog(self.tools)

                def _do_plan():
                    return self.planner_fn(
                        self.llm,
                        objective=self.objective,
                        context=state.context,
                        tools=tool_catalog,
                        reflexions=reflexion_notes,
                    )

                if needs_research and self.config.parallel_research:
                    def _do_research():
                        return self.researcher_fn(
                            self.llm,
                            objective=self.objective,
                            context=state.context,
                            unknowns=None,
                        )

                    with ThreadPoolExecutor(max_workers=2) as executor:
                        future_plan = executor.submit(_do_plan)
                        future_research = executor.submit(_do_research)
                        start = time.monotonic()
                        last_beat = start
                        while not (future_plan.done() and future_research.done()):
                            time.sleep(0.25)
                            now = time.monotonic()
                            if now - last_beat >= self.config.heartbeat_seconds:
                                elapsed = now - start
                                print(f"[TEAM MODE] Still working... elapsed={elapsed:.1f}s")
                                last_beat = now
                        try:
                            state.last_plan = future_plan.result()
                        except Exception as exc:
                            state.last_error = f"planner_error: {exc}"
                            state.last_plan = PlannerOutput(
                                next_steps=[],
                                questions=[
                                    "Planner failed to load. What should I do next? (e.g., 'retry', 'abort', or describe the next step)"
                                ],
                            )
                        try:
                            state.last_research = future_research.result()
                        except Exception as exc:
                            state.last_error = state.last_error or f"research_error: {exc}"
                            state.last_research = ResearcherOutput()
                        if state.last_research and state.last_research.findings:
                            state.context = state.context + "\n" + "\n".join(state.last_research.findings)
                            state.context_fingerprint = _hash_context(state.context)
                            self.research_path.write_text(
                                "\n".join(state.last_research.findings), encoding="utf-8"
                            )
                else:
                    try:
                        state.last_plan = _with_heartbeat(
                            _do_plan, heartbeat_seconds=self.config.heartbeat_seconds
                        )
                    except Exception as exc:
                        state.last_error = f"planner_error: {exc}"
                        state.last_plan = PlannerOutput(
                            next_steps=[],
                            questions=[
                                "Planner failed to load. What should I do next? (e.g., 'retry', 'abort', or describe the next step)"
                            ],
                        )
                _write_json(self.plan_path, state.last_plan.model_dump())

                if state.last_plan.questions:
                    state.phase = Phase.ASK_USER
                else:
                    state.phase = Phase.EXECUTE
                continue

            if state.phase == Phase.ASK_USER:
                questions = list(state.last_plan.questions if state.last_plan else [])
                if questions:
                    self._ask_user(questions, state)
                    qa_summary = "\n".join(
                        f"Q: {q['question']}\nA: {q['answer']}" for q in state.qa_pairs
                    )
                    state.context = state.context + "\n" + qa_summary
                    state.context_fingerprint = _hash_context(state.context)
                state.phase = Phase.PLAN
                continue

            if state.phase == Phase.EXECUTE:
                if not state.last_plan or not state.last_plan.next_steps:
                    state.phase = Phase.ABORT
                    state.last_error = "no_steps"
                    continue
                step = state.last_plan.next_steps[0].model_dump()
                action_sig = f"{step.get('tool')}:{step.get('description')}"
                if self.loop_detector.update(action_sig, state.context_fingerprint):
                    state.last_error = "loop_detected"
                    state.phase = Phase.RESEARCH
                    continue
                if not self.config.allow_tool_execution:
                    state.last_error = "tool_execution_disabled"
                    state.phase = Phase.REFLECT
                    continue
                state.last_tool = step.get("tool")
                result = _with_heartbeat(
                    lambda: self._execute_step(step),
                    heartbeat_seconds=self.config.heartbeat_seconds,
                )
                state.last_tool_result = result
                state.last_error = result.error or ""
                state.phase = Phase.VERIFY
                steps_taken += 1
                continue

            if state.phase == Phase.VERIFY:
                if not state.last_plan or not state.last_plan.next_steps:
                    state.phase = Phase.DONE
                    continue
                step = state.last_plan.next_steps[0].model_dump()
                ok = self._verify_step(step, state.last_tool_result or ToolResult(False))
                if ok:
                    state.phase = Phase.DONE
                else:
                    state.last_error = state.last_error or "verification_failed"
                    state.phase = Phase.REFLECT
                continue

            if state.phase == Phase.REFLECT:
                self._record_reflexion(state)
                try:
                    critic = self.critic_fn(
                        self.llm,
                        objective=self.objective,
                        context=state.context,
                        error=state.last_error,
                        last_step=state.last_plan.next_steps[0].model_dump()
                        if state.last_plan and state.last_plan.next_steps
                        else None,
                    )
                except Exception as exc:
                    critic = CriticOutput(
                        decision="ask_user",
                        rationale=f"critic_error: {exc}",
                        suggested_changes=[],
                    )
                decision = critic.decision
                if decision == "retry":
                    step_id = (
                        state.last_plan.next_steps[0].id
                        if state.last_plan and state.last_plan.next_steps
                        else "step"
                    )
                    state.retries[step_id] = state.retries.get(step_id, 0) + 1
                    if state.retries[step_id] > self.config.max_retries:
                        state.phase = Phase.ABORT
                    else:
                        state.phase = Phase.PLAN
                elif decision == "research":
                    state.phase = Phase.RESEARCH
                elif decision == "ask_user":
                    state.phase = Phase.ASK_USER
                elif decision == "pivot":
                    state.phase = Phase.PLAN
                elif decision == "abort":
                    state.phase = Phase.ABORT
                else:
                    state.phase = Phase.PLAN
                continue

        status = "success" if state.phase == Phase.DONE else "aborted"
        self.summary_path.write_text(
            f"status: {status}\nerror: {state.last_error}\n", encoding="utf-8"
        )
        return 0 if state.phase == Phase.DONE else 1


def run_team(
    objective: str,
    *,
    unsafe_mode: bool = False,
    run_dir: Optional[Path] = None,
    llm: Optional[LLMClient] = None,
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

    agent_cfg = AgentConfig(
        unsafe_mode=bool(unsafe_mode),
        enable_web_gui=True,
        enable_desktop=True,
        allow_human_ask=True,
    )
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    base_folder = "team"
    lowered = (objective or "").lower()
    if "team_smoke" in lowered or "smoke test" in lowered:
        base_folder = "team_smoke"
    root = _repo_root() / "runs" / base_folder
    run_dir = run_dir or (root / run_id)
    orchestrator = SupervisorOrchestrator(
        objective=objective,
        llm=llm,
        agent_cfg=agent_cfg,
        run_dir=run_dir,
    )
    return orchestrator.run()
