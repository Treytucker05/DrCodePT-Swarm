from __future__ import annotations

"""Execute mode - instant playbook execution (no LLM) with Codex fallback."""

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
PLAYBOOKS_DIR = BASE_DIR / "playbooks"
PLAYBOOKS_INDEX = PLAYBOOKS_DIR / "index.json"
RUNS_DIR = BASE_DIR / "runs" / "treys_agent"


def _ensure_dirs() -> None:
    PLAYBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_playbooks() -> dict:
    """Load playbook index."""
    _ensure_dirs()
    if not PLAYBOOKS_INDEX.is_file():
        return {}
    return _read_json(PLAYBOOKS_INDEX) or {}


def save_playbooks(index: dict) -> None:
    """Save playbook index."""
    _ensure_dirs()
    _write_json(PLAYBOOKS_INDEX, index)


def list_playbooks() -> None:
    playbooks = load_playbooks()
    if not playbooks:
        print(f"{YELLOW}No playbooks saved yet.{RESET}")
        print("Use 'Learn: [task]' to create one.")
        return

    print(f"\n{CYAN}Saved Playbooks:{RESET}")
    for pb_id, pb_data in playbooks.items():
        name = pb_data.get("name", pb_id)
        triggers = ", ".join((pb_data.get("triggers") or [])[:3])
        print(f"  • {name}")
        if triggers:
            print(f"    Triggers: {triggers}")


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "playbook"


def find_matching_playbook(command: str, playbooks: dict) -> Tuple[Optional[str], Optional[dict]]:
    """
    Find a playbook that matches the user's command.
    Returns (playbook_id, playbook_data) or (None, None).
    """
    command_lower = command.lower().strip()
    if not command_lower:
        return None, None

    # Direct match on triggers
    for pb_id, pb_data in playbooks.items():
        triggers = pb_data.get("triggers") or []
        for trigger in triggers:
            t = str(trigger).lower().strip()
            if not t:
                continue
            if t == command_lower:
                return pb_id, pb_data
            if t in command_lower or command_lower in t:
                return pb_id, pb_data

    # Fuzzy match on name/description (best-effort)
    words = [w for w in re.split(r"\\s+", command_lower) if len(w) > 3]
    if not words:
        return None, None

    for pb_id, pb_data in playbooks.items():
        name = str(pb_data.get("name") or "").lower()
        desc = str(pb_data.get("description") or "").lower()
        if any(word in name or word in desc for word in words):
            return pb_id, pb_data

    return None, None


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
            timeout=int(os.getenv("CODEX_TIMEOUT_SECONDS", "180")),
        )
    except FileNotFoundError:
        return "[CODEX ERROR] Codex CLI not found on PATH."
    except subprocess.TimeoutExpired:
        return "[CODEX ERROR] Codex CLI timed out."

    if proc.returncode != 0:
        error = proc.stderr.strip() if proc.stderr else "Unknown error"
        return f"[CODEX ERROR] {error}"

    return proc.stdout.strip() if proc.stdout else ""


