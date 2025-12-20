from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.llm.stub import StubLLM
from agent.autonomous.models import ToolResult
from agent.autonomous.runner import AgentRunner
from agent.autonomous.tools.registry import ToolRegistry, ToolSpec


def test_loop_detection_trips_on_repeated_identical_failures(tmp_path: Path):
    agent_cfg = AgentConfig(memory_db_path=tmp_path / "memory.sqlite3")
    runner_cfg = RunnerConfig(max_steps=10, timeout_seconds=30, loop_repeat_threshold=3, loop_window=8)
    planner_cfg = PlannerConfig(mode="react")

    class FailArgs(BaseModel):
        pass

    def fail_tool(ctx, args: FailArgs) -> ToolResult:  # noqa: ARG001
        return ToolResult(success=False, error="fail")

    tools = ToolRegistry(agent_cfg=agent_cfg)
    tools.register(ToolSpec(name="fail_tool", args_model=FailArgs, fn=fail_tool))

    llm = StubLLM(
        responses=[
            {
                "goal": "t",
                "steps": [
                    {"goal": "do fail", "tool_name": "fail_tool", "tool_args": {}, "success_criteria": ["fails"]}
                ],
            },
            {"status": "replan", "explanation_short": "failed", "next_hint": "retrying"},
            {
                "goal": "t",
                "steps": [
                    {"goal": "do fail", "tool_name": "fail_tool", "tool_args": {}, "success_criteria": ["fails"]}
                ],
            },
            {"status": "replan", "explanation_short": "failed", "next_hint": "retrying"},
            {
                "goal": "t",
                "steps": [
                    {"goal": "do fail", "tool_name": "fail_tool", "tool_args": {}, "success_criteria": ["fails"]}
                ],
            },
            {"status": "replan", "explanation_short": "failed", "next_hint": "retrying"},
        ]
    )

    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        tools=tools,
        run_dir=tmp_path / "run",
    )
    result = runner.run("Trigger loop detection")
    assert result.success is False
    assert result.stop_reason == "loop_detected"


def test_tool_schema_validation_rejects_invalid_args(tmp_path: Path):
    agent_cfg = AgentConfig(memory_db_path=tmp_path / "memory.sqlite3")

    class Args(BaseModel):
        x: int

    def tool(ctx, args: Args) -> ToolResult:  # noqa: ARG001
        return ToolResult(success=True, output={"x": args.x})

    tools = ToolRegistry(agent_cfg=agent_cfg)
    tools.register(ToolSpec(name="typed_tool", args_model=Args, fn=tool))

    res = tools.call("typed_tool", {"x": "abc"}, ctx=None)  # type: ignore[arg-type]
    assert res.success is False
    assert res.error and "validation" in res.error.lower()


def test_closed_loop_reaches_finish_stop_condition(tmp_path: Path):
    agent_cfg = AgentConfig(memory_db_path=tmp_path / "memory.sqlite3")
    runner_cfg = RunnerConfig(max_steps=10, timeout_seconds=30)
    planner_cfg = PlannerConfig(mode="react")

    class EchoArgs(BaseModel):
        text: str

    def echo(ctx, args: EchoArgs) -> ToolResult:  # noqa: ARG001
        return ToolResult(success=True, output={"echo": args.text})

    class FinishArgs(BaseModel):
        summary: str = ""

    def finish(ctx, args: FinishArgs) -> ToolResult:  # noqa: ARG001
        return ToolResult(success=True, output={"summary": args.summary})

    tools = ToolRegistry(agent_cfg=agent_cfg)
    tools.register(ToolSpec(name="echo", args_model=EchoArgs, fn=echo))
    tools.register(ToolSpec(name="finish", args_model=FinishArgs, fn=finish))

    llm = StubLLM(
        responses=[
            {
                "goal": "x",
                "steps": [
                    {"goal": "echo hi", "tool_name": "echo", "tool_args": {"text": "hi"}, "success_criteria": ["echo==hi"]}
                ],
            },
            {"status": "success", "explanation_short": "echo ok", "next_hint": ""},
            {
                "goal": "x",
                "steps": [
                    {"goal": "finish", "tool_name": "finish", "tool_args": {"summary": "done"}, "success_criteria": ["done"]}
                ],
            },
            {"status": "success", "explanation_short": "finish ok", "next_hint": ""},
        ]
    )

    run_dir = tmp_path / "run"
    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        tools=tools,
        run_dir=run_dir,
    )
    result = runner.run("Say hi then finish")
    assert result.success is True
    assert result.stop_reason == "goal_achieved"
    assert result.trace_path and Path(result.trace_path).is_file()
