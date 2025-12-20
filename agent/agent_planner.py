"""
Provider-agnostic Agent Planner

Generates YAML task plans based on a natural language goal using the locally authenticated Codex CLI.
"""

import sys
from pathlib import Path

from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError, schemas as llm_schemas

# Load the planner system prompt
ROOT = Path(__file__).resolve().parent
PROMPT_FILE = ROOT / "planner_system_prompt.txt"

def load_system_prompt() -> str:
    """Load the planner system prompt from file."""
    if not PROMPT_FILE.is_file():
        print(f"Error: Planner system prompt not found at {PROMPT_FILE}")
        sys.exit(1)
    return PROMPT_FILE.read_text(encoding="utf-8")


def generate_plan(goal: str) -> str:
    """
    Generate a YAML plan using Codex CLI with a structured JSON wrapper.

    Args:
        goal: The natural language goal from the user

    Returns:
        The YAML plan as a string
    """
    system_prompt = load_system_prompt()

    try:
        llm = CodexCliClient.from_env()
        prompt = (
            "You are a planning model.\n"
            "Produce the YAML plan requested by the system prompt and wrap it in JSON as {\"yaml\": \"...\"}.\n"
            "Return JSON only.\n\n"
            f"SYSTEM_PROMPT:\n{system_prompt}\n\n"
            f"GOAL:\n{goal}\n"
        )
        data = llm.complete_json(prompt, schema_path=llm_schemas.YAML_PLAN)
        yaml_text = (data.get("yaml") or "").strip()
        if not yaml_text:
            raise ValueError("Planner returned empty YAML.")
        return yaml_text

    except Exception as e:
        print(f"Error calling Codex CLI: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the planner."""
    if len(sys.argv) < 2:
        print("Usage: python agent_planner.py \"your goal here\"")
        sys.exit(1)

    goal = " ".join(sys.argv[1:])

    try:
        _ = CodexCliClient.from_env()
    except (CodexCliNotFoundError, CodexCliAuthError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Generating plan for goal: {goal}", file=sys.stderr)
    print("[INFO] Calling Codex CLI...", file=sys.stderr)

    yaml_plan = generate_plan(goal)

    # Output the YAML plan to stdout (for piping)
    sys.stdout.write(yaml_plan)


if __name__ == "__main__":
    main()
