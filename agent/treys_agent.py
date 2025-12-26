"""
Trey's Agent - Fast, Learning, Research-Capable Personal Assistant
Default behavior: chat-only (no tool execution).
Modes: Execute, Learn, Research, Auto, Plan, Team, Swarm, Think, Mail.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict

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

from agent.modes.execute import find_matching_playbook, load_playbooks


def banner() -> None:
    print(f"\n{CYAN}{'=' * 44}")
    print("                 TREY'S AGENT")
    print("            Fast | Learning | Research")
    print(f"{'=' * 44}{RESET}\n")


def show_help() -> None:
    print(
        f"""
{CYAN}TREY'S AGENT - Commands{RESET}

{GREEN}Chat mode (default):{RESET}
  Just type what you want to say.
  The agent will respond conversationally without running tools.
  To run tools, use Execute:, Auto:, Plan:, Team:, Swarm:, Mail:, or Learn: prefixes.
  Or just ask for a task and the agent will auto-route to the best mode.
  Examples:
    - clean my yahoo spam
    - download school files
    - create a python calculator

{GREEN}Execute mode (quick actions):{RESET}
  Execute: [task]  - Runs quick actions/playbooks without long loops
  Example:
    - Execute: open my PT School folder

{GREEN}Autonomous loop (explicit):{RESET}
  Auto: [task]  - Runs the tool loop with replanning
  Example:
    - Auto: research autonomous AI agents

{GREEN}Swarm mode (parallel sub-agents):{RESET}
  Swarm: [task]  - Splits work into subtasks and runs them in parallel
  Example:
    - Swarm: compare 3 CRMs and summarize pros/cons

{GREEN}Enhanced Autonomous (Self-Healing):{RESET}
  Plan: [task]   - Creates execution plan, then runs with error recovery
  Example:
    - Plan: setup Google Tasks API and test it
    - Plan: consolidate my Yahoo folders and create rules

{GREEN}Supervisor Team Mode:{RESET}
  Team: [task]   - Runs observe->research->plan->execute->verify->reflect loop
  Example:
    - Team: audit my project and propose fixes

{GREEN}Think Mode (no tool execution):{RESET}
  Think: [task]  - Iterative planning/refinement without executing tools
  Example:
    - Think: design a migration plan for the repo

{GREEN}Issue Tracking:{RESET}
  issues         - List all tracked issues
  issues open    - List open issues
  issues resolved - List resolved issues

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

{GREEN}Mail (intelligent assistant):{RESET}
  Natural language about organizing mail/email/folders will route here automatically.
  The agent will understand your request and help you conversationally.

  You can still force it with:
    Mail: [request]
    Mail task: [request]

  Examples:
    - organize my yahoo mail folders
    - clean my yahoo inbox
    - I need help organizing my email
    - Mail task: Continue consolidation using saved rule deliveries_to_shopping_online_small_merge...

  The agent will ask questions, understand your goals, and execute actions as needed.
  {YELLOW}Advanced:{RESET} Set MAIL_USE_WORKFLOW=1 for the structured workflow mode.

{GREEN}Collaborative Planning:{RESET}
  Collab: [goal]  - Interactive planning with Q&A before execution
  Example:
    - Collab: organize my downloads folder

{GREEN}Smart mode selection:{RESET}
  If a request could be either research or execution, the agent will ask which you want.
  You can still force research with "Research:" (and pick light/moderate/deep when prompted).

{GREEN}Credentials (startup prompt):{RESET}
  If configured, the agent can prompt for credentials at startup to enable auto-login.
  Set TREYS_AGENT_CRED_PROMPT_SITES="site1,site2" to control which sites to ask for.

{GREEN}Routing defaults:{RESET}
  - Chat-only is default; nothing runs unless you approve it.
  - When you approve a task with "yes", the agent uses TREYS_AGENT_DEFAULT_MODE (default: execute).
  - Set TREYS_AGENT_PROMPT_ON_AMBIGUOUS=1 to show a mode picker.

{GREEN}Other:{RESET}
  menu       - Show full capability menu
  grade      - Grade the last run (trace evaluation)
  connect    - Connect to an MCP server (e.g., Connect: github)
  mcp list   - List tools from the active MCP server
  resume     - Resume the most recent run
  maintenance - Summarize recent runs and update memory
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

_MAIL_KEYWORDS = {
    "mail",
    "email",
    "inbox",
    "folder",
    "folders",
    "spam",
    "organize",
    "clean",
    "yahoo",
    "gmail",
}
_MAIL_EXPLICIT_KEYWORDS = {"mail", "email", "inbox", "gmail", "yahoo"}

