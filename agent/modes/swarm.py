from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, replace
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import traceback

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.isolation import (
    WorktreeInfo,
    copy_repo_to_workspace,
    create_worktree,
    remove_worktree,
    sanitize_branch_name,
)
from agent.autonomous.qa import QaResult, format_qa_summary, validate_artifacts
import subprocess
from agent.autonomous.manifest import write_run_manifest
from agent.autonomous.repo_scan import is_repo_review_task
from agent.config.profile import resolve_profile
from agent.autonomous.runner import AgentRunner
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm import schemas as llm_schemas


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        return


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or not str(val).strip():
        return default
    try:
        return int(str(val).strip())
    except Exception:
        return default


def _split_paths(raw: str) -> list[Path]:
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    return [Path(p) for p in parts]


def _choose_planner_mode(task: str) -> str:
    text = (task or "").strip().lower()
    if not text:
        return "react"
    words = [w for w in re.split(r"\s+", text) if w]
    word_count = len(words)
    conjunctions = (" and ", " then ", " after ", " before ", " also ", " plus ")
    plan_keywords = (
        "plan",
        "steps",
        "roadmap",
        "multi-step",
        "implement",
        "build",
        "create",
        "setup",
        "configure",
        "migrate",
        "refactor",
        "research",
        "compare",
        "analyze",
        "summarize",
    )
    if word_count >= 12:
        return "plan_first"
    if any(k in text for k in conjunctions):
        return "plan_first"
    if text.count(",") >= 2 or ":" in text or ";" in text:
        return "plan_first"
    if any(k in text for k in plan_keywords):
        return "plan_first"
    return "react"


def _default_allowed_roots(repo_root: Path) -> Tuple[Path, ...]:
    return (repo_root,)


