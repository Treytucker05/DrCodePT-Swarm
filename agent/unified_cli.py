from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

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
PLANNER_PROMPT_FILE = BASE_DIR / "planner_system_prompt.txt"
TEMP_PLAN = BASE_DIR / "temp_plan.yaml"


def banner():
    print(f"{CYAN}=== Trey'sAgent - Codex + Ollama Team ==={RESET}")


def load_planner_prompt() -> str:
    if not PLANNER_PROMPT_FILE.exists():
        return "You are a planner."
    return PLANNER_PROMPT_FILE.read_text(encoding="utf-8")


def codex_command() -> list:
    cmd = shutil.which("codex") or shutil.which("codex.ps1")
    if cmd and cmd.lower().endswith(".ps1"):
        return ["powershell", "-File", cmd]
    return [cmd or "codex"]


def generate_plan(goal: str) -> bool:
    planner_prompt = load_planner_prompt()
    prompt = f"{planner_prompt}\n\nUser goal:\n{goal}\n\nReturn ONLY the YAML plan."
    cmd = codex_command() + ["exec", "--output-last-message", str(TEMP_PLAN)]
    proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True)
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


def display_plan():
    print(f"{YELLOW}--- Generated Plan ({TEMP_PLAN}) ---{RESET}")
    print(TEMP_PLAN.read_text(encoding="utf-8"))
    print(f"{YELLOW}------------------------------------{RESET}")


def execute_plan() -> int:
    start = time.time()
    cmd = [sys.executable, "-m", "agent.supervisor.supervisor", str(TEMP_PLAN)]
    proc = subprocess.run(cmd)
    duration = time.time() - start
    status = "SUCCESS" if proc.returncode == 0 else "FAIL"
    color = GREEN if proc.returncode == 0 else RED
    print(f"{color}[{status}] Execution finished in {duration:.1f}s (code {proc.returncode}){RESET}")
    return proc.returncode


def main():
    os.chdir(BASE_DIR)
    banner()
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

        if not generate_plan(goal):
            continue

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

        execute_plan()


if __name__ == "__main__":
    main()
