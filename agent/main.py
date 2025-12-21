from __future__ import annotations

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
if str(ROOT.parent) not in sys.path:
    sys.path.append(str(ROOT.parent))

from agent.schemas.task_schema import Task, TaskDefinition, load_task_from_yaml
from agent.supervisor.supervisor import run_task
from agent.agent_logging.run_logger import init_run, log_event, finalize_run
from agent.learning.learning_store import load_playbook

load_dotenv()

ROOT = Path(__file__).resolve().parent
TASKS_DIR = ROOT / "tasks"
RUNS_DIR = ROOT / "runs"
FAILURES_DIR = ROOT / "failures"
HANDOFF_DIR = ROOT / "handoff"
PLAYBOOK_DIR = ROOT / "memory" / "site_playbooks"
ENV_PATH = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

CLS = "cls" if os.name == "nt" else "clear"


def clear():
    os.system(CLS)


# ---------------- Self-check ----------------
def check_task_schema() -> Tuple[bool, str]:
    file_path = ROOT / "schemas" / "task_schema.py"
    if not file_path.is_file():
        return False, "Missing schemas/task_schema.py"
    try:
        for sample in ["example_browser_task.yaml", "example_shell_task.yaml", "example_composite_task.yaml", "test_shell.yaml", "test_handoff.yaml"]:
            path = TASKS_DIR / sample
            if path.is_file():
                load_task_from_yaml(str(path))
    except Exception as exc:
        return False, f"Validation failed: {exc}"
    return True, ""


def check_tools() -> Tuple[bool, str]:
    required = ["base.py", "browser.py", "fs.py", "shell.py", "python_exec.py", "api.py", "registry.py"]
    missing = [f for f in required if not (ROOT / "tools" / f).is_file()]
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, ""


def check_logging() -> Tuple[bool, str]:
    path = ROOT / "logging" / "run_logger.py"
    if not path.is_file():
        return False, "Missing logging/run_logger.py"
    return True, ""


def check_verifiers() -> Tuple[bool, str]:
    required = ["base.py", "file_exists.py", "json_has_entries.py", "text_in_file.py", "page_contains.py", "command_exit_zero.py", "api_status_ok.py", "registry.py"]
    missing = [f for f in required if not (ROOT / "verifiers" / f).is_file()]
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, ""


def check_evidence() -> Tuple[bool, str]:
    if not (ROOT / "evidence" / "capture.py").is_file():
        return False, "Missing evidence/capture.py"
    return True, ""


def check_supervisor() -> Tuple[bool, str]:
    if not (ROOT / "supervisor" / "supervisor.py").is_file():
        return False, "Missing supervisor/supervisor.py"
    return True, ""


def check_learning() -> Tuple[bool, str]:
    if not (ROOT / "learning" / "learning_store.py").is_file():
        return False, "Missing learning/learning_store.py"
    return True, ""


def check_hardening() -> Tuple[bool, str]:
    if not (ROOT / "supervisor" / "hardening.py").is_file():
        return False, "Missing supervisor/hardening.py"
    return True, ""


def check_sessions() -> Tuple[bool, str]:
    if not (ROOT / "sessions").is_dir():
        return False, "sessions/ folder missing"
    return True, ""


def check_secrets() -> Tuple[bool, str]:
    if not ENV_EXAMPLE.is_file():
        return False, ".env.example missing"
    # .env optional but recommended
    return True, ""


def check_tasks() -> Tuple[bool, str]:
    needed = [
        "example_browser_task.yaml",
        "example_shell_task.yaml",
        "example_composite_task.yaml",
        "test_shell.yaml",
        "test_handoff.yaml",
    ]
    missing = [t for t in needed if not (TASKS_DIR / t).is_file()]
    if missing:
        return False, f"Missing example tasks: {', '.join(missing)}"
    try:
        for t in needed:
            if (TASKS_DIR / t).is_file():
                load_task_from_yaml(str(TASKS_DIR / t))
    except Exception as exc:
        return False, f"Task validation failed: {exc}"
    return True, ""


def run_self_check() -> List[Tuple[str, bool, str]]:
    checks = [
        ("Task Schema", check_task_schema),
        ("Tool Bus", check_tools),
        ("Run Logging", check_logging),
        ("Verifiers", check_verifiers),
        ("Evidence Capture", check_evidence),
        ("Supervisor Loop", check_supervisor),
        ("Learning Store", check_learning),
        ("Hardening", check_hardening),
        ("Sessions", check_sessions),
        ("Secrets", check_secrets),
        ("Tasks", check_tasks),
    ]
    results = []
    for name, fn in checks:
        ok, msg = fn()
        results.append((name, ok, msg))
    return results


# ---------------- Helpers ----------------
def pause():
    input("\n[Press Enter to continue]")


def list_task_files() -> List[Path]:
    return sorted(TASKS_DIR.glob("*.yaml"))


