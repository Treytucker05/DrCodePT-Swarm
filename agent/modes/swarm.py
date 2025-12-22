from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
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
    userprofile = os.getenv("USERPROFILE") or ""
    roots: list[Path] = []
    if userprofile:
        roots.append(Path(userprofile) / "Desktop")
        roots.append(Path(userprofile) / "OneDrive" / "Desktop")
    roots.append(repo_root)
    return tuple(roots)


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


def _run_subagent(
    subtask: Subtask,
    *,
    repo_root: Path,
    run_dir: Path,
    agent_cfg: AgentConfig,
    runner_cfg: RunnerConfig,
    unsafe_mode: bool,
) -> tuple[Subtask, str, str, Path]:
    # Threaded swarm runs must never mutate process-global state (e.g., os.chdir).
    planner_mode = _planner_mode_for(subtask.goal)
    planner_cfg = PlannerConfig(
        mode=planner_mode,  # type: ignore[arg-type]
        num_candidates=_int_env("SWARM_NUM_CANDIDATES", _int_env("AUTO_NUM_CANDIDATES", 1)),
        max_plan_steps=_int_env("SWARM_MAX_PLAN_STEPS", _int_env("AUTO_MAX_PLAN_STEPS", 6)),
    )
    try:
        llm = CodexCliClient.from_env(workdir=repo_root, log_dir=run_dir)
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


def mode_swarm(objective: str, *, unsafe_mode: bool = False, profile: str | None = None) -> None:
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

    llm = llm.with_context(workdir=repo_root, log_dir=run_root)
    subtasks = _decompose(llm, objective, max_items=max_subtasks)
    if not subtasks:
        print("[SWARM] Could not decompose; running as a single Auto task.")
        from agent.modes.autonomous import mode_autonomous

        mode_autonomous(objective, unsafe_mode=unsafe_mode)
        return

    print(f"\n[SWARM] Objective: {objective}")
    print(f"[SWARM] Subtasks: {len(subtasks)} | Workers: {workers}")
    for s in subtasks:
        deps = f" (deps: {', '.join(s.depends_on)})" if s.depends_on else ""
        print(f"  - {s.id}: {s.goal}{deps}")

    agent_cfg = _build_agent_cfg(repo_root, unsafe_mode=unsafe_mode, profile_name=profile)
    runner_cfg = _build_runner_cfg(profile)
    if not agent_cfg.enable_web_gui and not agent_cfg.enable_desktop:
        print("[SWARM] MCP-based tools disabled (web_gui/desktop). Using local file/Python/web_fetch tools only.")

    remaining: Dict[str, Subtask] = {s.id: s for s in subtasks}
    completed: set[str] = set()
    results: List[tuple[Subtask, str, str, Path]] = []

    while remaining:
        ready = [s for s in remaining.values() if all(d in completed for d in s.depends_on)]
        if not ready:
            ready = list(remaining.values())

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {}
            for s in ready:
                sub_dir = run_root / f"{s.id}_{uuid4().hex[:6]}"
                future = executor.submit(
                    _run_subagent,
                    s,
                    repo_root=repo_root,
                    run_dir=sub_dir,
                    agent_cfg=agent_cfg,
                    runner_cfg=runner_cfg,
                    unsafe_mode=unsafe_mode,
                )
                future_map[future] = s

            for future in as_completed(future_map):
                subtask, status, stop_reason, sub_run_dir = future.result()
                results.append((subtask, status, stop_reason, sub_run_dir))
                completed.add(subtask.id)
                if subtask.id in remaining:
                    del remaining[subtask.id]

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

    print(f"[SWARM] Run folder: {run_root}")


__all__ = ["mode_swarm"]
