from pathlib import Path

from agent.autonomous.planning.think_loop import ThinkConfig, run_think_loop
from agent.autonomous.supervisor.roles import CriticOutput, PlanStep, PlannerOutput


def test_think_loop_converges(tmp_path):
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

    def critic_fn(_llm, *, objective, context, error, last_step=None):
        return CriticOutput(decision="continue", rationale="good", suggested_changes=[])

    result = run_think_loop(
        "Think test",
        run_dir=tmp_path / "think",
        config=ThinkConfig(max_rounds=3),
        llm=object(),  # type: ignore[arg-type]
        planner_fn=planner_fn,
        critic_fn=critic_fn,
    )
    assert result == 0
    summary = Path(tmp_path / "think" / "summary.md").read_text(encoding="utf-8")
    assert "converged" in summary