_MAIL_PHRASES = {
    "organize my mail",
    "organize my email",
    "clean my mail",
    "clean my email",
    "clean my inbox",
    "organize my inbox",
    "mail folders",
    "email folders",
    "yahoo mail",
    "yahoo inbox",
    "gmail inbox",
}

_MAIL_PREFIX_RE = re.compile(
    r"^(mail(?:\s*-?\s*task)?|mailtask)\s*:\s*(.*)$",
    re.IGNORECASE,
)

_DEFAULT_CRED_PROMPT_SITES = ["yahoo", "yahoo_imap"]

_SIMPLE_QUESTION_PATTERNS = {
    "do you have",
    "do i have",
    "is installed",
    "is there",
    "can you",
    "can i",
    "where is",
    "what is",
    "how do i",
    "how can i",
}

_EXECUTE_PREFIXES = (
    "auto:",
    "plan:",
    "research:",
    "collab:",
    "mail:",
    "mail task:",
    "team:",
    "think:",
    "swarm:",
)
_MODE_SWITCH_PHRASES = (
    "different mode",
    "switch mode",
    "change mode",
    "another mode",
    "mode switch",
    "go into a different mode",
    "go into another mode",
    "enter a different mode",
    "enter another mode",
)

_APPROACH_LABELS = {
    "collab": "Collab (talk it through + plan)",
    "execute": "Execute (do the task)",
    "research": "Research (sources + analysis)",
    "auto": "Auto (hands-off execution)",
    "swarm": "Swarm (parallel sub-agents)",
}

_ACTION_VERBS = {
    "open",
    "show",
    "bring",
    "pull",
    "launch",
    "start",
    "run",
    "execute",
    "download",
    "upload",
    "install",
    "uninstall",
    "delete",
    "remove",
    "move",
    "rename",
    "create",
    "edit",
    "update",
    "clean",
    "organize",
    "sort",
    "scan",
    "search",
    "find",
    "copy",
    "paste",
    "click",
    "double",
}

_CONFIRM_WORDS = {
    "yes",
    "y",
    "yeah",
    "yep",
    "sure",
    "ok",
    "okay",
    "do it",
    "go ahead",
    "proceed",
    "run it",
}


def _confirm_execution(prompt: str) -> bool:
    choice = input(prompt).strip().lower()
    return choice in {"y", "yes", "sure", "ok", "okay", "run", "do it", "doit"}


def _should_confirm(user_input: str) -> bool:
    val = (os.getenv("TREYS_AGENT_CONFIRM_EXECUTION") or "1").strip().lower()
    if val in {"0", "false", "no", "off"}:
        return False
    lowered = user_input.strip().lower()
    return not lowered.startswith(_EXECUTE_PREFIXES)


def _is_simple_question(text: str) -> bool:
    lowered = text.lower().strip()
    if not lowered.endswith("?"):
        return False

    # Check if it's a complex task request (mail, research, etc.)
    # These should NOT be treated as simple questions
    mail_score = _score_intent(text, _MAIL_KEYWORDS, _MAIL_PHRASES)
    research_score = _score_intent(text, _RESEARCH_KEYWORDS, _RESEARCH_PHRASES)
    collab_score = _score_intent(text, _COLLAB_KEYWORDS, _COLLAB_PHRASES)
    exec_score = _score_intent(text, _EXEC_KEYWORDS, _EXEC_PHRASES)

    if mail_score > 0 or research_score > 0 or collab_score > 0 or exec_score > 0:
        return False

    for pattern in _SIMPLE_QUESTION_PATTERNS:
        if pattern in lowered:
            return True

    if lowered.startswith("is ") and "installed" in lowered:
        return True
    if lowered.startswith("are ") and "installed" in lowered:
        return True

    return False


def _is_capability_query(text: str) -> bool:
    lowered = text.strip().lower()
    triggers = {
        "what can you help me with",
        "what can you do",
        "capabilities",
        "tools",
        "show tools",
        "what tools do you have",
    }
    if lowered in triggers:
        return True
    return any(trigger in lowered for trigger in triggers if len(trigger.split()) > 1)


def _is_mode_switch_request(text: str) -> bool:
    lowered = text.lower().strip()
    if any(phrase in lowered for phrase in _MODE_SWITCH_PHRASES):
        return True
    return lowered in {"mode", "modes", "switch modes", "change modes"}


