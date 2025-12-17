import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# Ensure repository root is importable when launched from other folders
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

try:
    from agent.schemas.task_schema import TaskDefinition
    from agent.supervisor.supervisor import run_task
except ImportError:
    # Fallback for local testing if run from outside the main project root
    print("Error: Could not import agent modules. Check PYTHONPATH.")
    sys.exit(1)


def main():
    """
    Reads YAML from stdin (piped from Codex), converts it to a TaskDefinition,
    and executes it using the custom supervisor.
    """
    raw_yaml = sys.stdin.read()
    
    # --- Start Robust Parsing Loop ---
    try:
        if not raw_yaml.strip():
            raise ValueError("Received empty input from Codex.")

        # 1. Parse the YAML into a Python dictionary
        task_data = yaml.safe_load(raw_yaml)
        if not isinstance(task_data, dict):
            raise ValueError("Codex output is not a valid YAML dictionary.")

        # 2. Validate and convert to TaskDefinition object
        task_def = TaskDefinition(**task_data)

    except Exception as e:
        # This is the failure point. Instead of crashing, we report the error 
        # in a structured way that a human (or another LLM) can use to correct the plan.
        print(f"\n--- PLANNER ERROR: INVALID YAML OUTPUT ---")
        print(f"Error: {e}")
        print(f"The following YAML failed to parse:")
        print("---------------------------------------")
        print(raw_yaml)
        print("---------------------------------------")
        print("ACTION REQUIRED: The Planner (Codex) must be re-prompted with this error to generate a corrected YAML plan.")
        sys.exit(1)
    # --- End Robust Parsing Loop ---

    # 3. Execute the task using the custom supervisor
    print(f"--- Supervisor: Starting Task: {task_def.goal} ---")
    try:
        run_result = run_task(task_def)
    except Exception as e:
        print(f"\n--- SUPERVISOR EXECUTION ERROR ---")
        print(f"Error during task execution: {e}")
        sys.exit(1)

    # 4. Report the final result
    print("\n--- Task Complete ---")
    print(f"Outcome: {run_result.outcome}")
    print(f"Summary: {run_result.summary}")
    print("---------------------\n")


if __name__ == "__main__":
    main()
