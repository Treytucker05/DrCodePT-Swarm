"""
Trey's Agent - Fast, Learning, Research-Capable Personal Assistant

Three modes:
- EXECUTE (default): Instant playbook execution (no LLM) or Codex playbook generation for new tasks
- LEARN: Record user actions as new playbooks
- RESEARCH: Iterative deep research with refinement
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from colorama import Fore, Style, init as color_init

    color_init()
    GREEN, RED, CYAN, YELLOW, RESET = (
        Fore.GREEN,
        Fore.RED,
        Fore.CYAN,
        Fore.YELLOW,
        Style.RESET_ALL,
    )
except Exception:
    GREEN = RED = CYAN = YELLOW = RESET = ""

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent

# Ensure imports resolve to the repo-root `agent` package when run from `...\\agent`.
sys.path.insert(0, str(REPO_ROOT))


def banner() -> None:
    print(f"\n{CYAN}{'=' * 44}")
    print("                 TREY'S AGENT")
    print("            Fast | Learning | Research")
    print(f"{'=' * 44}{RESET}\n")


def show_help() -> None:
    print(
        f"""
{CYAN}TREY'S AGENT - Commands{RESET}

{GREEN}Execute mode (default):{RESET}
  Just type what you want to do.
  Examples:
    - clean my yahoo spam
    - download school files
    - create a python calculator

{GREEN}Learn mode:{RESET}
  Learn: [task name]
  Example:
    - Learn: how to download school files

{GREEN}Research mode:{RESET}
  Research: [topic]
  Example:
    - Research: best Python project structure

{GREEN}Other:{RESET}
  playbooks  - List saved playbooks
  help       - Show this help
  exit       - Quit
""".rstrip()
    )


def main() -> None:
    from agent.modes.execute import list_playbooks, load_playbooks, mode_execute
    from agent.modes.learn import mode_learn
    from agent.modes.research import mode_research

    banner()
    playbooks = load_playbooks()
    print(f"{GREEN}Ready!{RESET} {len(playbooks)} playbooks loaded.")
    print("Type 'help' for commands.\n")

    while True:
        try:
            user_input = input(f"{CYAN}>{RESET} ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return

        if not user_input:
            continue

        lower = user_input.lower().strip()
        if lower in {"exit", "quit"}:
            print("Goodbye!")
            return

        if lower == "help":
            show_help()
            continue

        if lower == "playbooks":
            list_playbooks()
            continue

        if lower.startswith("learn:"):
            task_name = user_input[6:].strip()
            if not task_name:
                print(f"{YELLOW}[INFO]{RESET} Provide a task name after 'Learn:'.")
                continue
            mode_learn(task_name)
            playbooks = load_playbooks()
            continue

        if lower.startswith("research:"):
            topic = user_input[9:].strip()
            if not topic:
                print(f"{YELLOW}[INFO]{RESET} Provide a topic after 'Research:'.")
                continue
            mode_research(topic)
            continue

        mode_execute(user_input)
        playbooks = load_playbooks()


if __name__ == "__main__":
    main()
