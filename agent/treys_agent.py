"""
Trey's Agent - Fast, Learning, Research-Capable Personal Assistant

Three modes:
- EXECUTE (default): Instant playbook execution (no LLM) or Codex playbook generation for new tasks
- LEARN: Record user actions as new playbooks
- RESEARCH: Iterative deep research with refinement
"""

from __future__ import annotations

import os
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
  If a playbook matches, it runs instantly.
  If no playbook matches, it runs the autonomous loop (dynamic replanning).
  Examples:
    - clean my yahoo spam
    - download school files
    - create a python calculator

{GREEN}Autonomous loop (true agent):{RESET}
  Auto: [task]
  Example:
    - Auto: research autonomous AI agents

{GREEN}Credentials (encrypted):{RESET}
  Cred: <site>   - Save/update site username + password (stored encrypted)
  creds          - List credential sites saved

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
    from agent.modes.autonomous import mode_autonomous
    from agent.modes.execute import find_matching_playbook, list_playbooks, load_playbooks, mode_execute
    from agent.modes.learn import mode_learn
    from agent.modes.research import mode_research

    banner()
    playbooks = load_playbooks()
    print(f"{GREEN}Ready!{RESET} {len(playbooks)} playbooks loaded.")
    print("Type 'help' for commands.\n")

    unsafe_mode = os.getenv("AGENT_UNSAFE_MODE", "").strip().lower() in {"1", "true", "yes", "y", "on"}

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

        if lower in {"unsafe on", "unsafe_mode on", "unsafe true"}:
            unsafe_mode = True
            os.environ["AGENT_UNSAFE_MODE"] = "1"
            print(f"{YELLOW}[INFO]{RESET} unsafe_mode enabled for this session.")
            continue
        if lower in {"unsafe off", "unsafe_mode off", "unsafe false"}:
            unsafe_mode = False
            os.environ.pop("AGENT_UNSAFE_MODE", None)
            print(f"{YELLOW}[INFO]{RESET} unsafe_mode disabled for this session.")
            continue

        if lower in {"creds", "credentials"}:
            try:
                from agent.memory.memory_manager import load_memory

                sites = sorted((load_memory().get("credentials") or {}).keys())
                if not sites:
                    print(f"{YELLOW}[INFO]{RESET} No credential sites saved yet.")
                else:
                    print(f"{CYAN}Saved credential sites:{RESET} " + ", ".join(sites))
            except Exception as exc:
                print(f"{RED}[ERROR]{RESET} Failed to list credentials: {exc}")
            continue

        if lower.startswith("cred:") or lower.startswith("credentials:"):
            site = user_input.split(":", 1)[1].strip().lower()
            if not site:
                print(f"{YELLOW}[INFO]{RESET} Usage: Cred: <site>  (example: Cred: yahoo)")
                continue

            try:
                import getpass

                from agent.memory.credentials import CredentialError, save_credential

                print(f"{CYAN}[CREDENTIALS]{RESET} Saving encrypted credentials for: {site}")
                username = input(f"{CYAN}Username/email:{RESET} ").strip()
                password = getpass.getpass("Password (input hidden): ").strip()

                if not username or not password:
                    print(f"{YELLOW}[INFO]{RESET} Username/password cannot be blank.")
                    continue

                cred_id = save_credential(site, username, password)
                print(f"{GREEN}[SAVED]{RESET} Stored encrypted credentials for '{site}' (id={cred_id}).")
                print(f"{YELLOW}[NOTE]{RESET} Passwords are not recorded from browser typing; they are stored here and filled at runtime.")
            except CredentialError as exc:
                print(f"{RED}[ERROR]{RESET} {exc}")
            except Exception as exc:
                print(f"{RED}[ERROR]{RESET} Failed to save credentials: {exc}")
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

        if lower.startswith("auto:") or lower.startswith("loop:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Auto:'.")
                continue
            mode_autonomous(task, unsafe_mode=unsafe_mode)
            continue

        # Default: run a matching playbook; otherwise run the true autonomous loop.
        pb_id, pb_data = find_matching_playbook(user_input, playbooks)
        if pb_data:
            mode_execute(user_input)
            playbooks = load_playbooks()
            continue

        mode_autonomous(user_input, unsafe_mode=unsafe_mode)


if __name__ == "__main__":
    main()
