
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.config.profile import resolve_profile
from agent.autonomous.runner import AgentRunner
from agent.llm.codex_cli_client import CodexCliClient

def run_benchmark():
    print("Starting Benchmark...")
    
    # Setup Paths
    repo_root = Path(__file__).resolve().parents[1]
    run_dir = repo_root / "runs" / "benchmark" / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run Directory: {run_dir}")

    # Config
    profile = resolve_profile("fast")
    agent_cfg = AgentConfig(profile=profile)
    runner_cfg = RunnerConfig(
        max_steps=10,
        timeout_seconds=300,
        llm_heartbeat_seconds=profile.heartbeat_s,
        llm_plan_timeout_seconds=profile.plan_timeout_s,
        llm_plan_retry_timeout_seconds=profile.plan_retry_timeout_s,
    )
    planner_cfg = PlannerConfig(mode="react")

    planner_cfg = PlannerConfig(mode="react")

    # Client
    try:
        from agent.llm.server_client import ServerClient
        llm = ServerClient.from_env()
        print("Using ServerClient for benchmark.")
    except Exception as e:
        print(f"Failed to init LLM: {e}")
        return

    # Runner
    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        run_dir=run_dir,
        agent_id="benchmark",
    )

    tasks = [
        "Use python to calculate 12345 * 67890",
        "List the files in the current directory"
    ]

    for task in tasks:
        print(f"\n--- Running Task: {task} ---")
        t0 = time.time()
        result = runner.run(task)
        dur = time.time() - t0
        print(f"Task Completed: {result.success}")
        print(f"Duration: {dur:.2f}s")
        print(f"Stop Reason: {result.stop_reason}")

    # Analyze Performance Log
    perf_log = run_dir / "performance.log"
    if perf_log.exists():
        print("\n--- Performance Summary ---")
        lines = perf_log.read_text(encoding="utf-8").strip().split("\n")
        logs = [json.loads(line) for line in lines]
        
        llm_logs = [l for l in logs if l["cat"] == "llm"]
        tool_logs = [l for l in logs if l["cat"] == "tool"]
        
        total_llm_time = sum(l["dur_ms"] for l in llm_logs)
        total_tool_time = sum(l["dur_ms"] for l in tool_logs)
        
        print(f"Total LLM Calls: {len(llm_logs)}")
        print(f"Total LLM Time: {total_llm_time/1000:.2f}s")
        if llm_logs:
            print(f"Avg LLM Time: {(total_llm_time/len(llm_logs))/1000:.2f}s")
            
        print(f"Total Tool Calls: {len(tool_logs)}")
        print(f"Total Tool Time: {total_tool_time/1000:.2f}s")

if __name__ == "__main__":
    run_benchmark()
