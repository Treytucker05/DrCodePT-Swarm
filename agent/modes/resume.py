from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.runner import AgentRunner
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError


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


def _default_allowed_roots(repo_root: Path) -> tuple[Path, ...]:
    userprofile = os.getenv("USERPROFILE") or ""
    roots: list[Path] = []
    if userprofile:
        roots.append(Path(userprofile) / "Desktop")
        roots.append(Path(userprofile) / "OneDrive" / "Desktop")
    roots.append(repo_root)
    return tuple(roots)


def _iter_checkpoints(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("checkpoint.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def _find_checkpoint(target: Optional[str]) -> Optional[Path]:
    repo_root = Path(__file__).resolve().parents[2]
    runs_root = repo_root / "runs"

    if target:
        candidate = Path(target.strip().strip("\"'"))
        if candidate.is_file():
            return candidate
        if candidate.is_dir():
            ck = candidate / "checkpoint.json"
            if ck.is_file():
                return ck
        for ck in _iter_checkpoints(runs_root):
            if ck.parent.name == target:
                return ck

    checkpoints = _iter_checkpoints(runs_root)
    return checkpoints[0] if checkpoints else None


def resume_run(target: Optional[str] = None) -> None:
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
    ckpt = _find_checkpoint(target)
    if ckpt is None or not ckpt.exists():
        print("[RESUME] No checkpoint found.")
        return

    fs_anywhere = _bool_env("AUTO_FS_ANYWHERE", False)
    raw_roots = os.getenv("AUTO_FS_ALLOWED_ROOTS", "").strip()
    allowed_roots = _split_paths(raw_roots) if raw_roots else list(_default_allowed_roots(repo_root))

    agent_cfg = AgentConfig(
        unsafe_mode=_bool_env("AGENT_UNSAFE_MODE", False),
        enable_web_gui=_bool_env("AUTO_ENABLE_WEB_GUI", True),
        enable_desktop=_bool_env("AUTO_ENABLE_DESKTOP", True),
        pre_mortem_enabled=_bool_env("AUTO_PRE_MORTEM", False),
        allow_user_info_storage=_bool_env("AUTO_ALLOW_USER_INFO_STORAGE", False),
        allow_human_ask=_bool_env("AUTO_ALLOW_HUMAN_ASK", True),
        allow_fs_anywhere=fs_anywhere,
        fs_allowed_roots=tuple(allowed_roots),
    )

    runner_cfg = RunnerConfig(
        max_steps=_int_env("AUTO_MAX_STEPS", 30),
        timeout_seconds=_int_env("AUTO_TIMEOUT_SECONDS", 600),
    )
    planner_cfg = PlannerConfig(
        mode=(os.getenv("AUTO_PLANNER_MODE") or "react").strip().lower(),  # type: ignore[arg-type]
        num_candidates=_int_env("AUTO_NUM_CANDIDATES", 1),
        max_plan_steps=_int_env("AUTO_MAX_PLAN_STEPS", 6),
    )

    runner = AgentRunner(cfg=runner_cfg, agent_cfg=agent_cfg, planner_cfg=planner_cfg, llm=llm)
    print(f"[RESUME] Using checkpoint: {ckpt}")
    result = runner.run("", resume_path=ckpt)
    if result.success:
        print(f"[RESUME] success=True stop_reason={result.stop_reason} steps={result.steps_executed}")
    else:
        print(f"[RESUME] success=False stop_reason={result.stop_reason} steps={result.steps_executed}")
    if result.trace_path:
        print(f"[TRACE] {result.trace_path}")


__all__ = ["resume_run"]
