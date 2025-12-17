"""
Claude-Powered Agent Planner

This script uses the Claude API to generate YAML task plans based on natural language goals.
The generated plans are then executed by the custom supervisor with full verification and self-healing.
"""

import os
import sys
from pathlib import Path
from anthropic import Anthropic

# Load the planner system prompt
ROOT = Path(__file__).resolve().parent
PROMPT_FILE = ROOT / "planner_system_prompt.txt"

def load_system_prompt() -> str:
    """Load the planner system prompt from file."""
    if not PROMPT_FILE.is_file():
        print(f"Error: Planner system prompt not found at {PROMPT_FILE}")
        sys.exit(1)
    return PROMPT_FILE.read_text(encoding="utf-8")


def generate_plan(goal: str, api_key: str, model: str) -> str:
    """
    Generate a YAML plan using Claude API.

    Args:
        goal: The natural language goal from the user
        api_key: Claude API key

    Returns:
        The YAML plan as a string
    """
    client = Anthropic(api_key=api_key)
    system_prompt = load_system_prompt()

    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": goal}
            ]
        )

        # Extract text content blocks from the response
        text_blocks = [
            block.text for block in message.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        ]
        if not text_blocks:
            raise ValueError("Claude response contained no text content.")
        return "".join(text_blocks)

    except Exception as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the planner."""
    if len(sys.argv) < 2:
        print("Usage: python agent_planner.py \"your goal here\"")
        sys.exit(1)

    goal = " ".join(sys.argv[1:])

    # Get API key from environment
    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        print("Error: CLAUDE_API_KEY environment variable not set.")
        print("Please add it to your .env file.")
        sys.exit(1)

    model = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
    print(f"[INFO] Generating plan for goal: {goal}", file=sys.stderr)
    print(f"[INFO] Calling Claude API (model: {model})...", file=sys.stderr)

    yaml_plan = generate_plan(goal, api_key, model)

    # Output the YAML plan to stdout (for piping)
    sys.stdout.write(yaml_plan)


if __name__ == "__main__":
    main()
