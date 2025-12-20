"""
Trey's Agent - One Terminal, Codex Powered
All LLM calls use Codex CLI (codex exec).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

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

# Ensure imports resolve to the repo-root `agent` package when run from `...\agent`.
sys.path.insert(0, str(REPO_ROOT))

CODEX_TIMEOUT_SECONDS = int(os.getenv("CODEX_TIMEOUT_SECONDS", "120"))
CODEX_REASONING_EFFORT = os.getenv("CODEX_REASONING_EFFORT", "medium")

TEMP_PLAN = BASE_DIR / "temp_plan.yaml"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
PROMPTS_DIR = BASE_DIR / "prompts"


def banner():
    print(f"\n{CYAN}{'=' * 50}")
    print("   Trey's Agent - Codex Powered")
    print(f"{'=' * 50}{RESET}\n")


def load_prompt(name: str) -> str:
    """Load a prompt file from prompts directory."""
    path = PROMPTS_DIR / f"{name}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def load_context() -> str:
    """Load agent context (credentials, playbooks, tools)."""
    try:
        from agent.context_loader import format_context_for_display, format_context_for_llm

        print(f"{CYAN}[SYSTEM] Loading context...{RESET}")
        print(format_context_for_display())
        return format_context_for_llm()
    except Exception as e:
        print(f"{YELLOW}[INFO] Context loader not available: {e}{RESET}")
        return ""


def codex_command() -> list:
    """Get the codex command."""
    cmd = shutil.which("codex") or shutil.which("codex.ps1")
    if cmd and cmd.lower().endswith(".ps1"):
        return ["powershell", "-File", cmd]
    return [cmd or "codex"]


class Spinner:
    def __init__(self, label: str = "Working"):
        self.label = label
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        frames = ["|", "/", "-", "\\"]
        idx = 0
        while not self._stop.is_set():
            print(f"\r{CYAN}[{self.label}] {frames[idx]}{RESET}", end="", flush=True)
            idx = (idx + 1) % len(frames)
            self._stop.wait(0.2)
        print("\r" + " " * 60 + "\r", end="", flush=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        self._thread.join(timeout=1)


def call_codex(prompt: str, save_to: Optional[Path] = None) -> str:
    """
    Call Codex CLI in non-interactive mode.
    Returns the response text.
    """
    # Keep Codex "text-only" here: planning/self-heal/post-chat should not execute shell/MCP tools.
    # Note: `--search` is a global flag and must appear before the `exec` subcommand.
    cmd = codex_command() + [
        "--dangerously-bypass-approvals-and-sandbox",
        "--search",
        "exec",
        "-c",
        f'model_reasoning_effort="{CODEX_REASONING_EFFORT}"',
        "--disable",
        "shell_tool",
        "--disable",
        "rmcp_client",
    ]
    if save_to:
        cmd.extend(["--output-last-message", str(save_to)])

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        spinner_ctx = Spinner("CODEX") if sys.stdout.isatty() else nullcontext()
        with spinner_ctx:
            proc = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                encoding="utf-8",
                errors="ignore",
                capture_output=True,
                env=env,
                cwd=str(REPO_ROOT),
                timeout=CODEX_TIMEOUT_SECONDS,
            )
    except FileNotFoundError:
        return "[CODEX ERROR] Codex CLI not found on PATH."
    except subprocess.TimeoutExpired:
        return "[CODEX ERROR] Codex CLI timed out."

    if proc.returncode != 0:
        error = proc.stderr.strip() if proc.stderr else "Unknown error"
        return f"[CODEX ERROR] {error}"

    return proc.stdout.strip() if proc.stdout else ""


def interactive_planning(goal: str, context: str) -> Optional[str]:
    """
    Have Codex ask clarifying questions, then generate YAML.
    Returns the YAML plan or None.
    """
    system_prompt = load_prompt("interactive_planner")
    if not system_prompt:
        system_prompt = """You are a task planning assistant.
