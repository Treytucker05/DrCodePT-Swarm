"""
Integration smoke tests for Trey's Agent.

Checks:
1) Ollama connectivity
2) Codex CLI availability
3) Successful plan execution (calculator)
4) Self-healing trigger on a failing plan
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

import requests
import yaml

BASE_DIR = Path(__file__).resolve().parent
RUNS_DIR = BASE_DIR / "runs"
TMP_DIR = BASE_DIR / "tmp_tests"
TMP_DIR.mkdir(exist_ok=True)


def write_yaml(path: Path, data: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def run_supervisor(plan_path: Path) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "agent.supervisor.supervisor", str(plan_path)]
    return subprocess.run(cmd, capture_output=True, text=True)


def latest_run(after_ts: float) -> Path | None:
    if not RUNS_DIR.exists():
        return None
    runs = [p for p in RUNS_DIR.iterdir() if p.is_dir() and p.stat().st_mtime >= after_ts]
    if not runs:
        return None
    return sorted(runs, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def test_ollama():
    try:
        resp = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "qwen2.5:7b-instruct", "prompt": "ping", "stream": False},
            timeout=45,
        )
        data = resp.json()
        ok = resp.status_code == 200 and "response" in data
        return ok, f"status={resp.status_code}"
    except Exception as exc:
        return False, str(exc)


def test_codex():
    try:
        cmd = shutil.which("codex") or shutil.which("codex.ps1") or "codex"
        if str(cmd).lower().endswith(".ps1"):
            proc = subprocess.run(["powershell", "-File", cmd, "--version"], capture_output=True, text=True)
        else:
            proc = subprocess.run([cmd, "--version"], capture_output=True, text=True)
        return proc.returncode == 0, proc.stdout.strip() or proc.stderr.strip()
    except Exception as exc:
        return False, str(exc)


def build_calculator_plan() -> Path:
    plan = {
        "id": "calc-test",
        "name": "Build calculator",
        "type": "shell",
        "goal": "Create a Python calculator program",
        "inputs": {},
        "output": {},
        "definition_of_done": "calculator.py exists and prints a sum",
        "verify": [],
        "allowed_paths": ["."],
        "tools_allowed": ["shell"],
        "stop_rules": {"max_attempts": 2, "max_minutes": 5, "max_tool_calls": 5},
        "on_fail": "retry",
        "command": """$code = @'
import sys
def calc(a, b, op):
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "mul":
        return a * b
    if op == "div":
        return a / b
if __name__ == "__main__":
    print(calc(2, 3, "add"))
'@
Set-Content -Path calculator.py -Value $code -Encoding UTF8
python calculator.py
""",
    }
    path = TMP_DIR / "calculator.yaml"
    write_yaml(path, plan)
    return path


def build_failing_plan() -> Path:
    plan = {
        "id": "fail-test",
        "name": "Create root file",
        "type": "shell",
        "goal": "Create a file at /root/test.txt",
        "inputs": {},
        "output": {},
        "definition_of_done": "file created",
        "verify": [],
        "allowed_paths": ["."],
        "tools_allowed": ["shell"],
        "stop_rules": {"max_attempts": 1, "max_minutes": 2, "max_tool_calls": 2},
        "on_fail": "retry",
        "command": "New-Item -Path /root/test.txt -ItemType File",
    }
    path = TMP_DIR / "failing.yaml"
    write_yaml(path, plan)
    return path


def run_tests():
    results = []

    ok, info = test_ollama()
    results.append(("Ollama connection", ok, info))

    ok, info = test_codex()
    results.append(("Codex CLI", ok, info))

    calc_plan = build_calculator_plan()
    proc_calc = run_supervisor(calc_plan)
    results.append(("Calculator plan", proc_calc.returncode == 0, proc_calc.stdout.strip() or proc_calc.stderr.strip()))

    failing_plan = build_failing_plan()
    ts = time.time()
    proc_fail = run_supervisor(failing_plan)
    run_dir = latest_run(ts)
    healed = False
    if run_dir:
        heal_dir = run_dir / "self_heal"
        healed = (heal_dir / "corrected_plan.yaml").exists() or (run_dir / "healing_log.jsonl").exists()
    results.append(("Self-healing attempt", healed or proc_fail.returncode == 0, proc_fail.stdout.strip() or proc_fail.stderr.strip()))

    for name, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name} - {detail}")

    overall = all(r[1] for r in results)
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    run_tests()
