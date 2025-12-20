from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.runner import AgentRunner
from agent.llm.codex_cli_client import CodexCliClient


def load_tasks(tasks_dir: Path) -> List[Dict[str, Any]]:
    tasks = []
    for path in sorted(tasks_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("goal"):
                data["id"] = data.get("id") or path.stem
                tasks.append(data)
        except Exception:
            continue
    return tasks


def parse_trace(trace_path: Path) -> Dict[str, Any]:
    failed_steps = 0
    total_steps = 0
    loop_detected = False
    if not trace_path.is_file():
        return {"failed_steps": 0, "total_steps": 0, "loop_detected": False}
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except Exception:
            continue
        if event.get("type") == "step":
            total_steps += 1
            result = event.get("result") or {}
            if not result.get("success", False):
                failed_steps += 1
        if event.get("type") == "stop" and event.get("reason") == "loop_detected":
            loop_detected = True
    return {"failed_steps": failed_steps, "total_steps": total_steps, "loop_detected": loop_detected}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-dir", default="tasks", help="Directory of task JSON files")
    parser.add_argument("--out-dir", default="runs/benchmarks", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Only print tasks, do not run")
    args = parser.parse_args()

    tasks_dir = Path(args.tasks_dir)
    out_dir = Path(args.out_dir) / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks(tasks_dir)
    if not tasks:
        print("No tasks found.")
        return

    if args.dry_run:
        print(f"Found {len(tasks)} tasks:")
        for t in tasks:
            print(f"- {t.get('id')}: {t.get('goal')}")
        return

    llm = CodexCliClient.from_env()
    runner_cfg = RunnerConfig(max_steps=20, timeout_seconds=300)
    agent_cfg = AgentConfig(unsafe_mode=False, enable_web_gui=False, enable_desktop=False)
    planner_cfg = PlannerConfig(mode="plan_first")

    results: List[Dict[str, Any]] = []
    loops = 0
    for task in tasks:
        goal = task["goal"]
        runner = AgentRunner(cfg=runner_cfg, agent_cfg=agent_cfg, planner_cfg=planner_cfg, llm=llm)
        run_result = runner.run(goal)
        trace_path = Path(run_result.trace_path) if run_result.trace_path else None
        trace_stats = parse_trace(trace_path) if trace_path else {"failed_steps": 0, "total_steps": 0, "loop_detected": False}
        if trace_stats["loop_detected"]:
            loops += 1
        tool_error_rate = (
            trace_stats["failed_steps"] / trace_stats["total_steps"] if trace_stats["total_steps"] else 0.0
        )
        results.append(
            {
                "id": task.get("id"),
                "goal": goal,
                "success": run_result.success,
                "steps": run_result.steps_executed,
                "tool_error_rate": round(tool_error_rate, 3),
                "loop_detected": trace_stats["loop_detected"],
                "trace_path": run_result.trace_path,
                "stop_reason": run_result.stop_reason,
            }
        )

    success_rate = sum(1 for r in results if r["success"]) / len(results)
    avg_steps = sum(r["steps"] for r in results) / max(1, len(results))
    avg_tool_error = sum(r["tool_error_rate"] for r in results) / max(1, len(results))
    loop_rate = loops / len(results)

    summary = {
        "tasks": len(results),
        "success_rate": round(success_rate, 3),
        "avg_steps": round(avg_steps, 2),
        "avg_tool_error_rate": round(avg_tool_error, 3),
        "loop_rate": round(loop_rate, 3),
        "results_path": str(out_dir / "results.json"),
    }

    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with (out_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "success", "steps", "tool_error_rate", "loop_detected", "stop_reason", "trace_path"],
        )
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
