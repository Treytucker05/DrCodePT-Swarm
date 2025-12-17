import os
import sys
import subprocess
from pathlib import Path

# Ensure imports work
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Assuming 'codex' is available on your system PATH
CODEX_CLI_COMMAND = "codex"

def run_task_from_prompt(prompt: str):
    """
    Sends a prompt to the Codex CLI (Planner) and pipes the resulting YAML
    to the local supervisor (Executor) via codex_bridge.py.
    """
    print(f"\n--- Planner: Sending Goal to Codex ---")
    print(f"Goal: {prompt}")

    # 1. Construct the command to call the Codex CLI
    # We use the --output-only flag to get only the YAML plan
    codex_command = [
        CODEX_CLI_COMMAND,
        "--dangerously-bypass-approvals-and-sandbox",
        "--search",
        "--output-only",
        prompt
    ]

    # 2. Construct the command to execute the supervisor bridge
    bridge_command = [
        sys.executable, # Use the current Python interpreter
        str(ROOT / "codex_bridge.py")
    ]

    try:
        # Execute the Codex command and pipe its output to the bridge command
        codex_process = subprocess.Popen(codex_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        bridge_process = subprocess.Popen(bridge_command, stdin=codex_process.stdout, text=True)

        # Wait for the bridge to finish execution
        bridge_process.wait()

        # Close the pipe
        codex_process.stdout.close()

        # Check for errors from the Codex process itself
        if codex_process.wait() != 0:
            stderr_output = codex_process.stderr.read()
            print(f"\n--- Codex CLI Error ---")
            print(stderr_output)
            print("-----------------------")

    except FileNotFoundError:
        print(f"\n--- ERROR: Codex CLI not found ---")
        print(f"Please ensure '{CODEX_CLI_COMMAND}' is installed and available on your system PATH.")
    except Exception as e:
        print(f"\n--- Execution Error ---")
        print(f"An unexpected error occurred: {e}")


def main():
    print("DrCodePT Autonomous Agent Console (Type 'exit' to quit)")
    while True:
        try:
            prompt = input("Goal: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nShutting down.")
            break

        if prompt.lower() in {"exit", "quit"}:
            print("Shutting down.")
            break

        if not prompt:
            continue

        run_task_from_prompt(prompt)


if __name__ == "__main__":
    main()