def show_tasks():
    clear()
    print("Tasks:\n")
    for idx, path in enumerate(list_task_files(), 1):
        try:
            t = load_task_from_yaml(str(path))
            print(f"{idx}. {t.id} | {t.type.value} | {t.goal[:80]}")
        except Exception:
            print(f"{idx}. {path.name} (failed to load)")
    pause()


def view_task_yaml():
    clear()
    files = list_task_files()
    if not files:
        print("No tasks found.")
        pause()
        return
    for idx, f in enumerate(files, 1):
        print(f"{idx}. {f.name}")
    choice = input("\nSelect task #: ")
    if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
        return
    path = files[int(choice) - 1]
    clear()
    print(path.read_text(encoding="utf-8"))
    pause()


def run_task_menu():
    clear()
    files = list_task_files()
    if not files:
        print("No tasks available.")
        pause()
        return
    for idx, f in enumerate(files, 1):
        print(f"{idx}. {f.name}")
    choice = input("\nSelect task #: ")
    if not choice.isdigit() or not (1 <= int(choice) <= len(files)):
        return
    path = files[int(choice) - 1]
    clear()
    print(f"Running {path.name}...\n")
    try:
        run_task(str(path))
        print("\nTask finished. Check runs/ for details.")
    except Exception as exc:
        print(f"Error running task: {exc}")
    pause()


def create_task():
    clear()
    print("Create New Task\n")
    id_ = input("id: ").strip()
    name = input("name: ").strip()
    ttype = input("type (browser|shell|python|fs|api|composite): ").strip()
    goal = input("goal: ").strip()
    definition_of_done = input("definition_of_done: ").strip()
    on_fail = input("on_fail (retry|escalate|abort): ").strip()
    allowed_paths = input("allowed_paths (comma-separated, blank for none): ").strip().split(",") if input else []
    tools_allowed = input("tools_allowed (comma-separated): ").strip().split(",")
    stop_rules = {
        "max_attempts": int(input("stop_rules.max_attempts: ").strip() or "3"),
        "max_minutes": int(input("stop_rules.max_minutes: ").strip() or "5"),
        "max_tool_calls": int(input("stop_rules.max_tool_calls: ").strip() or "10"),
    }
    verify = []
    verify_add = input("Add verify? (y/n): ").strip().lower()
    while verify_add == "y":
        vid = input("  verifier id: ").strip()
        args_raw = input("  args as JSON (e.g., {\"text\": \"Welcome\"}): ").strip() or "{}"
        try:
            args = json.loads(args_raw)
        except json.JSONDecodeError:
            args = {}
        verify.append({"id": vid, "args": args})
        verify_add = input("Add another? (y/n): ").strip().lower()

    extra = {}
    if ttype == "browser":
        extra["url"] = input("url: ").strip()
    if ttype == "shell":
        extra["command"] = input("command: ").strip()
    if ttype == "python":
        extra["script"] = input("script: ").strip()
    if ttype == "fs":
        extra["path"] = input("path: ").strip()
    if ttype == "api":
        extra["endpoint"] = input("endpoint: ").strip()
        extra["method"] = input("method (GET/POST/PUT/DELETE): ").strip().upper() or "GET"
    if ttype == "composite":
        print("Composite steps not supported in quick create; please edit YAML manually.")

    data = {
        "id": id_,
        "name": name,
        "type": ttype,
        "goal": goal,
        "inputs": {},
        "output": {},
        "definition_of_done": definition_of_done,
        "verify": verify,
        "allowed_paths": [p for p in allowed_paths if p.strip()],
        "tools_allowed": [t.strip() for t in tools_allowed if t.strip()],
        "stop_rules": stop_rules,
        "on_fail": on_fail,
    }
    data.update(extra)

    try:
        task = TaskDefinition.parse_obj(data)
        out_path = TASKS_DIR / f"{id_}.yaml"
        TASKS_DIR.mkdir(parents=True, exist_ok=True)
        import yaml as _yaml

        out_path.write_text(_yaml.safe_dump(task.dict()), encoding="utf-8")
        print(f"Saved to {out_path}")
    except Exception as exc:
        print(f"Validation failed: {exc}")
    pause()


