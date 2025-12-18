from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import yaml

try:  # optional color
    from colorama import Fore, Style, init as color_init

    color_init()
    GREEN = Fore.GREEN
    RED = Fore.RED
    CYAN = Fore.CYAN
    YELLOW = Fore.YELLOW
    RESET = Style.RESET_ALL
except Exception:  # pragma: no cover - fallback to plain text
    GREEN = RED = CYAN = YELLOW = RESET = ""


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
PLANNER_PROMPT_FILE = BASE_DIR / "planner_system_prompt.txt"
TEMP_PLAN = BASE_DIR / "temp_plan.yaml"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
CONVO_LOG = LOG_DIR / "conversations.log"
PROMPTS_DIR = BASE_DIR / "prompts"
INTERACTIVE_PLANNER_PROMPT = PROMPTS_DIR / "interactive_planner.txt"
POST_EXEC_PROMPT = PROMPTS_DIR / "post_execution.txt"


def banner():
    print(f"{CYAN}=== Trey'sAgent - Codex + Ollama Team ==={RESET}")


def load_planner_prompt() -> str:
    if not PLANNER_PROMPT_FILE.exists():
        return "You are a planner."
    return PLANNER_PROMPT_FILE.read_text(encoding="utf-8")


def load_prompt_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def log_conversation(role: str, content: str):
    entry = {"ts": datetime.now().isoformat(), "role": role, "content": content}
    with CONVO_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def codex_command() -> list:
    cmd = shutil.which("codex") or shutil.which("codex.ps1")
    if cmd and cmd.lower().endswith(".ps1"):
        return ["powershell", "-File", cmd]
    return [cmd or "codex"]


def codex_chat_turn(system_prompt: str, history: List[Dict[str, str]]) -> str:
    """
    Approximate a chat turn by sending history to codex CLI in one shot.
    """
    transcript_lines = [f"System: {system_prompt.strip()}"]
    for msg in history:
        prefix = "User" if msg["role"] == "user" else "Assistant"
        transcript_lines.append(f"{prefix}: {msg['content']}")
    prompt = "\n".join(transcript_lines) + "\nAssistant:"

    # use codex exec (non-interactive) to avoid TTY requirement
    cmd = codex_command() + ["exec", "--dangerously-bypass-approvals-and-sandbox"]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    output = (proc.stdout or "").strip()
    if proc.returncode != 0 or not output:
        err = (proc.stderr or "").strip()
        msg = f"[codex error {proc.returncode}] {err}" if err else "[codex produced no output]"
        return msg
    return output