Ask 2-3 clarifying questions about the user's goal, then generate a YAML task plan.
When ready, output the YAML starting with 'id:' and ending with the complete plan."""

    full_prompt = f"{context}\n\n{system_prompt}\n\nUser's goal: {goal}"

    print(f"\n{CYAN}[CODEX]{RESET} Let me understand your goal better...")

    for _turn in range(6):  # Max 6 turns
        response = call_codex(full_prompt)

        if response.startswith("[CODEX ERROR]"):
            print(f"{RED}{response}{RESET}")
            return None

        print(f"\n{CYAN}[CODEX]{RESET} {response}")

        # Check if response contains YAML
        yaml_match = extract_yaml(response)
        if yaml_match:
            return yaml_match

        # Get user input
        user_input = input(f"\n{GREEN}[YOU]{RESET} ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "cancel"]:
            return None

        full_prompt = f"{full_prompt}\n\nAssistant: {response}\n\nUser: {user_input}\n\nAssistant:"

    print(f"{RED}[ERROR] Could not generate YAML plan after multiple attempts.{RESET}")
    return None


def extract_yaml(text: str) -> Optional[str]:
    """Extract YAML from text (handles code fences)."""
    fenced = re.findall(r"```(?:yaml)?\\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates: List[str] = fenced
    else:
        m = re.search(r"(?m)^\\s*id\\s*:\\s*.+$", text)
        candidates = [text[m.start() :]] if m else [text]

    for candidate in candidates:
        candidate = candidate.strip()
        try:
            loaded = yaml.safe_load(candidate)
        except Exception:
            continue
        if isinstance(loaded, dict) and "id" in loaded and "type" in loaded:
            return candidate
    return None


def execute_plan(*, unsafe_mode: bool = False) -> Dict[str, Any]:
    """Execute the plan using supervisor."""
    start_time = time.time()

    cmd = [sys.executable, "-m", "agent.supervisor.supervisor", str(TEMP_PLAN)]
    if unsafe_mode:
        cmd.append("--unsafe-mode")
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))

    duration = time.time() - start_time
    success = proc.returncode == 0

    return {
        "success": success,
        "exit_code": proc.returncode,
        "duration": round(duration, 1),
        "artifacts": find_artifacts(start_time),
    }


def find_artifacts(since: float) -> List[str]:
    """Find files created/modified since timestamp."""
    artifacts: List[str] = []
    allowed = {".py", ".txt", ".md", ".json", ".yaml", ".yml", ".html", ".css", ".js"}

    for root, _, files in os.walk(REPO_ROOT):
        for f in files:
            path = Path(root) / f
            try:
                if path.stat().st_mtime >= since and path.suffix.lower() in allowed:
                    rel = path.relative_to(REPO_ROOT)
                    artifacts.append(str(rel))
            except Exception:
                continue

    return artifacts[:20]


def self_heal(goal: str, error: str, yaml_content: str, context: str) -> Optional[str]:
    """
    Use Codex to analyze failure and generate corrected YAML.
    Returns corrected YAML or None.
    """
    print(f"\n{YELLOW}[SELF-HEALING] Analyzing failure with Codex...{RESET}")

    prompt = f"""{context}

You are debugging a failed task. Analyze the error and generate a corrected YAML plan.

ORIGINAL GOAL: {goal}

FAILED YAML:
{yaml_content}

ERROR:
{error}

Instructions:
1. Analyze what went wrong
2. Explain the fix briefly
3. Output the corrected YAML plan

Start your response with your analysis, then output the corrected YAML."""

    response = call_codex(prompt)

    if response.startswith("[CODEX ERROR]"):
        print(f"{RED}{response}{RESET}")
        return None

    print(f"\n{CYAN}[CODEX]{RESET} {response[:500]}...")

    corrected = extract_yaml(response)
    if corrected:
        print(f"\n{GREEN}[SELF-HEALING] Generated corrected plan!{RESET}")
        return corrected

    print(f"{RED}[SELF-HEALING] Could not extract corrected YAML.{RESET}")
    return None


def post_execution_chat(result: Dict[str, Any], context: str) -> Optional[str]:
    """
    Discuss results with user, offer options.
    Returns next goal if user wants to continue, None otherwise.
    """
    system_prompt = load_prompt("post_execution")
    if not system_prompt:
        system_prompt = """You are a helpful assistant discussing task results.
