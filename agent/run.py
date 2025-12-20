from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        return


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m agent.run", description="Run the autonomous agent loop.")
    p.add_argument("--task", required=True, help="Goal/task for the agent to accomplish.")
    p.add_argument("--planner-mode", choices=["react", "plan_first"], default="react")
    p.add_argument("--num-candidates", type=int, default=1, help="Plan-first: number of candidate plans to generate.")
    p.add_argument("--max-plan-steps", type=int, default=6, help="Plan-first: max steps per plan.")
    p.add_argument("--max-steps", type=int, default=30)
    p.add_argument("--timeout-seconds", type=int, default=600)
    p.add_argument("--cost-budget-usd", type=float, default=None)

    p.add_argument("--unsafe-mode", action="store_true", help="Enable unsafe tools/actions (shell, external writes, etc).")
    p.add_argument("--enable-web-gui", action="store_true", help="Enable Playwright Web/GUI snapshot tool.")
    p.add_argument("--enable-desktop", action="store_true", help="Enable Desktop adapter stub tool.")
    p.add_argument("--pre-mortem", action="store_true", help="Enable anticipatory reflection before actions.")

    p.add_argument("--memory-db", type=str, default=None, help="SQLite path for long-term memory store.")
    p.add_argument("--run-dir", type=str, default=None, help="Directory for this run's artifacts (trace, workspace).")
    p.add_argument("--stub-llm", action="store_true", help="Use a deterministic stub LLM (no API keys).")
    return p


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    args = build_arg_parser().parse_args(argv)

    from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
    from agent.autonomous.llm.stub import StubLLM
    from agent.autonomous.runner import AgentRunner
    from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError

    agent_cfg = AgentConfig(
        unsafe_mode=bool(args.unsafe_mode),
        enable_web_gui=bool(args.enable_web_gui),
        enable_desktop=bool(args.enable_desktop),
        pre_mortem_enabled=bool(args.pre_mortem),
        memory_db_path=Path(args.memory_db) if args.memory_db else None,
    )
    runner_cfg = RunnerConfig(
        max_steps=int(args.max_steps),
        timeout_seconds=int(args.timeout_seconds),
        cost_budget_usd=args.cost_budget_usd,
    )
    planner_cfg = PlannerConfig(
        mode=str(args.planner_mode),
        num_candidates=int(args.num_candidates),
        max_plan_steps=int(args.max_plan_steps),
    )

    run_dir = Path(args.run_dir).resolve() if args.run_dir else None

    if args.stub_llm:
        llm = StubLLM(
            responses=[
                {
                    "goal": "stub",
                    "steps": [
                        {
                            "goal": "Print hello",
                            "tool_name": "python_exec",
                            "tool_args": {"code": 'print("hello from stub")'},
                            "success_criteria": ["stdout contains hello from stub"],
                        }
                    ],
                },
                {"status": "success", "explanation_short": "ok", "next_hint": ""},
                {
                    "goal": "stub",
                    "steps": [
                        {
                            "goal": "Finish",
                            "tool_name": "finish",
                            "tool_args": {"summary": "stub done"},
                            "success_criteria": ["done"],
                        }
                    ],
                },
                {"status": "success", "explanation_short": "done", "next_hint": ""},
            ]
        )
    else:
        try:
            llm = CodexCliClient.from_env()
        except CodexCliNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except CodexCliAuthError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    runner = AgentRunner(cfg=runner_cfg, agent_cfg=agent_cfg, planner_cfg=planner_cfg, llm=llm, run_dir=run_dir)
    result = runner.run(args.task)
    print(f"success={result.success} stop_reason={result.stop_reason} steps={result.steps_executed}")
    if result.trace_path:
        print(f"trace={result.trace_path}")
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