def _parse_mode_request(text: str) -> str | None:
    lowered = text.lower().strip()
    if "swarm" in lowered:
        return "swarm"
    if "team" in lowered:
        return "team"
    if "auto" in lowered:
        return "auto"
    if "plan" in lowered:
        return "plan"
    if "mail" in lowered:
        return "mail"
    if "research" in lowered:
        return "research"
    if "execute" in lowered or "exec" in lowered:
        return "execute"
    return None


def _is_confirm(text: str) -> bool:
    lowered = text.lower().strip()
    if lowered in _CONFIRM_WORDS:
        return True
    return any(word in lowered for word in _CONFIRM_WORDS)


def _looks_like_action_request(text: str) -> bool:
    lowered = text.lower().strip()
    if any(phrase in lowered for phrase in ("can you", "could you", "please", "i need you to", "i want you to")):
        return True
    tokens = set(re.findall(r"[a-z0-9']+", lowered))
    if tokens & _ACTION_VERBS:
        return True
    exec_score = _score_intent(text, _EXEC_KEYWORDS, _EXEC_PHRASES)
    return exec_score > 0


def _run_capabilities() -> None:
    from agent.autonomous.help.capabilities import build_capabilities_response

    print(build_capabilities_response())


def _run_chat(user_input: str, history: list[tuple[str, str]]) -> None:
    from agent.context_loader import format_context_for_llm
    from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
    from agent.llm import schemas as llm_schemas

    try:
        llm = CodexCliClient.from_env()
    except CodexCliNotFoundError as exc:
        print(f"{RED}[ERROR]{RESET} {exc}")
        return
    except CodexCliAuthError as exc:
        print(f"{RED}[ERROR]{RESET} {exc}")
        return

    def _render_history(items: list[tuple[str, str]], limit: int = 6) -> str:
        lines = []
        for role, text in items[-limit:]:
            lines.append(f"{role}: {text}")
        return "\n".join(lines)

    context = format_context_for_llm()
    convo = _render_history(history)
    prompt = (
        "You are Trey's Agent in chat-only mode.\n"
        "Do NOT execute tools or run commands. Just talk.\n"
        "If the user asks to do something, ask a clarifying question or suggest a mode\n"
        "(Auto/Plan/Team/Mail) instead of executing.\n"
        "If a playbook seems relevant, you may mention it and ask for confirmation,\n"
        "but do not execute it.\n\n"
        f"{context}\n\n"
        "Conversation so far:\n"
        f"{convo}\n\n"
        f"User: {user_input}\n\n"
        "Return JSON with fields: response (string) and action (type none).\n"
        'Set action to {"type":"none","folder":null}.\n'
    )

    data = llm.reason_json(prompt, schema_path=llm_schemas.CHAT_RESPONSE)
    if isinstance(data, dict):
        response = (data.get("response") or "").strip()
        if response:
            print(response)
            history.append(("assistant", response))
            return
    print(f"{YELLOW}[INFO]{RESET} I didn't get a response. Try again.")


def _show_menu() -> None:
    from agent.context_loader import build_context_summary
    from agent.modes.execute import load_playbooks

    ctx = build_context_summary()
    manual_playbooks = load_playbooks()

    print("\nMENU")
    print("====")
    print("Default behavior: chat-only (no tools).")
    print("")
    print("Modes (prefix to force):")
    print("- Execute: run quick actions/playbooks")
    print("- Auto: run the tool-using agent loop")
    print("- Swarm: run parallel sub-agents")
    print("- Plan: plan first, then execute")
    print("- Team: observe -> research -> plan -> execute -> verify -> reflect")
    print("- Think: plan only (no tools)")
    print("- Research: sources + summary")
    print("- Mail: email workflows")
    print("- Learn: record a playbook")
    print("")
    print("Quick commands:")
    print("- help, menu, playbooks, creds, issues, unsafe on/off, exit")
    print("- connect: <server>, mcp list, resume, maintenance")
    print("")
    print("Status:")
    creds = ctx.get("credentials") or []
    tools = ctx.get("tools") or []
    learned = ctx.get("playbooks") or []
    print(f"- Credentials saved: {len(creds)}")
    if creds:
        print("  " + ", ".join(creds[:8]) + ("..." if len(creds) > 8 else ""))
    print(f"- Tools available: {len(tools)}")
    if tools:
        print("  " + ", ".join(tools))
    print(f"- Playbooks (manual): {len(manual_playbooks)}")
    if manual_playbooks:
        names = [pb.get("name", k) for k, pb in list(manual_playbooks.items())[:8]]
        print("  " + ", ".join(names) + ("..." if len(manual_playbooks) > 8 else ""))
    print(f"- Playbooks (learned): {len(learned)}")
    recent = ctx.get("recent_tasks") or []
    if recent:
        print("- Recent tasks:")
        for task in recent[:3]:
            name = task.get("name", "")
            goal = task.get("goal", "")
            print(f"  - {name}: {goal[:60]}")