def extract_yaml_from_text(text: str) -> str | None:
    fenced = re.findall(r"```(?:yaml)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    candidates = fenced if fenced else [text]
    for cand in candidates:
        if "id:" in cand and "type:" in cand:
            try:
                yaml.safe_load(cand)
                return cand.strip()
            except Exception:
                continue
    return None


def interactive_planning_with_codex(initial_goal: str) -> str | None:
    system_prompt = load_prompt_file(INTERACTIVE_PLANNER_PROMPT)
    history: List[Dict[str, str]] = [{"role": "user", "content": initial_goal}]
    log_conversation("user", initial_goal)
    print(f"{CYAN}[CODEX] Let's refine your goal...{RESET}")
    for _ in range(8):  # max turns
        reply = codex_chat_turn(system_prompt, history)
        log_conversation("assistant", reply)
        print(f"{CYAN}[CODEX]{RESET} {reply}")
        if reply.startswith("[codex error"):
            print(f"{RED}[WARN]{RESET} Codex CLI returned an error; try again or check codex install.")
        yaml_block = extract_yaml_from_text(reply)
        if yaml_block:
            try:
                yaml.safe_load(yaml_block)
                return yaml_block
            except Exception:
                pass
        user = input(f"{CYAN}[YOU]{RESET} ").strip()
        log_conversation("user", user)
        if not user:
            continue
        history.append({"role": "assistant", "content": reply})
        history.append({"role": "user", "content": user})
    print(f"{RED}[ERROR]{RESET} Could not obtain YAML plan from Codex.")
    return None


def post_execution_conversation(task_result: dict) -> str | None:
    system_prompt = load_prompt_file(POST_EXEC_PROMPT)
    summary = json.dumps(task_result, indent=2)
    history: List[Dict[str, str]] = [{"role": "user", "content": f"Task result:\n{summary}"}]
    while True:
        reply = codex_chat_turn(system_prompt, history)
        log_conversation("assistant", reply)
        print(f"{CYAN}[CODEX]{RESET} {reply}")
        user = input(f"{CYAN}[YOU]{RESET} ").strip()
        log_conversation("user", user)
        if user.lower() in {"exit", "quit"}:
            return "exit"
        if user.lower() in {"next", "new", "done"}:
            return None
        if user.isdigit():
            return f"option:{user}"
        if user.lower().startswith("improve") or "add" in user.lower():
            return user
        if user:
            history.append({"role": "assistant", "content": reply})
            history.append({"role": "user", "content": user})
        else:
            return None


def _truncate(text: str, limit: int = 120) -> str:
    text = text.replace("\n", " ").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def summarize_plan(plan: dict):
    if not isinstance(plan, dict):
        print("  (unable to summarize)")
        return
    print(f"  Goal: {plan.get('goal','(no goal)')}")
    print(f"  Definition of done: {plan.get('definition_of_done','(not specified)')}")
    steps = plan.get("steps") or []
    if steps:
        print("  Steps:")
        for idx, step in enumerate(steps, 1):
            name = step.get("name") or step.get("id") or f"step-{idx}"
            stype = step.get("type")
            goal = step.get("goal") or ""
            detail = ""
            if stype == "shell":
                detail = _truncate(step.get("command", ""))
            elif stype == "browser":
                detail = step.get("url", "")
            elif stype == "python":
                detail = _truncate(step.get("script", ""))
            print(f"    {idx}. [{stype}] {name} — {goal} {('(cmd: ' + detail + ')') if detail else ''}")
    else:
        print("  (no steps listed)")


def display_plan():
    print(f"{YELLOW}--- Generated Plan ({TEMP_PLAN}) ---{RESET}")
    content = TEMP_PLAN.read_text(encoding="utf-8")
    print(content)
    print(f"{YELLOW}------------------------------------{RESET}")
    try:
        data = yaml.safe_load(content)
        print(f"{GREEN}Plain-English summary:{RESET}")
        summarize_plan(data)
    except Exception:
        print(f"{RED}[WARN]{RESET} Could not parse YAML for summary.")


def open_created_files(artifacts: List[str]):
    if not artifacts:
        print("No artifacts to open.")
        return
    for path in artifacts:
        p = Path(path)
        if not p.exists():
            print(f"{RED}Missing:{RESET} {path}")
            continue
        suffix = p.suffix.lower()
        try:
            if suffix == ".py":
                run = input(f"Run {p.name}? (y/n) ").strip().lower()
                if run == "y":
                    creationflag = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
                    subprocess.Popen([sys.executable, str(p)], creationflags=creationflag, cwd=str(p.parent))
                else:
                    os.startfile(str(p))
            elif p.is_dir():
                os.startfile(str(p))
            else:
                os.startfile(str(p))
        except Exception as exc:
            print(f"{RED}Could not open {p}: {exc}{RESET}")


def find_recent_artifacts(start_ts: float) -> List[str]:
    artifacts = []
    roots = [REPO_ROOT, REPO_ROOT / "agent", REPO_ROOT / "launchers"]
    allowed_suffixes = {".py", ".txt", ".md", ".json", ".yaml", ".yml"}
    for base in roots:
        if not base.exists():
            continue
        for root, _, files in os.walk(base):
            for f in files:
                path = Path(root) / f
                try:
                    if path.stat().st_mtime >= start_ts and path.suffix.lower() in allowed_suffixes:
                        artifacts.append(str(path.relative_to(REPO_ROOT)))
                except FileNotFoundError:
                    continue
    return artifacts[:50]


def generate_plan(goal: str) -> bool:
    planner_prompt = load_planner_prompt()
    prompt = f"{planner_prompt}\n\nUser goal:\n{goal}\n\nReturn ONLY the YAML plan."
    cmd = codex_command() + ["exec", "--output-last-message", str(TEMP_PLAN)]
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    if proc.returncode != 0:
        print(f"{RED}[ERROR] codex exec failed ({proc.returncode}){RESET}")
        if proc.stderr:
            print(proc.stderr.strip())
        return False
    if not TEMP_PLAN.exists():
        print(f"{RED}[ERROR] Plan file not created at {TEMP_PLAN}{RESET}")
        return False
    try:
        yaml.safe_load(TEMP_PLAN.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"{RED}[ERROR] Generated plan is not valid YAML: {exc}{RESET}")
        return False
    return True


def execute_plan() -> int:
    start = time.time()
    cmd = [sys.executable, "-m", "agent.supervisor.supervisor", str(TEMP_PLAN)]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    duration = time.time() - start
    status = "SUCCESS" if proc.returncode == 0 else "FAIL"
    color = GREEN if proc.returncode == 0 else RED
    print(f"{color}[{status}] Execution finished in {duration:.1f}s (code {proc.returncode}){RESET}")
    return proc.returncode


def handle_post_option(option: str, artifacts: List[str]):
    num = option.split(":")[-1]
    if num == "1":
        open_created_files(artifacts)
    elif num == "2":
        for a in artifacts:
            p = REPO_ROOT / a
            if p.exists() and p.is_file():
                print(f"\n--- {a} ---")
                try:
                    print(p.read_text(encoding="utf-8"))
                except Exception as exc:
                    print(f"[unable to read: {exc}]")
    elif num == "3":
        print("You can ask Codex to explain; type a question in the post-run chat.")
    elif num == "4":
        improvement = input("What improvement do you want? ").strip()
        if improvement:
            global _IMPROVEMENT_QUEUE  # type: ignore
            _IMPROVEMENT_QUEUE = improvement
    elif num == "5":
        print("Okay, let's start a new goal.")


def main():
    os.chdir(REPO_ROOT)
    banner()
    global _IMPROVEMENT_QUEUE
    _IMPROVEMENT_QUEUE = None
    while True:
        try:
            goal = input(f"{CYAN}Enter goal (or 'exit'): {RESET}").strip()
        except KeyboardInterrupt:
            print("\nBye!")
            return

        if not goal:
            continue
        if goal.lower() in {"exit", "quit"}:
            print("Exiting.")
            return

        # Phase 1: interactive planning
        yaml_text = interactive_planning_with_codex(goal)
        if not yaml_text:
            continue
        TEMP_PLAN.write_text(yaml_text, encoding="utf-8")

        display_plan()
        choice = input("Execute this plan? (Y/n/edit): ").strip().lower() or "y"
        if choice == "n":
            continue
        if choice == "edit":
            subprocess.run(["notepad", str(TEMP_PLAN)])
            try:
                yaml.safe_load(TEMP_PLAN.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"{RED}[ERROR] Plan after edit is invalid YAML: {exc}{RESET}")
                continue

        start_ts = time.time()
        code = execute_plan()
        success = code == 0
        artifacts = find_recent_artifacts(start_ts)
        result = {
            "success": success,
            "exit_code": code,
            "artifacts": artifacts,
            "started_at": start_ts,
            "finished_at": time.time(),
        }
        if success:
            print(f"{GREEN}[SUCCESS]{RESET} Task completed.")
        else:
            print(f"{RED}[FAIL]{RESET} Task failed (code {code}).")
        if artifacts:
            print("Artifacts:")
            for a in artifacts:
                print(f"  - {a}")

        next_action = post_execution_conversation(result)
        if next_action == "exit":
            break
        if next_action and next_action.startswith("option:"):
            handle_post_option(next_action, artifacts)
            continue
        if _IMPROVEMENT_QUEUE:
            goal = _IMPROVEMENT_QUEUE
            _IMPROVEMENT_QUEUE = None
            continue
        if next_action:
            goal = next_action
            continue


if __name__ == "__main__":
    main()
