"""
Integration smoke tests for the autonomous agent skeleton.

These checks avoid any local-model dependencies and can run with a stubbed LLM.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def run_tests() -> int:
    # Imports are the primary "smoke test" for now.
    from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
    from agent.autonomous.runner import AgentRunner
    from agent.autonomous.llm.stub import StubLLM

    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)

        cfg = AgentConfig(memory_db_path=run_dir / "memory.sqlite3")
        runner_cfg = RunnerConfig(max_steps=5, timeout_seconds=30)
        planner_cfg = PlannerConfig(mode="react")
        llm = StubLLM(
            responses=[
                {
                    "goal": "smoke",
                    "steps": [
                        {
                            "goal": "print smoke-ok",
                            "tool_name": "python_exec",
                            "tool_args": {"code": 'print("smoke-ok")'},
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
                            "tool_args": {"summary": "done"},
                            "success_criteria": ["run complete"],
                        }
                    ],
                },
                {"status": "success", "explanation_short": "finished", "next_hint": ""},
            ]
        )

        runner = AgentRunner(
            cfg=runner_cfg,
            agent_cfg=cfg,
            planner_cfg=planner_cfg,
            llm=llm,
            run_dir=run_dir,
        )
        result = runner.run(task="Smoke test: print 'smoke-ok'")
        if not result.success:
            print(f"FAIL: {result.stop_reason}")
            return 1

    print("PASS: autonomous agent smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
