"""
Trey's Agent - Fast, Learning, Research-Capable Personal Assistant

Three modes:
- EXECUTE (default): Instant playbook execution (no LLM) or Codex playbook generation for new tasks
- LEARN: Record user actions as new playbooks
- RESEARCH: Iterative deep research with refinement
"""

from __future__ import annotations

import os
import re
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

{GREEN}Mail (supervised):{RESET}
  Mail: [request]
  Example:
    - Mail: review my Yahoo inbox and suggest rules

{GREEN}Collab (interactive planning):{RESET}
  Natural language that includes "plan", "organize", "strategy", etc. will route here automatically.
  You can still force it with:
    Collab: [goal]
  Example:
    - I want a plan to reorganize my Yahoo folders and clean rules

{GREEN}Smart mode selection:{RESET}
  If a request could be either research or execution, the agent will ask which you want.
  You can still force research with "Research:" (and pick light/moderate/deep when prompted).

{GREEN}Credentials (startup prompt):{RESET}
  If configured, the agent can prompt for credentials at startup to enable auto-login.
  Set TREYS_AGENT_CRED_PROMPT_SITES="site1,site2" to control which sites to ask for.

{GREEN}Routing defaults:{RESET}
  - If ambiguous, defaults to Execute (change with TREYS_AGENT_DEFAULT_MODE=collab|research|execute).
  - Set TREYS_AGENT_PROMPT_ON_AMBIGUOUS=1 to show a mode picker.

{GREEN}Other:{RESET}
  playbooks  - List saved playbooks
  help       - Show this help
  exit       - Quit
