"""
Swarm smoke test: runs a tiny swarm objective and verifies run artifacts.

Usage:
  python scripts/swarm_smoke_test.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _latest_run_dir(runs_root: Path, before: set[str]) -> Path | None:
    candidates = [p for p in runs_root.glob("*") if p.is_dir() and p.name not in before]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    runs_root = repo_root / "runs" / "swarm"
    runs_root.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in runs_root.glob("*") if p.is_dir()}

    os.environ.setdefault("SWARM_MAX_WORKERS", "2")
    os.environ.setdefault("SWARM_MAX_SUBTASKS", "2")
    os.environ.setdefault("SWARM_SUMMARIZE", "0")
    os.environ.setdefault("SWARM_LLM_PLAN_TIMEOUT_SECONDS", "30")
    os.environ.setdefault("SWARM_LLM_PLAN_RETRY_TIMEOUT_SECONDS", "10")

    sys.path.insert(0, str(repo_root))
    from agent.modes.swarm import mode_swarm

    mode_swarm("Return a short hello message.", unsafe_mode=False)

    run_dir = _latest_run_dir(runs_root, before)
    if run_dir is None:
        print("FAIL: no new swarm run folder created")
        return 1

    sub_runs = [p for p in run_dir.iterdir() if p.is_dir()]
    if not sub_runs:
        print(f"FAIL: no subagent run folders found under {run_dir}")
        return 1

    missing = []
    for sub in sub_runs:
        if not (sub / "trace.jsonl").is_file():
            missing.append(f"{sub}\\trace.jsonl")
        if not (sub / "result.json").is_file():
            missing.append(f"{sub}\\result.json")
    if missing:
        print("FAIL: missing artifacts:")
        for path in missing:
            print(f" - {path}")
        return 1

    print(f"PASS: swarm artifacts present for {len(sub_runs)} subagents in {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