def _suggest_mode(text: str) -> tuple[str, str]:
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z0-9']+", lowered))
    mail_explicit = bool(tokens & _MAIL_EXPLICIT_KEYWORDS)
    mail_score = _score_intent(text, _MAIL_KEYWORDS, _MAIL_PHRASES)
    research_score = _score_intent(text, _RESEARCH_KEYWORDS, _RESEARCH_PHRASES)
    collab_score = _score_intent(text, _COLLAB_KEYWORDS, _COLLAB_PHRASES)
    exec_score = _score_intent(text, _EXEC_KEYWORDS, _EXEC_PHRASES)

    if "research" in lowered or "sources" in lowered or "citations" in lowered:
        research_score += 2

    if mail_explicit and mail_score >= max(research_score, collab_score, exec_score) and mail_score > 0:
        return "mail", "you mentioned email-related wording"
    if research_score >= max(collab_score, exec_score) and research_score > 0:
        return "research", "this looks like a request for information or comparisons"
    if collab_score >= exec_score and collab_score > 0:
        return "collab", "this sounds like planning or organizing"
    if exec_score > 0:
        return "execute", "this sounds like a task you want done"
    return "collab", "a short back-and-forth will help clarify the goal"


def _prompt_mode_with_suggestion(user_input: str) -> tuple[str, str | None]:
    suggestion, reason = _suggest_mode(user_input)
    if suggestion == "mail":
        return "mail", None

    print(f"{YELLOW}[SUGGEST]{RESET} I think this fits: {suggestion} ({reason}).")
    prompt = (
        f"{YELLOW}[PROMPT]{RESET} Choose an approach:\n"
        f"  1) {_APPROACH_LABELS['collab']}\n"
        f"  2) {_APPROACH_LABELS['execute']}\n"
        f"  3) {_APPROACH_LABELS['research']}\n"
        f"  4) {_APPROACH_LABELS['auto']} (opt-in)\n"
        f"{CYAN}Choose 1/2/3/4 (default {suggestion}). You can also type the word:{RESET} "
    )
    choice = input(prompt).strip().lower()
    if not choice:
        return suggestion, None

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

    if choice in {"1", "collab", "plan"}:
        return "collab", None
    if choice in {"2", "execute", "exec"}:
        return "execute", None
    if choice in {"3", "research", "r"}:
        return "research", None
    if choice in {"4", "auto"}:
        return "auto", None
    if choice in depth_map:
        return "research", depth_map[choice]

    return suggestion, None