""".rstrip()
    )    


_RESEARCH_KEYWORDS = {
    "research",
    "compare",
    "comparison",
    "overview",
    "explain",
    "analysis",
    "review",
    "recommend",
    "recommendations",
    "best",
    "top",
    "pros",
    "cons",
    "advantages",
    "disadvantages",
    "latest",
    "current",
    "sources",
    "citations",
    "evidence",
    "report",
    "guide",
    "tutorial",
    "learn",
}

_RESEARCH_PHRASES = {
    "what is",
    "how does",
    "how do",
    "what's",
    "pros and cons",
    "pros & cons",
}

_COLLAB_KEYWORDS = {
    "plan",
    "planning",
    "strategy",
    "roadmap",
    "outline",
    "organize",
    "organizing",
    "structure",
    "brainstorm",
    "prioritize",
    "priorities",
    "decide",
    "decision",
    "workflow",
    "next",
    "steps",
    "approach",
}

_COLLAB_PHRASES = {
    "come up with a plan",
    "help me plan",
    "organize my thoughts",
    "break this down",
    "step by step plan",
    "step-by-step plan",
    "master plan",
    "what should we do",
    "how should we",
}

_EXEC_KEYWORDS = {
    "login",
    "signin",
    "open",
    "download",
    "upload",
    "install",
    "uninstall",
    "delete",
    "remove",
    "clean",
    "organize",
    "sort",
    "move",
    "rename",
    "create",
    "edit",
    "update",
    "send",
    "email",
    "schedule",
    "book",
    "buy",
    "order",
    "run",
    "execute",
    "build",
    "deploy",
    "configure",
    "fill",
    "submit",
    "check",
    "list",
    "scan",
}

_EXEC_PHRASES = {
    "log in",
    "sign in",
    "check my",
    "check the",
}

_DEFAULT_CRED_PROMPT_SITES = ["yahoo", "yahoo_imap"]


def _score_intent(text: str, keywords: set[str], phrases: set[str]) -> int:
    lowered = text.lower()
    score = 0
    for phrase in phrases:
        if phrase in lowered:
            score += 2
    tokens = re.findall(r"[a-z0-9']+", lowered)
    for token in tokens:
        if token in keywords:
            score += 1
    return score


def _infer_intent(text: str) -> str:
    lowered = text.lower().strip()
    if lowered.startswith("research:"):
        return "research"
    if lowered.startswith("collab:"):
        return "collab"
    if lowered.startswith("auto:") or lowered.startswith("loop:") or lowered.startswith("learn:") or lowered.startswith("cred:") or lowered.startswith("credentials:"):
        return "execute"

    research_score = _score_intent(text, _RESEARCH_KEYWORDS, _RESEARCH_PHRASES)
    collab_score = _score_intent(text, _COLLAB_KEYWORDS, _COLLAB_PHRASES)
    exec_score = _score_intent(text, _EXEC_KEYWORDS, _EXEC_PHRASES)

    if "research" in lowered or "citations" in lowered or "sources" in lowered:
        research_score += 2

    if collab_score >= 2 and collab_score > max(research_score, exec_score):
        return "collab"
    if research_score >= 2 and research_score > max(collab_score, exec_score):
        return "research"
    if exec_score >= 2 and exec_score > max(collab_score, research_score):
        return "execute"
    if collab_score > 0 and (research_score > 0 or exec_score > 0):
        return "ambiguous"
    if research_score > 0 and collab_score == 0 and exec_score == 0:
        return "research"
    if collab_score > 0 and research_score == 0 and exec_score == 0:
        return "collab"
    if exec_score > 0 and research_score == 0 and collab_score == 0:
        return "execute"
    return "ambiguous"


def _prompt_mode_choice() -> tuple[str, str | None]:
    prompt = (
        f"{YELLOW}[PROMPT]{RESET} Does this request need research or execution?\n"
        "  1) Research (light / moderate / deep)\n"
        "  2) Execute a task\n"
        "  3) Collab (organize thoughts + plan)\n"
        f"{CYAN}Choose 1/2/3 (default 2). You can also type light/balanced/deep:{RESET} "
    )
    choice = input(prompt).strip().lower()
    if not choice:
        return "execute", None

    depth_map = {
        "light": "light",
        "l": "light",
        "balanced": "balanced",
        "b": "balanced",
        "moderate": "balanced",
        "m": "balanced",
        "deep": "deep",
        "d": "deep",
    }

    if choice in {"1", "research", "r"}:
        return "research", None
    if choice in {"2", "execute", "exec", "e"}:
        return "execute", None
    if choice in {"3", "collab", "c", "plan"}:
        return "collab", None
    if choice in depth_map:
        return "research", depth_map[choice]

    # Fallback: treat unknown input as execute to avoid accidental long research runs.
    return "execute", None


def _prompt_startup_credentials() -> None:
    try:
        import getpass

        from agent.memory.credentials import CredentialError, get_credential, save_credential
        from agent.memory.memory_manager import load_memory, save_memory
    except Exception:
        return

    env_sites = (os.getenv("TREYS_AGENT_CRED_PROMPT_SITES") or "").strip()
    if env_sites:
        sites = [s.strip().lower() for s in env_sites.split(",") if s.strip()]
    else:
        sites = list(_DEFAULT_CRED_PROMPT_SITES)

    if not sites:
        return

    memory = load_memory()
    prefs = memory.get("preferences") or {}
    skips = set(prefs.get("credential_prompt_skip") or [])

    missing = [s for s in sites if s not in skips and not get_credential(s)]
    if not missing:
        return

    print(
        f"{YELLOW}[CREDENTIALS]{RESET} Missing saved credentials for: "
        + ", ".join(missing)
    )
    print(
        f"{YELLOW}[NOTE]{RESET} For Google services (Gmail/Tasks/Calendar), OAuth is recommended and does not require a password."
    )

    for site in missing:
        ans = input(
            f"{CYAN}Save credentials for '{site}' now? (y/n/skip):{RESET} "
        ).strip().lower()
        if ans in {"skip", "s"}:
            skips.add(site)
            continue
        if ans not in {"y", "yes"}:
            continue

        try:
            username = input(f"{CYAN}Username/email for {site}:{RESET} ").strip()
            password = getpass.getpass(f"Password for {site} (input hidden): ").strip()
            if not username or not password:
                print(f"{YELLOW}[INFO]{RESET} Skipping {site}: username/password cannot be blank.")
                continue
            save_credential(site, username, password)
            print(f"{GREEN}[SAVED]{RESET} Stored encrypted credentials for '{site}'.")
        except CredentialError as exc:
            print(f"{RED}[ERROR]{RESET} {exc}")
        except Exception as exc:
            print(f"{RED}[ERROR]{RESET} Failed to save credentials for {site}: {exc}")

    if skips:
        prefs["credential_prompt_skip"] = sorted(skips)
        memory["preferences"] = prefs
        save_memory(memory)


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
    _prompt_startup_credentials()

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

        if lower.startswith("mail:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Mail:'.")
                continue
            from agent.modes.mail_supervised import run_mail_supervised

            run_mail_supervised(task)
            continue

        if lower.startswith("collab:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a goal after 'Collab:'.")
                continue
            from agent.modes.collab import run_collab_session

            run_collab_session(task)
            continue

        intent = _infer_intent(user_input)
        if intent == "ambiguous":
            if os.getenv("TREYS_AGENT_PROMPT_ON_AMBIGUOUS", "").strip().lower() in {"1", "true", "yes", "y", "on"}:
                chosen, depth = _prompt_mode_choice()
                intent = chosen
                if depth:
                    os.environ["TREYS_AGENT_RESEARCH_MODE"] = depth
            else:
                default_mode = (os.getenv("TREYS_AGENT_DEFAULT_MODE") or "execute").strip().lower()
                if default_mode not in {"execute", "research", "collab"}:
                    default_mode = "execute"
                intent = default_mode

        if intent == "research":
            mode_research(user_input)
            continue

        # Default: run a matching playbook; otherwise run the true autonomous loop.
        pb_id, pb_data = find_matching_playbook(user_input, playbooks)
        if pb_data:
            status = mode_execute(user_input)
            playbooks = load_playbooks()
            if status == "failed":
                print(f"{YELLOW}[INFO]{RESET} Playbook failed; falling back to Auto mode.")
                mode_autonomous(user_input, unsafe_mode=unsafe_mode)
            continue

        mode_autonomous(user_input, unsafe_mode=unsafe_mode)


if __name__ == "__main__":
    main()