def list_runs():
    clear()
    runs = sorted([p for p in RUNS_DIR.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    if not runs:
        print("No runs.")
        pause()
        return
    for idx, r in enumerate(runs, 1):
        print(f"{idx}. {r.name}")
    choice = input("\nSelect run # to view summary (or Enter to return): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(runs):
        r = runs[int(choice) - 1]
        clear()
        summary = (r / "summary.md").read_text(encoding="utf-8") if (r / "summary.md").is_file() else "(no summary)"
        print(summary)
        if input("\nView events.jsonl? (y/n): ").strip().lower() == "y":
            events = (r / "events.jsonl").read_text(encoding="utf-8") if (r / "events.jsonl").is_file() else "(no events)"
            print("\n--- events.jsonl ---\n")
            print(events)
    pause()


def view_failures():
    clear()
    fails = sorted([p for p in FAILURES_DIR.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    if not fails:
        print("No failures.")
        pause()
        return
    for idx, f in enumerate(fails, 1):
        print(f"{idx}. {f.name}")
    choice = input("\nSelect failure # to view escalation.yaml (or Enter to return): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(fails):
        f = fails[int(choice) - 1]
        esc = f / "escalation.yaml"
        clear()
        print(esc.read_text(encoding="utf-8") if esc.is_file() else "(no escalation.yaml)")
    pause()


def handoff_status():
    clear()
    wait = HANDOFF_DIR / "WAITING.yaml"
    if wait.is_file():
        print("WAITING.yaml present:\n")
        print(wait.read_text(encoding="utf-8"))
    else:
        print("No pending handoffs.")
    pause()


def handoff_continue():
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    flag = HANDOFF_DIR / "CONTINUE.flag"
    flag.write_text("resume", encoding="utf-8")
    clear()
    print("CONTINUE.flag created.")
    pause()


def view_playbooks():
    clear()
    files = sorted(PLAYBOOK_DIR.glob("*.yaml"))
    if not files:
        print("No playbooks.")
        pause()
        return
    for idx, f in enumerate(files, 1):
        print(f"{idx}. {f.name}")
    choice = input("\nSelect playbook # to view (or Enter to return): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        f = files[int(choice) - 1]
        clear()
        print(f.read_text(encoding="utf-8"))
        if input("\nOpen in Notepad? (y/n): ").strip().lower() == "y":
            os.system(f'notepad "{f}"')
    pause()


def self_check_menu():
    clear()
    results = run_self_check()
    print("Self-Check Results:\n")
    for name, ok, msg in results:
        status = "Γ£à" if ok else "Γ¥î"
        print(f"{status} {name} - {msg}")
    pause()


def record_session_menu():
    clear()
    print("Record Browser Session\n")
    print("This will open a browser and record your actions.")
    print("A playbook will be generated when you close the browser.\n")
    
    site = input("Site name (e.g., blackboard, google): ").strip()
    if not site:
        print("Cancelled.")
        pause()
        return
    
    url = input("Starting URL (or Enter for blank): ").strip()
    
    print(f"\nStarting recorder for '{site}'...")
    print("Close the browser window when done.\n")
    
    try:
        from agent.recorder import run_recorder
        run_recorder(site, start_url=url)
    except Exception as exc:
        print(f"Error: {exc}")
    
    pause()


def capture_session_menu():
    clear()
    print("Capture Login Session\n")
    print("This will open a browser for you to log in manually.")
    print("The session will be saved when you close the browser.\n")
    
    site = input("Site name (e.g., blackboard): ").strip()
    if not site:
        print("Cancelled.")
        pause()
        return
    
    url = input("Login URL: ").strip()
    if not url:
        print("URL required.")
        pause()
        return
    
    print(f"\nOpening browser for '{site}'...")
    print("Log in, then close the browser to save session.\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "agent.sessions.capture_session",
            "--site", site,
            "--url", url
        ], capture_output=False)
    except Exception as exc:
        print(f"Error: {exc}")
    
    pause()


def main_menu():
    while True:
        clear()
        print("=" * 42)
        print("        DrCodePT Agent System")
        print("=" * 42 + "\n")
        print("  [1] Run Task")
        print("  [2] List Tasks")
        print("  [3] Create New Task")
        print("  [4] View Runs")
        print("  [5] View Failures")
        print("  [6] Check Handoff Status")
        print("  [7] Continue Handoff (create flag)")
        print("  [8] View Playbooks")
        print("  [9] Self-Check System")
        print("  [R] Record Browser Session")
        print("  [S] Capture Login Session")
        print("  [0] Exit\n")
        choice = input("Select option: ").strip().lower()
        if choice == "1":
            run_task_menu()
        elif choice == "2":
            show_tasks()
        elif choice == "3":
            create_task()
        elif choice == "4":
            list_runs()
        elif choice == "5":
            view_failures()
        elif choice == "6":
            handoff_status()
        elif choice == "7":
            handoff_continue()
        elif choice == "8":
            view_playbooks()
        elif choice == "9":
            self_check_menu()
        elif choice == "r":
            record_session_menu()
        elif choice == "s":
            capture_session_menu()
        elif choice == "0":
            clear()
            sys.exit(0)
        else:
            continue


if __name__ == "__main__":
    args = sys.argv[1:]
    # Flags:
    # --menu / -m : open the DrCodePT menu
    # default    : launch Codex CLI (LAUNCH_CODEX.bat) if present; fallback to Agent_CLI.bat; otherwise menu
    if any(a in {"--menu", "-m"} for a in args):
        main_menu()
    else:
        launch = ROOT.parent / "LAUNCH_CODEX.bat"
        fallback = ROOT.parent / "Agent_CLI.bat"
        target = launch if launch.is_file() else fallback if fallback.is_file() else None
        if target:
            rc = subprocess.call(str(target), shell=True)
            if rc != 0:
                print(f"{target.name} exited with code {rc}, falling back to menu.")
                main_menu()
        else:
            main_menu()