def _handle_simple_question(text: str) -> None:
    lowered = text.lower().strip()

    if "installed" in lowered:
        import subprocess
        query = text.replace("?", "").strip()
        for prefix in ["is", "are"]:
            if query.lower().startswith(prefix):
                query = query[len(prefix):].strip()
        if query.lower().endswith("installed"):
            query = query[:-9].strip()

        print(f"{CYAN}[QUERY]{RESET} Checking if '{query}' is installed...")
        try:
            result = subprocess.run(
                ["pip", "show", query],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                version_line = next((l for l in lines if l.startswith("Version:")), None)
                version = version_line.split(":", 1)[1].strip() if version_line else "unknown"
                print(f"{GREEN}[YES]{RESET} {query} is installed (version {version})")
            else:
                result2 = subprocess.run(
                    ["which", query] if sys.platform != "win32" else ["where", query],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result2.returncode == 0:
                    print(f"{GREEN}[YES]{RESET} {query} is installed at: {result2.stdout.strip()}")
                else:
                    print(f"{YELLOW}[NO]{RESET} {query} is not installed.")
        except Exception as exc:
            print(f"{RED}[ERROR]{RESET} Could not check installation: {exc}")
    elif "do you have" in lowered or "do i have" in lowered:
        package_query = text.replace("?", "").strip()
        for prefix in ["do you have", "do i have"]:
            if prefix in lowered:
                package_query = package_query[len(prefix):].strip()
                break

        if package_query:
            print(f"{CYAN}[QUERY]{RESET} Checking for '{package_query}'...")
            try:
                import subprocess
                result = subprocess.run(
                    ["pip", "show", package_query],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    version_line = next((l for l in lines if l.startswith("Version:")), None)
                    version = version_line.split(":", 1)[1].strip() if version_line else "unknown"
                    print(f"{GREEN}[YES]{RESET} {package_query} is installed (version {version})")
                else:
                    print(f"{YELLOW}[NO]{RESET} {package_query} is not installed.")
                    print(f"{CYAN}[TIP]{RESET} To install it, run: pip install {package_query}")
            except Exception as exc:
                print(f"{RED}[ERROR]{RESET} Could not check package: {exc}")
        else:
            print(f"{CYAN}[QUERY]{RESET} I'm an agent that can help you execute tasks, research topics, or plan strategies.")
            print(f"{CYAN}[QUERY]{RESET} Type 'help' for available commands.")
    elif "where is" in lowered:
        import subprocess
        query = text.replace("?", "").strip()
        print(f"{CYAN}[QUERY]{RESET} Searching for location...")
        try:
            result = subprocess.run(
                ["find", "/", "-name", query.split()[-1], "-type", "f"] if sys.platform != "win32" else ["where", query.split()[-1]],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout.strip():
                print(f"{GREEN}[FOUND]{RESET} {result.stdout.strip()}")
            else:
                print(f"{YELLOW}[NOT FOUND]{RESET} Could not locate {query.split()[-1]}.")
        except Exception as exc:
            print(f"{RED}[ERROR]{RESET} Search failed: {exc}")
    else:
        print(f"{CYAN}[QUERY]{RESET} {text}")
        print(f"{YELLOW}[INFO]{RESET} For detailed answers, try 'Research: {text.rstrip('?')}'")


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
    if lowered.startswith("mail:"):
        return "mail"
    if lowered.startswith("auto:") or lowered.startswith("loop:") or lowered.startswith("learn:") or lowered.startswith("cred:") or lowered.startswith("credentials:"):
        return "execute"

    mail_score = _score_intent(text, _MAIL_KEYWORDS, _MAIL_PHRASES)
    research_score = _score_intent(text, _RESEARCH_KEYWORDS, _RESEARCH_PHRASES)
    collab_score = _score_intent(text, _COLLAB_KEYWORDS, _COLLAB_PHRASES)
    exec_score = _score_intent(text, _EXEC_KEYWORDS, _EXEC_PHRASES)

    if "research" in lowered or "citations" in lowered or "sources" in lowered:
        research_score += 2

    if mail_score >= 3:
        return "mail"
    if collab_score >= 2 and collab_score > max(research_score, exec_score, mail_score):
        return "collab"
    if research_score >= 2 and research_score > max(collab_score, exec_score, mail_score):
        return "research"
    if exec_score >= 2 and exec_score > max(collab_score, research_score, mail_score):
        return "execute"
    if collab_score > 0 and (research_score > 0 or exec_score > 0):
        return "ambiguous"
    if research_score > 0 and collab_score == 0 and exec_score == 0 and mail_score == 0:
        return "research"
    if collab_score > 0 and research_score == 0 and exec_score == 0 and mail_score == 0:
        return "collab"
    if exec_score > 0 and research_score == 0 and collab_score == 0 and mail_score == 0:
        return "execute"
    return "ambiguous"


def _extract_mail_objective(text: str) -> str | None:
    match = _MAIL_PREFIX_RE.match(text.strip())
    if not match:
        return None
    return match.group(2).strip()


def _run_mail_guided(objective: str) -> int:
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    if "PYTHONPATH" in env and env["PYTHONPATH"]:
        env["PYTHONPATH"] = str(repo_root) + os.pathsep + env["PYTHONPATH"]
    else:
        env["PYTHONPATH"] = str(repo_root)

    cmd = [
        sys.executable,
        "-m",
        "agent.autonomous.modes.mail_guided",
        "--objective",
        objective,
    ]
    result = subprocess.run(cmd, check=False, cwd=str(repo_root), env=env)
    if result.returncode != 0:
        check = subprocess.run(
            [
                sys.executable,
                "-c",
                "import agent.autonomous.modes.mail_guided as _m",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            env=env,
        )
        combined = (check.stdout or "") + (check.stderr or "")
        if "ModuleNotFoundError" in combined:
            print(
                f"{RED}[ERROR]{RESET} Mail workflow failed to import. "
                f"cwd={repo_root} python={sys.executable}"
            )
            print(
                f"{YELLOW}[INFO]{RESET} PYTHONPATH="
                f"{env.get('PYTHONPATH', '')}"
            )
            print(
                f"{YELLOW}[INFO]{RESET} Try running from the repo root or "
                "ensure PYTHONPATH includes the repo root."
            )
    return result.returncode


def _maybe_route_mail(user_input: str, *, intent: str | None = None) -> bool:
    objective = _extract_mail_objective(user_input)
    if objective is not None:
        if not objective:
            print(
                f"{YELLOW}[INFO]{RESET} Provide a task after 'Mail:' "
                "or 'Mail task:'."
            )
            return True
        _run_mail_guided(objective)
        return True
        _run_mail_guided(user_input)
        return True
    return False


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


def assess_task_complexity(user_input: str) -> str:
    """
    Analyze user input to determine if collaborative planning is needed.
    Returns: "collaborative" or "execute"
    """
    user_lower = user_input.lower().strip()

    # High ambiguity signals - needs collaboration
    ambiguous_keywords = [
        "organize",
        "clean",
        "improve",
        "optimize",
        "fix up",
        "better way",
        "help me with",
        "figure out",
        "plan",
    ]

    # Clear/specific signals - can execute directly
    clear_keywords = [
        "search for",
        "find",
        "list",
        "show me",
        "calculate",
        "what is",
        "how many",
        "tell me",
        "explain",
    ]

    # Check for ambiguous signals
    if any(keyword in user_lower for keyword in ambiguous_keywords):
        return "collaborative"

    # Check for clear signals
    if any(keyword in user_lower for keyword in clear_keywords):
        return "execute"

    # Default: if user input is short and specific, execute
    # If longer and open-ended, collaborate
    word_count = len(user_input.split())
    if word_count <= 5:
        return "execute"
    return "collaborative"


def smart_orchestrator(user_input: str) -> Dict[str, Any]:
    """
    Intelligent router that decides execution mode autonomously.
    Returns: {"mode": str, "reason": str, "auto_execute": bool}
    """
    lower = user_input.lower().strip()

    # TIER 1: Simple read-only queries (auto-execute immediately)
    if _is_simple_filesystem_query(user_input):
        return {
            "mode": "execute",
            "reason": "Simple filesystem query",
            "auto_execute": True,
        }

    # TIER 2: Playbook matches (if score high enough, use it)
    playbook_name, playbook_data = find_matching_playbook(
        user_input, load_playbooks()
    )
    if playbook_name and playbook_data:
        return {
            "mode": "execute",
            "reason": f"Matched playbook: {playbook_name}",
            "auto_execute": True,
            "playbook": playbook_name,
        }

    # TIER 3: Deep analysis/research tasks (swarm mode)
    swarm_keywords = [
        "audit",
        "analyze",
        "research",
        "investigate",
        "compare",
        "find improvements",
        "identify gaps",
        "review code",
        "deep dive",
        "comprehensive analysis",
    ]
    if any(kw in lower for kw in swarm_keywords):
        return {
            "mode": "swarm",
            "reason": "Complex analysis requiring parallel research",
            "auto_execute": False,  # Ask for swarm confirmation
        }

    # TIER 4: Ambiguous tasks (collaborative planning)
    ambiguous_keywords = [
        "organize",
        "clean up",
        "improve",
        "optimize",
        "fix",
        "better way",
        "help me with",
    ]
    if any(kw in lower for kw in ambiguous_keywords):
        return {
            "mode": "collaborative",
            "reason": "Ambiguous task needs clarification",
            "auto_execute": True,
        }

    # TIER 5: Action requests (default to execute)
    if _looks_like_action_request(user_input):
        return {
            "mode": "execute",
            "reason": "Standard action request",
            "auto_execute": True,
        }

    # TIER 6: Conversational (chat only)
    return {
        "mode": "chat",
        "reason": "Conversational query",
        "auto_execute": True,
    }


def _is_simple_filesystem_query(user_input: str) -> bool:
    """Detect simple read-only filesystem queries that don't need confirmation."""
    lower = user_input.lower()

    # Read-only filesystem operations
    readonly_patterns = [
        "list files",
        "show files",
        "list directories",
        "show directories",
        "read file",
        "show file",
        "search for files",
        "find files",
    ]

    # Path indicators (if present, likely filesystem query)
    has_path = any(
        p in lower
        for p in [":\\", "downloads", "documents", "desktop", "/users/", "/home/"]
    )

    # If has read-only pattern OR (has "list"/"show" AND has path)
    if any(pattern in lower for pattern in readonly_patterns):
        return True
    if has_path and any(word in lower for word in ["list", "show", "find", "search"]):
        return True

    return False


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
    default_action_mode = os.getenv("TREYS_AGENT_DEFAULT_MODE", "execute").strip().lower()
    if default_action_mode not in {"execute", "team", "auto", "swarm", "plan", "mail", "research", "collab", "think"}:
        default_action_mode = "execute"
    _prompt_startup_credentials()

    chat_history: list[tuple[str, str]] = []
    pending_task: str | None = None
    pending_mode: str | None = None

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

        if lower in {"help", "?", "show help"}:
            show_help()
            continue

        if lower in {"menu", "show menu"}:
            _show_menu()
            continue

        if _is_capability_query(user_input):
            _run_capabilities()
            continue

        if lower == "grade":
            from agent.modes.grade import grade_run

            grade_run(None)
            continue

        if lower.startswith("grade:"):
            from agent.modes.grade import grade_run

            target = user_input.split(":", 1)[1].strip()
            grade_run(target or None)
            continue

        if lower.startswith("connect:"):
            from agent.modes.mcp import connect

            server = user_input.split(":", 1)[1].strip()
            if not server:
                print(f"{YELLOW}[INFO]{RESET} Usage: Connect: <server_name>")
            else:
                connect(server)
            continue

        if lower in {"mcp list", "mcp tools", "mcp"}:
            from agent.modes.mcp import mcp_list

            mcp_list()
            continue

        if lower == "resume":
            from agent.modes.resume import resume_run

            resume_run(None)
            continue

        if lower.startswith("resume:"):
            from agent.modes.resume import resume_run

            target = user_input.split(":", 1)[1].strip()
            resume_run(target or None)
            continue

        if lower in {"maintenance", "maintain"}:
            from agent.modes.maintenance import maintenance_report

            maintenance_report()
            continue

        if lower.startswith("maintenance:"):
            from agent.modes.maintenance import maintenance_report

            arg = user_input.split(":", 1)[1].strip()
            try:
                days = int(arg)
            except Exception:
                days = 7
            maintenance_report(days=days)
            continue

        if pending_task:
            if lower in {"cancel", "never mind", "nevermind", "stop"}:
                print(f"{YELLOW}[CANCELLED]{RESET} Ok, not running.")
                pending_task = None
                pending_mode = None
                continue

            requested_mode = _parse_mode_request(user_input)
            if requested_mode:
                if requested_mode == "team":
                    run_team = None
                    from agent.autonomous.supervisor.orchestrator import run_team as _run_team
                    run_team = _run_team
                    run_team(pending_task, unsafe_mode=unsafe_mode)
                elif requested_mode == "swarm":
                    from agent.modes.swarm import mode_swarm

                    mode_swarm(pending_task, unsafe_mode=unsafe_mode)
                elif requested_mode == "auto":
                    mode_autonomous(pending_task, unsafe_mode=unsafe_mode)
                elif requested_mode == "plan":
                    from agent.modes.autonomous_enhanced import mode_plan_and_execute
                    mode_plan_and_execute(pending_task)
                elif requested_mode == "mail":
                    _run_mail_guided(pending_task)
                elif requested_mode == "research":
                    mode_research(pending_task)
                elif requested_mode == "execute":
                    mode_execute(pending_task)
                pending_task = None
                pending_mode = None
                continue

            if _is_confirm(user_input):
                chosen = pending_mode or "execute"
                if chosen == "team":
                    from agent.autonomous.supervisor.orchestrator import run_team as _run_team
                    _run_team(pending_task, unsafe_mode=unsafe_mode)
                elif chosen == "swarm":
                    from agent.modes.swarm import mode_swarm

                    mode_swarm(pending_task, unsafe_mode=unsafe_mode)
                elif chosen == "auto":
                    mode_autonomous(pending_task, unsafe_mode=unsafe_mode)
                elif chosen == "plan":
                    from agent.modes.autonomous_enhanced import mode_plan_and_execute
                    mode_plan_and_execute(pending_task)
                elif chosen == "mail":
                    _run_mail_guided(pending_task)
                elif chosen == "research":
                    mode_research(pending_task)
                elif chosen == "execute":
                    mode_execute(pending_task)
                pending_task = None
                pending_mode = None
                continue

        if _is_mode_switch_request(user_input):
            print(
                f"{YELLOW}[INFO]{RESET} I won't switch modes automatically. Tell me your goal and I'll ask questions first, then suggest research or a plan."
            )
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

        if lower.startswith("plan:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Plan:'.")
                continue
            from agent.modes.autonomous_enhanced import mode_plan_and_execute
            mode_plan_and_execute(task)
            continue

        if lower.startswith("team:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Team:'.")
                continue
            from agent.autonomous.supervisor.orchestrator import run_team

            run_team(task, unsafe_mode=unsafe_mode)
            continue

        if lower.startswith("swarm:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Swarm:'.")
                continue
            from agent.modes.swarm import mode_swarm

            mode_swarm(task, unsafe_mode=unsafe_mode)
            continue

        if lower.startswith("think:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Think:'.")
                continue
            from agent.autonomous.planning.think_loop import run_think_loop

            run_think_loop(task)
            continue

        if lower in {"issues", "issues open", "issues resolved"}:
            try:
                from agent.memory.issue_tracker import list_issues, get_issue_summary

                status_filter = None
                if "open" in lower:
                    status_filter = "open"
                elif "resolved" in lower:
                    status_filter = "resolved"

                issues = list_issues(status=status_filter)
                summary = get_issue_summary()

                print(f"\n{CYAN}[ISSUE TRACKER]{RESET}")
                print(f"Total: {summary['total']} | Open: {summary['open']} | Resolved: {summary['resolved']}\n")

                if not issues:
                    print(f"{YELLOW}[INFO]{RESET} No issues found.")
                else:
                    for issue in issues:
                        status_color = GREEN if issue.status == "resolved" else RED
                        print(f"{status_color}[{issue.status.upper()}]{RESET} {issue.issue_id}")
                        print(f"  Task: {issue.task}")
                        print(f"  Error: {issue.error}")
                        print(f"  Attempts: {len(issue.attempts)}")
                        if issue.solution:
                            print(f"  Solution: {issue.solution}")
                        print()
            except Exception as exc:
                print(f"{RED}[ERROR]{RESET} Failed to list issues: {exc}")
            continue

        if lower.startswith("auto:") or lower.startswith("loop:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Auto:'.")
                continue
            mode_autonomous(task, unsafe_mode=unsafe_mode)
            continue

        if lower.startswith("execute:") or lower.startswith("exec:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a task after 'Execute:'.")
                continue
            mode_execute(task)
            continue

        if _maybe_route_mail(user_input):
            continue

        if lower.startswith("collab:"):
            task = user_input.split(":", 1)[1].strip()
            if not task:
                print(f"{YELLOW}[INFO]{RESET} Provide a goal after 'Collab:'.")
                continue
            from agent.context_loader import format_context_for_llm
            from agent.modes.collaborative import mode_collaborative
            from agent.modes.execute_plan import execute_plan_direct

            context = format_context_for_llm()
            result = mode_collaborative(task, context=context)

            if result.get("approved"):
                plan_steps = result.get("plan_steps", [])
                if plan_steps:
                    # Use direct MCP tool execution (fast path!)
                    success = execute_plan_direct(plan_steps)
                    if not success:
                        print(f"{RED}[FALLBACK]{RESET} Direct execution failed, trying execute mode...")
                        mode_execute(task, context=result)
                else:
                    # No plan steps, fall back to execute mode
                    print(f"{YELLOW}[FALLBACK]{RESET} No plan steps, using execute mode...")
                    mode_execute(task, context=result)
            continue

        if _is_simple_question(user_input):
            _handle_simple_question(user_input)
            continue

        # Auto-execute simple filesystem queries
        if _is_simple_filesystem_query(user_input):
            mode_execute(user_input)
            continue

        # Smart orchestrator decides mode automatically
        routing = smart_orchestrator(user_input)

        if routing["mode"] == "collaborative":
            from agent.context_loader import format_context_for_llm
            from agent.modes.collaborative import mode_collaborative
            from agent.modes.execute_plan import execute_plan_direct

            context = format_context_for_llm()
            result = mode_collaborative(user_input, context=context)

            if result.get("approved"):
                plan_steps = result.get("plan_steps", [])
                if plan_steps:
                    success = execute_plan_direct(plan_steps)
                    if not success:
                        mode_execute(user_input, context=result)
                else:
                    mode_execute(user_input, context=result)
            continue

        if routing["mode"] == "swarm":
            from agent.modes.swarm import mode_swarm

            # Ask for swarm confirmation (complex tasks warrant it)
            print(f"{YELLOW}[SWARM RECOMMENDED]{RESET} {routing['reason']}")
            print("This task benefits from parallel analysis. Proceed with swarm mode? (y/n): ", end="")
            confirm = input().strip().lower()
            if confirm in {"y", "yes"}:
                mode_swarm(user_input, unsafe_mode=unsafe_mode)
            else:
                mode_execute(user_input)  # Fallback to single-agent
            continue

        if routing["mode"] == "execute":
            if routing.get("auto_execute"):
                mode_execute(user_input)
                continue

        if routing["mode"] == "chat":
            chat_history.append(("user", user_input))
            _run_chat(user_input, chat_history)
            continue

if __name__ == "__main__":
    main()
