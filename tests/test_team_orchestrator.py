import json
from typing import Any, Dict, List

from pydantic import BaseModel

from agent.autonomous.config import AgentConfig
from agent.autonomous.loop_detection import LoopDetector
from agent.autonomous.models import ToolResult
from agent.autonomous.tools.registry import ToolRegistry, ToolSpec
from agent.autonomous.supervisor.orchestrator import OrchestratorConfig, SupervisorOrchestrator
from agent.autonomous.supervisor.roles import CriticOutput, PlanStep, PlannerOutput, ResearcherOutput, run_planner
from agent.llm import schemas as llm_schemas
from agent.llm.errors import CodexCliExecutionError


class NoopArgs(BaseModel):
    pass


def test_orchestrator_ask_user_gate(tmp_path):
    asked = {"done": False}
    tool_calls: List[Dict[str, Any]] = []

    def noop_tool(_ctx, _args):
        assert asked["done"], "Tool executed before ASK_USER answers."
        tool_calls.append({"ok": True})
        return ToolResult(success=True, output={"ok": True})

    tools = ToolRegistry(agent_cfg=AgentConfig())
    tools.register(ToolSpec(name="noop", args_model=NoopArgs, fn=noop_tool, description="noop"))

    planner_calls = {"count": 0}

    def planner_fn(_llm, *, objective, context, tools, reflexions):
        planner_calls["count"] += 1
        if planner_calls["count"] == 1:
            return PlannerOutput(next_steps=[], questions=["Need preference?"])
        return PlannerOutput(
            next_steps=[
                PlanStep(
                    id="s1",
                    description="noop",
                    tool="noop",
                    args={},
                    success_check="",
                    fallback="",
                )
            ],
            questions=[],
        )

    def input_fn(_prompt: str) -> str:
        asked["done"] = True
        return "answer"

    orchestrator = SupervisorOrchestrator(
        objective="Test ask gate",
        llm=None,  # type: ignore[arg-type]
        agent_cfg=AgentConfig(),
        run_dir=tmp_path / "run",
        tools=tools,
        config=OrchestratorConfig(max_steps=3, allow_tool_execution=True),
        planner_fn=planner_fn,
        input_fn=input_fn,
    )
    result = orchestrator.run()
    assert result == 0
    assert tool_calls, "Expected tool to be called after answers."


def test_orchestrator_loop_detection_switches_to_research(tmp_path):
    research_called = {"count": 0}

    class OneShotLoop(LoopDetector):
        def __init__(self):
            super().__init__()
            self.called = 0

        def update(self, tool_name: str, args_hash: str, output_hash: str) -> bool:  # noqa: ARG002
            self.called += 1
            return self.called == 1

    def planner_fn(_llm, *, objective, context, tools, reflexions):
        return PlannerOutput(
            next_steps=[
                PlanStep(
                    id="s1",
                    description="noop",
                    tool="noop",
                    args={},
                    success_check="",
                    fallback="",
                )
            ],
            questions=[],
        )

    def researcher_fn(_llm, *, objective, context, unknowns):
        research_called["count"] += 1
        return ResearcherOutput(findings=["loop detected"], sources=[], recommended_steps=[], caveats=[])

    tools = ToolRegistry(agent_cfg=AgentConfig())
    tools.register(
        ToolSpec(
            name="noop",
            args_model=NoopArgs,
            fn=lambda _ctx, _args: ToolResult(success=True),
            description="noop",
        )
    )

    orchestrator = SupervisorOrchestrator(
        objective="Loop test",
        llm=None,  # type: ignore[arg-type]
        agent_cfg=AgentConfig(),
        run_dir=tmp_path / "run2",
        tools=tools,
        loop_detector=OneShotLoop(),
        config=OrchestratorConfig(max_steps=3, allow_tool_execution=True),
        planner_fn=planner_fn,
        researcher_fn=researcher_fn,
    )
    orchestrator.run()
    assert research_called["count"] >= 1


def test_orchestrator_planner_json_failure_fallback(tmp_path):
    class FailingPlannerLLM:
        def reason_json(self, prompt, schema_path=None, timeout_seconds=None):
            if schema_path == llm_schemas.CHAT_RESPONSE:
                return {"response": "Please retry with a smaller task."}
            raise CodexCliExecutionError("planner json failed")

    def critic_fn(_llm, *, objective, context, error, last_step=None):
        return CriticOutput(decision="abort", rationale="stop", suggested_changes=[])

    tools = ToolRegistry(agent_cfg=AgentConfig())
    run_dir = tmp_path / "run_planner_fail"
    orchestrator = SupervisorOrchestrator(
        objective="Planner JSON failure",
        llm=FailingPlannerLLM(),  # type: ignore[arg-type]
        agent_cfg=AgentConfig(),
        run_dir=run_dir,
        tools=tools,
        config=OrchestratorConfig(max_steps=3, allow_tool_execution=False),
        planner_fn=run_planner,
        critic_fn=critic_fn,
    )
    result = orchestrator.run()
    assert result == 1
    error_path = run_dir / "errors" / "planner_error.txt"
    assert error_path.is_file()
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    assert plan["next_steps"][0]["tool"] == "human_ask"


def test_team_summary_records_fail_with_repro(tmp_path):
    def planner_fn(_llm, *, objective, context, tools, reflexions):
        return PlannerOutput(next_steps=[], questions=[])

    def critic_fn(_llm, *, objective, context, error, last_step=None):
        return CriticOutput(decision="abort", rationale="stop", suggested_changes=[])

    run_dir = tmp_path / "run_summary"
    orchestrator = SupervisorOrchestrator(
        objective="Summary fail case",
        llm=None,  # type: ignore[arg-type]
        agent_cfg=AgentConfig(),
        run_dir=run_dir,
        tools=ToolRegistry(agent_cfg=AgentConfig()),
        config=OrchestratorConfig(max_steps=2, allow_tool_execution=False),
        planner_fn=planner_fn,
        critic_fn=critic_fn,
    )
    result = orchestrator.run()
    assert result == 1
    summary = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "result: FAIL" in summary
    assert "repro: Team: Summary fail case" in summary
    assert "Traceback" not in summary
