
from pathlib import Path
from agent.autonomous.runner import AgentRunner
from agent.autonomous.config import RunnerConfig, AgentConfig
from agent.autonomous.tools.builtins import build_default_tool_registry

def debug_reaction():
    agent_cfg = AgentConfig(
        llm_backend="server",
        allow_human_ask=True,
        enable_desktop=True, # Enable to see if it tries to use it
    )
    runner_cfg = RunnerConfig(
        max_steps=10,
        timeout_seconds=300,
        profile="fast",
    )
    
    # Simulate turn 2 context
    context = (
        "Current Local Time: 2026-01-04 00:44:19\n"
        "Context from previous turns in this session:\n"
        "User: What is on my google calendar for tomorrow 2-4pm?\n"
        "Assistant: No events found on your Google Calendar tomorrow between 2–4 PM (Central Time).\n"
        "Current Task: what about 12-2pm"
    )
    
    print("Initializing AgentRunner...")
    runner = AgentRunner(runner_cfg, agent_cfg=agent_cfg)
    
    print(f"Running task with context:\n{context}")
    result = runner.run(context)
    
    print(f"Final Stop Reason: {result.stop_reason}")
    print(f"Success: {result.success}")
    print(f"Steps: {result.steps_executed}")
    
    # Read trace to see tools called
    trace_path = Path(result.trace_path)
    if trace_path.exists():
        print("Trace summary:")
        with open(trace_path, 'r') as f:
            for line in f:
                import json
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "step":
                        print(f"  Step: {entry.get('tool_name')} - {entry.get('goal')}")
                    elif entry.get("type") == "tool":
                        print(f"  Tool Call: {entry.get('tool')} -> {'SUCCESS' if entry.get('success') else 'FAILED'}")
                    elif entry.get("type") == "error":
                        print(f"  ERROR: {entry.get('tool_name')}: {entry.get('error')}")
                except Exception:
                    pass

if __name__ == "__main__":
    debug_reaction()