def _extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None

    # Prefer fenced JSON
    fence = re.search(r"```json\\s*(\\{.*?\\})\\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass

    # Fallback: try first {...} block
    brace = re.search(r"(\\{.*\\})", text, flags=re.DOTALL)
    if brace:
        candidate = brace.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            return None
    return None


def _run_id(prefix: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return RUNS_DIR / f"{ts}_{_slugify(prefix)[:40]}"


def _coerce_browser_step(step: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(step)
    out.pop("type", None)
    out.pop("description", None)
    return out


def _iter_steps(playbook_data: dict) -> Iterable[dict]:
    steps = playbook_data.get("steps") or []
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict):
                yield step


def execute_playbook(playbook_id: str, playbook_data: dict, *, run_path: Optional[Path] = None) -> bool:
    """Execute a saved playbook directly (no LLM needed)."""
    _ensure_dirs()
    run_path = run_path or _run_id(playbook_id)
    run_path.mkdir(parents=True, exist_ok=True)

    print(f"{CYAN}[EXECUTING]{RESET} {playbook_data.get('name', playbook_id)}")

    try:
        from agent.tools.browser import BrowserTool
        from agent.tools.python_exec import PythonExecTool
        from agent.tools.shell import ShellTool
    except Exception as exc:
        print(f"{RED}[ERROR]{RESET} Failed to import tools: {exc}")
        return False

    shell_tool = ShellTool()
    python_tool = PythonExecTool()
    browser_tool = BrowserTool()

    # Some BrowserTool features read attributes from a task object.
    browser_task = SimpleNamespace(
        login_site=playbook_data.get("login_site"),
        session_state_path=playbook_data.get("session_state_path"),
        url=playbook_data.get("url"),
    )

    pending_browser: List[Dict[str, Any]] = []

    def flush_browser() -> bool:
        nonlocal pending_browser
        if not pending_browser:
            return True

        inputs = {
            "steps": pending_browser,
            "login_site": playbook_data.get("login_site"),
            "run_path": str(run_path),
            "url": playbook_data.get("url"),
        }
        result = browser_tool.execute(browser_task, inputs)
        if result.success:
            pending_browser = []
            return True

        # If credentials are missing, retry without login_site to allow already-signed-in sessions.
        err = str(result.error or "")
        if playbook_data.get("login_site") and "No credentials stored" in err:
            inputs["login_site"] = None
            browser_task.login_site = None
            retry = browser_tool.execute(browser_task, inputs)
            if retry.success:
                pending_browser = []
                return True
            result = retry

        print(f"{RED}    Browser failed:{RESET} {result.error or 'Unknown error'}")
        if result.evidence:
            shot = result.evidence.get("screenshot")
            html = result.evidence.get("html")
            if shot:
                print(f"{YELLOW}    Evidence:{RESET} {shot}")
            if html:
                print(f"{YELLOW}    Evidence:{RESET} {html}")
        return False

    steps = list(_iter_steps(playbook_data))
    if not steps:
        print(f"{YELLOW}[INFO]{RESET} Playbook has no steps.")
        return False

    for idx, step in enumerate(steps, 1):
        step_type = str(step.get("type") or "shell").lower()
        desc = step.get("description") or step.get("name") or step_type

        if step_type == "browser":
            # Allow either direct browser actions or nested `browser_steps`.
            if "browser_steps" in step and isinstance(step.get("browser_steps"), list):
                for sub in step["browser_steps"]:
                    if isinstance(sub, dict):
                        pending_browser.append(_coerce_browser_step(sub))
            else:
                pending_browser.append(_coerce_browser_step(step))
            continue

        # Non-browser step: flush any pending browser batch first.
        if not flush_browser():
            return False

        print(f"  Step {idx}: {desc}")
        try:
            if step_type == "shell":
                command = step.get("command") or ""
                result = shell_tool.execute(None, {"command": command})
                if not result.success:
                    print(f"{RED}    Failed:{RESET} {result.error or 'Unknown error'}")
                    stderr = (result.output or {}).get("stderr")
                    if stderr:
                        print(stderr.strip())
                    return False

            elif step_type in {"python", "python_inline"}:
                script = step.get("code") or step.get("script") or ""
                result = python_tool.execute(None, {"script": script})
                if not result.success:
                    print(f"{RED}    Failed:{RESET} {result.error or 'Unknown error'}")
                    stderr = (result.output or {}).get("stderr")
                    if stderr:
                        print(stderr.strip())
                    return False

            elif step_type in {"python_file", "python_script"}:
                path = step.get("path") or step.get("file") or ""
                abs_path = Path(path)
                if not abs_path.is_file():
                    abs_path = (REPO_ROOT / path).resolve()
                if not abs_path.is_file():
                    print(f"{RED}    Failed:{RESET} Missing python file: {path}")
                    return False
                proc = subprocess.run(
                    ["python", str(abs_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    cwd=str(REPO_ROOT),
                )
                if proc.returncode != 0:
                    print(f"{RED}    Failed:{RESET} Exit code {proc.returncode}")
                    if proc.stderr:
                        print(proc.stderr.strip())
                    return False

            elif step_type in {"manual"}:
                print(f"{YELLOW}    Manual step:{RESET} {desc}")

            else:
                print(f"{RED}    Failed:{RESET} Unsupported step type '{step_type}'")
                return False

            print(f"{GREEN}    ✓ Done{RESET}")
        except Exception as exc:
            print(f"{RED}    Error:{RESET} {exc}")
            return False

    # Flush any remaining browser steps
    if not flush_browser():
        return False

    return True


def _context_for_codex(playbooks: dict) -> str:
    lines = ["AGENT CONTEXT:"]

    # Playbooks summary
    if playbooks:
        sample = []
        for _pb_id, pb in list(playbooks.items())[:8]:
            name = pb.get("name") or _pb_id
            triggers = ", ".join((pb.get("triggers") or [])[:2])
            if triggers:
                sample.append(f"{name} (triggers: {triggers})")
            else:
                sample.append(str(name))
        lines.append("Available playbooks: " + "; ".join(sample))

    # Credentials (best-effort)
    try:
        from agent.memory.memory_manager import load_memory

        sites = sorted((load_memory().get("credentials") or {}).keys())
        if sites:
            lines.append("Saved credential sites: " + ", ".join(sites[:20]))
    except Exception:
        pass

    return "\\n".join(lines)


def _normalize_playbook_from_codex(obj: dict, *, fallback_name: str) -> dict:
    pb = dict(obj or {})
    if not pb.get("name"):
        pb["name"] = fallback_name.strip()[:80] or "New Playbook"
    if not pb.get("description"):
        pb["description"] = fallback_name.strip()
    if not isinstance(pb.get("triggers"), list) or not pb.get("triggers"):
        pb["triggers"] = [fallback_name.lower().strip()]
    if not isinstance(pb.get("steps"), list):
        pb["steps"] = []
    pb.setdefault("created", datetime.now().isoformat())
    return pb


def _choose_unique_id(playbooks: dict, base: str) -> str:
    base_id = _slugify(base)
    pb_id = base_id
    i = 2
    while pb_id in playbooks:
        pb_id = f"{base_id}-{i}"
        i += 1
    return pb_id


def mode_execute(command: str) -> None:
    """
    EXECUTE MODE:
    - If a playbook matches: run instantly (no questions, no LLM)
    - Else: use Codex once to generate a deterministic playbook, execute it, then offer to save it
    """
    playbooks = load_playbooks()
    pb_id, pb_data = find_matching_playbook(command, playbooks)

    if pb_data:
        print(f"{GREEN}[FOUND]{RESET} {pb_data.get('name', pb_id)}")
        ok = execute_playbook(pb_id or "playbook", pb_data)
        if ok:
            print(f"{GREEN}[DONE]{RESET} Task completed successfully!")
        else:
            print(f"{RED}[FAILED]{RESET} Task failed. Try 'Learn:' to re-record it.")
        return

    print(f"{YELLOW}[NEW TASK]{RESET} No playbook found. Asking Codex to generate one...")

    prompt = f"""{_context_for_codex(playbooks)}

User command: {command}

You are generating a deterministic playbook for Trey's Agent.

Return ONLY valid JSON (no prose). Schema:
{{
  "name": "Short name",
  "description": "What it does",
  "triggers": ["phrases the user might type"],
  "login_site": "optional site key for stored credentials",
  "steps": [
    {{"type":"shell","description":"...","command":"PowerShell here"}},
    {{"type":"python","description":"...","code":"python -c code here"}},
    {{"type":"browser","description":"...","action":"goto","url":"https://..."}},
    {{"type":"browser","description":"...","action":"click","selector":"css selector"}},
    {{"type":"browser","description":"...","action":"click","text":"visible text"}}
  ]
}}

Rules:
- No secrets; use ${{ENV_VAR}} placeholders if needed.
- Prefer BrowserTool actions: goto, click, click_optional, fill, press, wait_for, sleep, screenshot, extract.
- Keep it minimal and robust."""

    response = _call_codex(prompt, allow_tools=False)
    if response.startswith("[CODEX ERROR]"):
        print(f"{RED}{response}{RESET}")
        return

    obj = _extract_json_object(response)
    if not isinstance(obj, dict):
        print(f"{RED}[CODEX ERROR]{RESET} Could not parse JSON playbook from Codex output.")
        print(response)
        return

    playbook = _normalize_playbook_from_codex(obj, fallback_name=command)
    name = playbook.get("name") or command
    print(f"{CYAN}[GENERATED]{RESET} {name} ({len(playbook.get('steps') or [])} steps)")

    ok = execute_playbook("codex-generated", playbook, run_path=_run_id(name))
    if ok:
        print(f"{GREEN}[DONE]{RESET} Task completed successfully!")
    else:
        print(f"{RED}[FAILED]{RESET} Generated playbook failed. Try 'Learn:' to record it.")
        return

    save = input(f"\\n{YELLOW}Save this as a playbook for next time? (y/n):{RESET} ").strip().lower()
    if save != "y":
        return

    pb_id = _choose_unique_id(playbooks, name)
    playbook["created"] = datetime.now().isoformat()
    playbooks[pb_id] = playbook
    save_playbooks(playbooks)
    print(f"{GREEN}[SAVED]{RESET} Playbook '{name}' saved as '{pb_id}'.")

