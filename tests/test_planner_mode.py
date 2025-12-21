from __future__ import annotations

from agent.modes.autonomous import _choose_planner_mode


def test_choose_planner_mode_simple() -> None:
    assert _choose_planner_mode("open calculator") == "react"


def test_choose_planner_mode_complex() -> None:
    assert (
        _choose_planner_mode("Research options and then summarize the results")
        == "plan_first"
    )
    assert (
        _choose_planner_mode(
            "setup the environment, configure the tools, then build the pipeline"
        )
        == "plan_first"
    )
