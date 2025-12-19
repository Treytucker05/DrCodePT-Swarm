from __future__ import annotations

"""Research mode - iterative deep research with refinement."""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from colorama import Fore, Style

    GREEN, RED, CYAN, YELLOW, RESET = (
        Fore.GREEN,
        Fore.RED,
        Fore.CYAN,
        Fore.YELLOW,
        Style.RESET_ALL,
    )
except Exception:
    GREEN = RED = CYAN = YELLOW = RESET = ""

BASE_DIR = Path(__file__).resolve().parents[1]  # .../agent
REPO_ROOT = BASE_DIR.parent


def _codex_command() -> list[str]:
    cmd = shutil.which("codex") or shutil.which("codex.ps1")
    if cmd and cmd.lower().endswith(".ps1"):
        return ["powershell", "-File", cmd]
    return [cmd or "codex"]


def _call_codex(prompt: str, *, allow_tools: bool) -> str:
    cmd: list[str] = _codex_command() + ["exec"]
    if not allow_tools:
        cmd += ["-c", "--disable", "shell_tool", "--disable", "rmcp_client"]
    cmd += ["--dangerously-bypass-approvals-and-sandbox"]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="ignore",
            capture_output=True,
            env=env,
            cwd=str(REPO_ROOT),
            timeout=int(os.getenv("CODEX_TIMEOUT_SECONDS", "300")),
        )
    except FileNotFoundError:
        return "[CODEX ERROR] Codex CLI not found on PATH."
    except subprocess.TimeoutExpired:
        return "[CODEX ERROR] Codex CLI timed out."

    if proc.returncode != 0:
        error = proc.stderr.strip() if proc.stderr else "Unknown error"
        return f"[CODEX ERROR] {error}"

    return proc.stdout.strip() if proc.stdout else ""


def mode_research(topic: str) -> None:
    print(f"\n{CYAN}[RESEARCH MODE]{RESET} Topic: {topic}")
    print("I’ll ask a few quick questions to focus the research.\n")

    questions_prompt = f"""User wants to research: {topic}

Ask 2-3 targeted questions to clarify:
1) what aspect matters most,
2) what it's for (decision, implementation, learning),
3) constraints (time/budget/stack).

Be concise. Output questions only."""

    questions = _call_codex(questions_prompt, allow_tools=False)
    if questions.startswith("[CODEX ERROR]"):
        print(f"{RED}{questions}{RESET}")
        return

    print(f"{CYAN}[QUESTIONS]{RESET}\n{questions}")
    answers = input(f"\n{GREEN}[YOU]{RESET} ").strip()

    print(f"\n{YELLOW}[RESEARCHING]{RESET} Gathering sources and synthesizing...")
    research_prompt = f"""Research topic: {topic}
User clarifications: {answers}

Instructions:
- Do real web research (use shell/python to fetch sources if helpful).
- Compare multiple credible sources.
- Iterate: refine your answer as you discover better sources.
- Return a structured, comprehensive answer.
- Include citations as raw URLs (one per bullet or sentence as needed).
- Do not include any private data from this machine; do not modify files.
"""

    findings = _call_codex(research_prompt, allow_tools=True)
    if findings.startswith("[CODEX ERROR]"):
        print(f"{RED}{findings}{RESET}")
        return

    print(f"\n{CYAN}[FINDINGS]{RESET}\n{findings}")

    while True:
        followup = input(f"\n{GREEN}Follow-up (or 'done'):{RESET} ").strip()
        if not followup or followup.lower() in {"done", "exit", "quit"}:
            break

        followup_prompt = f"""Topic: {topic}
User clarifications: {answers}

Previous answer:
{findings[:4000]}

Follow-up question: {followup}

Do additional research and answer this follow-up. Include citations as raw URLs."""
        more = _call_codex(followup_prompt, allow_tools=True)
        if more.startswith("[CODEX ERROR]"):
            print(f"{RED}{more}{RESET}")
            continue
        print(f"\n{CYAN}[MORE]{RESET}\n{more}")
        findings += f"\n\n{more}"

    save = input(f"\n{YELLOW}Save this research to a file? (y/n):{RESET} ").strip().lower()
    if save != "y":
        return

    out_dir = BASE_DIR / "research"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"research_{topic[:32].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
    path = out_dir / filename
    path.write_text(findings, encoding="utf-8")
    print(f"{GREEN}[SAVED]{RESET} {path}")

