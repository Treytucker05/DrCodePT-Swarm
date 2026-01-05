
import sys
import logging
from pathlib import Path

# Add repo root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from agent.llm.server_client import ServerClient
from agent.autonomous.runner import AgentRunner
from agent.autonomous.config import PlannerConfig, AgentConfig, RunnerConfig

def debug_request():
    print("Testing ServerClient request...")
    client = ServerClient.from_env()
    
    # Simulate the exact request from AgentRunner's plan step
    prompt = "Task: Use python to calculate 12345 * 67890\n\nReturn ONLY valid JSON..." # Abbreviated
    # We need a valid schema path
    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / "agent" / "llm" / "schemas" / "plan_next_step.schema.json"
    
    if not schema_path.exists():
        print(f"Schema not found at {schema_path}")
        return

    print(f"Sending request (Schema: {schema_path})...")
    try:
        res = client.reason_json(prompt, schema_path=schema_path, timeout_seconds=60)
        print("Response received!")
        print(res)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_request()