Summarize what was done, list artifacts, and offer numbered options:
1. Run/open created files
2. See the code
3. Make improvements
4. Create something else
5. Exit"""

    result_summary = json.dumps(result, indent=2)
    full_prompt = (
        f"{context}\n\n{system_prompt}\n\nTask Result:\n{result_summary}\n\n"
        "Provide a friendly summary and options."
    )

    response = call_codex(full_prompt)
    print(f"\n{CYAN}[CODEX]{RESET} {response}")

    while True:
        user_input = input(f"\n{GREEN}[YOU]{RESET} ").strip()

        if not user_input or user_input.lower() in ["done", "next", "new", "5"]:
            return None

        if user_input.lower() in ["exit", "quit"]:
            return "EXIT"

        if user_input == "1":
            open_artifacts(result.get("artifacts", []))
            continue

        if user_input == "2":
            show_code(result.get("artifacts", []))
            continue

        if user_input in ["3", "4"] or "add" in user_input.lower() or "change" in user_input.lower():
            if user_input in ["3", "4"]:
                improvement = input(f"{GREEN}What would you like to change?{RESET} ").strip()
                return improvement if improvement else None
            return user_input

        # Continue conversation
        full_prompt = f"{full_prompt}\n\nUser: {user_input}\n\nAssistant:"
        response = call_codex(full_prompt)
        print(f"\n{CYAN}[CODEX]{RESET} {response}")


def open_artifacts(artifacts: List[str]):
    """Open/run artifact files."""
    if not artifacts:
        print("No artifacts to open.")
        return

    for artifact in artifacts[:5]:
        path = REPO_ROOT / artifact
        if not path.exists():
            continue

        print(f"\nOpening: {artifact}")
        try:
            if path.suffix == ".py":
                run = input(f"Run {path.name}? (y/n) ").strip().lower()
                if run == "y":
                    subprocess.Popen(
                        [sys.executable, str(path)],
                        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
                    )
                else:
                    os.startfile(str(path))
            else:
                os.startfile(str(path))
        except Exception as e:
            print(f"{RED}Could not open: {e}{RESET}")


def show_code(artifacts: List[str]):
    """Display code from artifacts."""
    code_files = [a for a in artifacts if a.endswith((".py", ".js", ".html", ".css"))]
    if not code_files:
        print("No code files found.")
        return

    for artifact in code_files[:3]:
        path = REPO_ROOT / artifact
        if path.exists():
            print(f"\n{YELLOW}--- {artifact} ---{RESET}")
            try:
                content = path.read_text(encoding="utf-8")
                print(content[:2000])
                if len(content) > 2000:
                    print(f"\n... ({len(content) - 2000} more characters)")
            except Exception as e:
                print(f"Could not read: {e}")


def main():
    banner()

    # Load context
    context = load_context()
    print()

    while True:
        try:
            goal = input(f"{CYAN}Enter goal (or 'exit'):{RESET} ").strip()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return

        if not goal:
            continue
        if goal.lower() in ["exit", "quit"]:
            print("Goodbye!")
            return

        # Phase 1: Interactive Planning
        yaml_content = interactive_planning(goal, context)
        if not yaml_content:
            continue

        # Save and display plan
        TEMP_PLAN.write_text(yaml_content, encoding="utf-8")
        print(f"\n{YELLOW}--- Generated Plan ---{RESET}")
        print(yaml_content[:1500])
        if len(yaml_content) > 1500:
            print("... (truncated)")
        print(f"{YELLOW}------------------------{RESET}")

        # Confirm execution
        choice = input(f"\n{GREEN}Execute this plan? (Y/n/edit):{RESET} ").strip().lower() or "y"
        if choice == "n":
            continue
        if choice == "edit":
            subprocess.run(["notepad", str(TEMP_PLAN)])
            yaml_content = TEMP_PLAN.read_text(encoding="utf-8")

        # Phase 2: Execute
        unsafe = os.getenv("AGENT_UNSAFE_MODE", "").strip().lower() in {"1", "true", "yes", "y", "on"}
        if not unsafe:
            try:
                unsafe_choice = input(f"{YELLOW}Enable unsafe mode for tool execution? (y/N):{RESET} ").strip().lower()
                unsafe = unsafe_choice == "y"
            except Exception:
                unsafe = False

        print(f"\n{CYAN}[EXECUTING]{RESET} Running task (unsafe_mode={unsafe})...")
        result = execute_plan(unsafe_mode=unsafe)

        # Handle failure with self-healing
        if not result["success"]:
            print(f"\n{RED}[FAILED] Task failed (exit code {result['exit_code']}){RESET}")

            retry = input(f"{YELLOW}Try self-healing? (y/n):{RESET} ").strip().lower()
            if retry == "y":
                corrected = self_heal(goal, f"Exit code {result['exit_code']}", yaml_content, context)
                if corrected:
                    TEMP_PLAN.write_text(corrected, encoding="utf-8")
                    print(f"\n{CYAN}[RETRYING]{RESET} Executing corrected plan...")
                    result = execute_plan(unsafe_mode=unsafe)

        # Show result
        status = "SUCCESS" if result["success"] else "FAILED"
        color = GREEN if result["success"] else RED
        print(f"\n{color}[{status}] Completed in {result['duration']}s{RESET}")

        if result["artifacts"]:
            print(f"\n{GREEN}Artifacts created:{RESET}")
            for a in result["artifacts"][:10]:
                print(f"  - {a}")

        # Phase 3: Post-execution chat
        next_goal = post_execution_chat(result, context)

        if next_goal == "EXIT":
            print("Goodbye!")
            return
        elif next_goal:
            goal = next_goal
            continue


if __name__ == "__main__":
    main()