def _build_agent_cfg(repo_root: Path, *, unsafe_mode: bool, profile_name: str | None) -> AgentConfig:
    profile = resolve_profile(profile_name, env_keys=("SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    fs_anywhere = _bool_env("SWARM_FS_ANYWHERE", _bool_env("AUTO_FS_ANYWHERE", False))
    raw_roots = os.getenv("SWARM_FS_ALLOWED_ROOTS") or os.getenv("AUTO_FS_ALLOWED_ROOTS") or ""
    allowed_roots = _split_paths(raw_roots) if raw_roots.strip() else list(_default_allowed_roots(repo_root))
    return AgentConfig(
        unsafe_mode=bool(unsafe_mode),
        enable_web_gui=_bool_env("SWARM_ENABLE_WEB_GUI", _bool_env("AUTO_ENABLE_WEB_GUI", False)),
        enable_desktop=_bool_env("SWARM_ENABLE_DESKTOP", _bool_env("AUTO_ENABLE_DESKTOP", False)),
        pre_mortem_enabled=_bool_env("SWARM_PRE_MORTEM", _bool_env("AUTO_PRE_MORTEM", False)),
        allow_user_info_storage=_bool_env(
            "SWARM_ALLOW_USER_INFO_STORAGE", _bool_env("AUTO_ALLOW_USER_INFO_STORAGE", False)
        ),
        allow_human_ask=bool(profile.allow_interactive),
        allow_fs_anywhere=fs_anywhere,
        fs_allowed_roots=tuple(allowed_roots),
        profile=profile,
    )


def _build_runner_cfg(profile_name: str | None) -> RunnerConfig:
    profile = resolve_profile(profile_name, env_keys=("SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    max_steps = _int_env("SWARM_MAX_STEPS", _int_env("AUTO_MAX_STEPS", 30))
    timeout_seconds = _int_env("SWARM_TIMEOUT_SECONDS", _int_env("AUTO_TIMEOUT_SECONDS", 600))
    heartbeat = _int_env("SWARM_LLM_HEARTBEAT_SECONDS", profile.heartbeat_s)
    plan_timeout = _int_env("SWARM_LLM_PLAN_TIMEOUT_SECONDS", profile.plan_timeout_s)
    retry_timeout = _int_env("SWARM_LLM_PLAN_RETRY_TIMEOUT_SECONDS", profile.plan_retry_timeout_s)
    return RunnerConfig(
        max_steps=max_steps,
        timeout_seconds=timeout_seconds,
        llm_heartbeat_seconds=heartbeat,
        llm_plan_timeout_seconds=plan_timeout,
        llm_plan_retry_timeout_seconds=retry_timeout,
    )


def _planner_mode_for(task: str) -> str:
    mode = (os.getenv("SWARM_PLANNER_MODE") or "auto").strip().lower()
    if mode == "auto":
        return _choose_planner_mode(task)
    return mode if mode in {"react", "plan_first"} else "react"


def _swarm_run_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    return repo_root / "runs" / "swarm" / run_id


@dataclass
class Subtask:
    id: str
    goal: str
    depends_on: List[str]
    notes: str


def _decompose(llm: CodexCliClient, objective: str, *, max_items: int) -> List[Subtask]:
    prompt = (
        "You are a swarm coordinator. Decompose the objective into 2-4 parallelizable subtasks.\n"
        "Only add dependencies when truly required. Use short IDs like A, B, C.\n"
        "If the objective is a repo review, require a repo_index/repo_map stage and review only selected files.\n"
        "Never ask to read the entire repo; cap reviews to the repo_map selection.\n"
        f"Objective: {objective}\n"
        "Return JSON only."
    )
    data = llm.reason_json(prompt, schema_path=llm_schemas.TASK_DECOMPOSITION)
    raw = data.get("subtasks") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return []
    items: List[Subtask] = []
    for idx, entry in enumerate(raw[:max_items], 1):
        if not isinstance(entry, dict):
            continue
        sid = str(entry.get("id") or f"S{idx}").strip()
        goal = str(entry.get("goal") or "").strip()
        if not goal:
            continue
        depends_on = entry.get("depends_on")
        if not isinstance(depends_on, list):
            depends_on = []
        notes = str(entry.get("notes") or "").strip()
        items.append(Subtask(id=sid, goal=goal, depends_on=[str(d) for d in depends_on], notes=notes))
    return items


def _ensure_repo_scan_subtask(subtasks: List[Subtask], *, objective: str, max_items: int) -> None:
    if not is_repo_review_task(objective):
        return
    repo_goal = (
        "Stage A: use repo_index.json and repo_map.json in this run directory. "
        "Only read files listed in repo_map.json (no broad globbing). "
        "Write A_findings.json summarizing repo structure, key files, and risks."
    )
    a_task = next((s for s in subtasks if s.id.strip().upper() == "A"), None)
    if a_task is None:
        if len(subtasks) < max_items:
            subtasks.insert(0, Subtask(id="A", goal=repo_goal, depends_on=[], notes=""))
            return
        a_task = subtasks[0]
        old_id = a_task.id
        a_task.id = "A"
        for s in subtasks[1:]:
            s.depends_on = ["A" if d == old_id else d for d in s.depends_on]
    if repo_goal not in a_task.goal:
        a_task.goal = f"{repo_goal}\n\n{a_task.goal}".strip()


def _select_isolation_mode(profile_name: str, explicit: str | None) -> str:
    raw = (explicit or os.getenv("SWARM_ISOLATION") or "").strip().lower()
    if raw in {"none", "sandbox", "worktree"}:
        return raw
    if profile_name in {"deep", "audit"}:
        return "sandbox"
    return "none"


def _workspace_note(goal: str, workspace: Path) -> str:
    note = (
        "Use the isolated workspace at:\n"
        f"{workspace}\n"
        "All file operations should stay inside this workspace."
    )
    return f"{note}\n\n{goal}".strip()


def _build_isolated_agent_cfg(agent_cfg: AgentConfig, *, repo_root: Path, workspace: Path) -> AgentConfig:
    roots = [r for r in agent_cfg.fs_allowed_roots if r != repo_root]
    if workspace not in roots:
        roots.append(workspace)
    return replace(agent_cfg, fs_allowed_roots=tuple(roots))


def _expected_artifacts_for(subtask: Subtask) -> List[str]:
    expected = ["result.json", "trace.jsonl"]
    goal = subtask.goal.lower()
    if "repo_map" in goal or "repo_index" in goal:
        expected.extend(["repo_index.json", "repo_map.json"])
    if "a_findings" in goal or subtask.id.strip().upper() == "A":
        expected.append("A_findings.json")
    return list(dict.fromkeys(expected))


def _should_run_tests(objective: str, subtasks: Iterable[Subtask]) -> bool:
    text = (objective or "").lower()
    keywords = (
        "implement",
        "refactor",
        "fix",
        "change",
        "modify",
        "update",
        "code",
        "add",
        "remove",
    )
    if any(k in text for k in keywords):
        return True
    for sub in subtasks:
        goal = sub.goal.lower()
        if any(k in goal for k in keywords):
            return True
    return False


def _build_reduced_goal(
    subtask: Subtask,
    *,
    failed_deps: List[str],
    results_by_id: Dict[str, Dict[str, Any]],
    run_dirs_by_id: Dict[str, Path],
    subtasks_by_id: Dict[str, Subtask],
) -> str:
    lines = [
        "Reduced synthesis mode: one or more dependencies failed.",
        "Summarize what failed and why based on available result.json/trace.jsonl.",
        "List missing artifacts per dependency.",
        "Propose next-run objectives and minimal inputs needed.",
        "",
        f"Failed dependencies: {', '.join(failed_deps)}",
        "Failure details:",
    ]
    for dep in failed_deps:
        result = results_by_id.get(dep, {})
        reason = ""
        if isinstance(result.get("error"), dict):
            err = result.get("error") or {}
            reason = err.get("message") or err.get("type") or ""
        reason = reason or str(result.get("stop_reason") or result.get("reason") or "unknown")
        lines.append(f"- {dep}: {reason}")
    lines.append("")
    lines.append("Missing artifacts:")
    for dep in failed_deps:
        dep_task = subtasks_by_id.get(dep, Subtask(id=dep, goal="", depends_on=[], notes=""))
        dep_dir = run_dirs_by_id.get(dep)
        expected = _expected_artifacts_for(dep_task)
        missing = []
        if dep_dir is not None:
            for name in expected:
                if not (dep_dir / name).exists():
                    missing.append(name)
        if missing:
            lines.append(f"- {dep}: {missing}")
    lines.append("")
    lines.append("Original goal (for context only):")
    lines.append(subtask.goal)
    return "\n".join(lines)


def _trace_tail(trace_path: str, *, max_lines: int = 200) -> List[dict]:
    try:
        path = Path(trace_path)
        if not path.is_file():
            return []
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = lines[-max_lines:]
        events: List[dict] = []
        for line in tail:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except Exception:
                continue
            if evt.get("type") in {"finish", "stop", "error_report", "tool_retry", "observation"}:
                events.append(evt)
        return events[-40:]
    except Exception:
        return []


def _read_result(run_dir: Path) -> Dict[str, Any]:
    try:
        path = run_dir / "result.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _write_result(run_dir: Path, payload: Dict[str, Any]) -> None:
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "result.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _run_subagent(
    subtask: Subtask,
    *,
    repo_root: Path,
    run_dir: Path,
    agent_cfg: AgentConfig,
    runner_cfg: RunnerConfig,
    unsafe_mode: bool,
    workdir: Optional[Path] = None,
) -> tuple[Subtask, str, str, Path]:
    # Threaded swarm runs must never mutate process-global state (e.g., os.chdir).
    planner_mode = _planner_mode_for(subtask.goal)
    planner_cfg = PlannerConfig(
        mode=planner_mode,  # type: ignore[arg-type]
        num_candidates=_int_env("SWARM_NUM_CANDIDATES", _int_env("AUTO_NUM_CANDIDATES", 1)),
        max_plan_steps=_int_env("SWARM_MAX_PLAN_STEPS", _int_env("AUTO_MAX_PLAN_STEPS", 6)),
    )
    try:
        llm = CodexCliClient.from_env(workdir=workdir or repo_root, log_dir=run_dir)
    except (CodexCliNotFoundError, CodexCliAuthError) as exc:
        return subtask, "failed", f"llm_error: {exc}", ""

    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        run_dir=run_dir,
        mode_name="swarm_subagent",
        agent_id=subtask.id,
    )
    result = runner.run(subtask.goal)
    status = "success" if result.success else "failed"
    return subtask, status, result.stop_reason or "", run_dir


def mode_swarm(
    objective: str,
    *,
    unsafe_mode: bool = False,
    profile: str | None = None,
    isolation: str | None = None,
    cleanup_worktrees: bool | None = None,
) -> None:
    _load_dotenv()
    try:
        llm = CodexCliClient.from_env()
    except CodexCliNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return
    except CodexCliAuthError as exc:
        print(f"[ERROR] {exc}")
        return

    repo_root = Path(__file__).resolve().parents[2]
    run_root = _swarm_run_dir()
    run_root.mkdir(parents=True, exist_ok=True)

    max_subtasks = max(1, _int_env("SWARM_MAX_SUBTASKS", 3))
    profile_cfg = resolve_profile(profile, env_keys=("SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    workers = max(1, _int_env("SWARM_MAX_WORKERS", profile_cfg.workers))
    isolation_mode = _select_isolation_mode(profile_cfg.name, isolation)
    cleanup_worktrees = (
        bool(cleanup_worktrees)
        if cleanup_worktrees is not None
        else _bool_env("SWARM_CLEANUP_WORKTREES", False)
    )

    llm = llm.with_context(workdir=repo_root, log_dir=run_root)
    subtasks = _decompose(llm, objective, max_items=max_subtasks)
    if not subtasks:
        print("[SWARM] Could not decompose; running as a single Auto task.")
        from agent.modes.autonomous import mode_autonomous

        mode_autonomous(objective, unsafe_mode=unsafe_mode)
        return
    _ensure_repo_scan_subtask(subtasks, objective=objective, max_items=max_subtasks)

    print(f"\n[SWARM] Objective: {objective}")
    print(f"[SWARM] Subtasks: {len(subtasks)} | Workers: {workers}")
    for s in subtasks:
        deps = f" (deps: {', '.join(s.depends_on)})" if s.depends_on else ""
        print(f"  - {s.id}: {s.goal}{deps}")

    agent_cfg = _build_agent_cfg(repo_root, unsafe_mode=unsafe_mode, profile_name=profile)
    runner_cfg = _build_runner_cfg(profile)
    write_run_manifest(
        run_root,
        run_id=run_root.name,
        profile=profile_cfg,
        runner_cfg=runner_cfg,
        workers=workers,
        mode="swarm",
    )
    if not agent_cfg.enable_web_gui and not agent_cfg.enable_desktop:
        print("[SWARM] MCP-based tools disabled (web_gui/desktop). Using local file/Python/web_fetch tools only.")

    remaining: Dict[str, Subtask] = {s.id: s for s in subtasks}
    completed: set[str] = set()
    results: List[tuple[Subtask, str, str, Path]] = []
    results_by_id: Dict[str, Dict[str, Any]] = {}
    run_dirs_by_id: Dict[str, Path] = {}
    status_by_id: Dict[str, str] = {}
    subtasks_by_id: Dict[str, Subtask] = {s.id: s for s in subtasks}
    worktrees_by_id: Dict[str, WorktreeInfo] = {}

    while remaining:
        ready = [s for s in remaining.values() if all(d in completed for d in s.depends_on)]
        if not ready:
            ready = list(remaining.values())

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map: Dict[Any, tuple[Subtask, Path]] = {}
            for s in ready:
                dep_failures = [d for d in s.depends_on if status_by_id.get(d) == "failed"]
                subtask = s
                if dep_failures:
                    reduced_goal = _build_reduced_goal(
                        s,
                        failed_deps=dep_failures,
                        results_by_id=results_by_id,
                        run_dirs_by_id=run_dirs_by_id,
                        subtasks_by_id=subtasks_by_id,
                    )
                    subtask = Subtask(id=s.id, goal=reduced_goal, depends_on=s.depends_on, notes=s.notes)
                sub_dir = run_root / f"{s.id}_{uuid4().hex[:6]}"
                sub_dir.mkdir(parents=True, exist_ok=True)
                workdir = repo_root
                sub_agent_cfg = agent_cfg
                if isolation_mode != "none":
                    workspace_dir = sub_dir / "workspace"
                    workspace_dir.mkdir(parents=True, exist_ok=True)
                    if isolation_mode == "sandbox":
                        copy_repo_to_workspace(repo_root, workspace_dir)
                    elif isolation_mode == "worktree":
                        branch = sanitize_branch_name(f"swarm/{run_root.name}/{s.id}-{uuid4().hex[:6]}")
                        info = create_worktree(repo_root, workspace_dir, branch)
                        worktrees_by_id[s.id] = info
                    workdir = workspace_dir
                    sub_agent_cfg = _build_isolated_agent_cfg(agent_cfg, repo_root=repo_root, workspace=workspace_dir)
                    subtask = Subtask(
                        id=subtask.id,
                        goal=_workspace_note(subtask.goal, workspace_dir),
                        depends_on=subtask.depends_on,
                        notes=subtask.notes,
                    )
                future = executor.submit(
                    _run_subagent,
                    subtask,
                    repo_root=repo_root,
                    run_dir=sub_dir,
                    agent_cfg=sub_agent_cfg,
                    runner_cfg=runner_cfg,
                    unsafe_mode=unsafe_mode,
                    workdir=workdir,
                )
                future_map[future] = (s, sub_dir)

            for future in as_completed(future_map):
                subtask, fallback_dir = future_map[future]
                try:
                    subtask, status, stop_reason, sub_run_dir = future.result()
                except Exception as exc:
                    sub_run_dir = fallback_dir
                    _write_result(
                        sub_run_dir,
                        {
                            "ok": False,
                            "mode": "swarm_subagent",
                            "agent_id": subtask.id,
                            "run_id": subtask.id,
                            "error": {
                                "type": type(exc).__name__,
                                "message": str(exc),
                                "traceback": traceback.format_exc(),
                            },
                        },
                    )
                    status = "failed"
                    stop_reason = f"exception:{type(exc).__name__}"
                results.append((subtask, status, stop_reason, sub_run_dir))
                run_dirs_by_id[subtask.id] = sub_run_dir
                results_by_id[subtask.id] = _read_result(sub_run_dir)
                status_by_id[subtask.id] = "success" if status == "success" else "failed"
                completed.add(subtask.id)
                if subtask.id in remaining:
                    del remaining[subtask.id]
                if cleanup_worktrees and subtask.id in worktrees_by_id:
                    remove_worktree(repo_root, worktrees_by_id[subtask.id])

    print("\n[SWARM] Results:")
    for subtask, status, stop_reason, sub_run_dir in results:
        # result.json is the canonical outcome; terminal output is a convenience.
        result_data = _read_result(sub_run_dir)
        ok = result_data.get("ok")
        if isinstance(ok, bool):
            status = "success" if ok else "failed"
        if isinstance(result_data.get("error"), dict):
            err = result_data["error"]
            stop_reason = err.get("message") or err.get("type") or stop_reason
            data = err.get("data") if isinstance(err, dict) else None
            if isinstance(data, dict) and data.get("questions"):
                stop_reason = f"{stop_reason} | questions: {data.get('questions')}"
        line = f"- {subtask.id}: {status}"
        if stop_reason:
            line += f" | {stop_reason}"
        print(line)
        trace_path = sub_run_dir / "trace.jsonl"
        if trace_path.is_file():
            print(f"  trace: {trace_path}")

    if _bool_env("SWARM_SUMMARIZE", True):
        tails = []
        for subtask, status, stop_reason, sub_run_dir in results:
            result_data = _read_result(sub_run_dir)
            ok = result_data.get("ok")
            if isinstance(ok, bool):
                status = "success" if ok else "failed"
            if isinstance(result_data.get("error"), dict):
                err = result_data["error"]
                stop_reason = err.get("message") or err.get("type") or stop_reason
                data = err.get("data") if isinstance(err, dict) else None
                if isinstance(data, dict) and data.get("questions"):
                    stop_reason = f"{stop_reason} | questions: {data.get('questions')}"
            trace_path = sub_run_dir / "trace.jsonl"
            if trace_path.is_file():
                tails.append(
                    {
                        "id": subtask.id,
                        "goal": subtask.goal,
                        "status": status,
                        "stop_reason": stop_reason,
                        "trace_tail": _trace_tail(str(trace_path)),
                    }
                )
        prompt = (
            "Summarize the swarm results and propose next steps.\n"
            "Be concise and action-oriented.\n\n"
            f"Objective: {objective}\n"
            f"Subtask results: {json.dumps(tails, ensure_ascii=False)}\n"
        )
        data = llm.reason_json(prompt, schema_path=llm_schemas.CHAT_RESPONSE)
        if isinstance(data, dict):
            summary = (data.get("response") or "").strip()
            if summary:
                print("\n[SWARM] Summary:")
                print(summary)

    # QA validation
    qa_results: Dict[str, QaResult] = {}
    for subtask, _status, _stop_reason, sub_run_dir in results:
        expected = _expected_artifacts_for(subtask)
        qa_results[subtask.id] = validate_artifacts(sub_run_dir, expected)

    test_result: Optional[Dict[str, Any]] = None
    if _bool_env("SWARM_QA_RUN_TESTS", False) and _should_run_tests(objective, subtasks):
        cmd = os.getenv("SWARM_QA_COMMAND") or "python -m pytest -q"
        proc = subprocess.run(cmd, shell=True, cwd=str(repo_root), capture_output=True, text=True)
        stdout_tail = (proc.stdout or "").splitlines()[-10:]
        stderr_tail = (proc.stderr or "").splitlines()[-10:]
        message = " ".join(stdout_tail[-2:] + stderr_tail[-2:]).strip()
        test_result = {
            "ok": proc.returncode == 0,
            "command": cmd,
            "returncode": proc.returncode,
            "message": message or f"exit {proc.returncode}",
        }

    print("\n[SWARM] QA Summary:")
    for line in format_qa_summary(qa_results, test_result):
        print(line)

    print(f"[SWARM] Run folder: {run_root}")


__all__ = ["mode_swarm"]


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="python -m agent.modes.swarm")
    p.add_argument("--objective", required=True, help="Objective for the swarm run.")
    p.add_argument("--profile", choices=["fast", "deep", "audit"], default=None)
    p.add_argument("--isolation", choices=["none", "sandbox", "worktree"], default=None)
    p.add_argument("--cleanup-worktrees", action="store_true")
    p.add_argument("--unsafe-mode", action="store_true")
    args = p.parse_args(argv)

    mode_swarm(
        args.objective,
        unsafe_mode=bool(args.unsafe_mode),
        profile=args.profile,
        isolation=args.isolation,
        cleanup_worktrees=bool(args.cleanup_worktrees),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
    raise SystemExit(main())
