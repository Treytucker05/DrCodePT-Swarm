from __future__ import annotations

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.llm.stub import StubLLM
from agent.autonomous.runner import AgentRunner


def test_agent_runner_smoke(tmp_path) -> None:
    llm = StubLLM(
        responses=[
            {
                "goal": "smoke",
                "steps": [
                    {
                        "goal": "print smoke-ok",
                        "tool_name": "python_exec",
                        "tool_args": [
                            {"key": "code", "value": "print('smoke-ok')"}
                        ],
                        "success_criteria": ["stdout contains smoke-ok"],
                    }
                ],
            },
            {"status": "success", "explanation_short": "python_exec ran", "next_hint": ""},
            {
                "goal": "smoke",
                "steps": [
                    {
                        "goal": "finish",
                        "tool_name": "finish",
                        "tool_args": [{"key": "summary", "value": "done"}],
                        "success_criteria": ["run complete"],
                    }
                ],
            },
            {"status": "success", "explanation_short": "finished", "next_hint": ""},
        ]
    )

    agent_cfg = AgentConfig(
        enable_web_gui=False,
        enable_desktop=False,
        memory_db_path=tmp_path / "memory.sqlite3",
    )
    runner_cfg = RunnerConfig(max_steps=5, timeout_seconds=30)
    planner_cfg = PlannerConfig(mode="react")
    run_dir = tmp_path / "run"

    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        run_dir=run_dir,
    )
    result = runner.run(task="Smoke test: print 'smoke-ok'")

    assert result.success
    assert result.stop_reason == "goal_achieved"
