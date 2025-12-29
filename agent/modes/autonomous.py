from __future__ import annotations

"""Autonomous mode - runs the true closed-loop agent runner."""

import os
import re
import sys
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


def mode_autonomous(task: str, *, unsafe_mode: bool = False) -> None:
    """
    Run the true agent loop (dynamic replanning) for the given task.

    Defaults:
    - safe-by-default (unsafe_mode=False)
    - enables web_gui_snapshot when available (Playwright)
    """

    _load_dotenv()

    from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
    from agent.config.profile import resolve_profile
    from agent.autonomous.runner import AgentRunner
    from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError

    planner_mode = (os.getenv("AUTO_PLANNER_MODE") or "react").strip().lower()
    auto_selected = False
    if planner_mode == "auto":
        planner_mode = _choose_planner_mode(task)
        auto_selected = True
    if planner_mode not in {"react", "plan_first"}:
        planner_mode = "react"

    # Default allowed roots: repo root only (run_dir/workspace are always allowed).
    desktop_default = [REPO_ROOT]

    fs_anywhere = _bool_env("AUTO_FS_ANYWHERE", False)
    raw_roots = os.getenv("AUTO_FS_ALLOWED_ROOTS", "").strip()
    allowed_roots = _split_paths(raw_roots) if raw_roots else desktop_default

    profile = resolve_profile(None, env_keys=("AUTO_PROFILE", "AGENT_PROFILE"))
    agent_cfg = AgentConfig(
        unsafe_mode=bool(unsafe_mode),
        enable_web_gui=_bool_env("AUTO_ENABLE_WEB_GUI", True),
        enable_desktop=_bool_env("AUTO_ENABLE_DESKTOP", True),
        pre_mortem_enabled=_bool_env("AUTO_PRE_MORTEM", False),
        allow_user_info_storage=_bool_env("AUTO_ALLOW_USER_INFO_STORAGE", False),
        allow_human_ask=_bool_env("AUTO_ALLOW_HUMAN_ASK", True),
        allow_fs_anywhere=fs_anywhere,
        fs_allowed_roots=tuple(allowed_roots),
        profile=profile,
    )
    runner_cfg = RunnerConfig(
        max_steps=_int_env("AUTO_MAX_STEPS", 30),
        timeout_seconds=_int_env("AUTO_TIMEOUT_SECONDS", 600),
        llm_heartbeat_seconds=_int_env("AUTO_LLM_HEARTBEAT_SECONDS", profile.heartbeat_s),
        llm_plan_timeout_seconds=_int_env("AUTO_LLM_PLAN_TIMEOUT_SECONDS", profile.plan_timeout_s),
        llm_plan_retry_timeout_seconds=_int_env("AUTO_LLM_PLAN_RETRY_TIMEOUT_SECONDS", profile.plan_retry_timeout_s),
    )
    planner_cfg = PlannerConfig(
        mode=planner_mode,  # type: ignore[arg-type]
        num_candidates=_int_env("AUTO_NUM_CANDIDATES", 1),
        max_plan_steps=_int_env("AUTO_MAX_PLAN_STEPS", 6),
    )

    llm = None
    codex_error = None
    try:
        llm = CodexCliClient.from_env(workdir=REPO_ROOT)
        if hasattr(llm, "check_auth") and not llm.check_auth():
            raise CodexCliAuthError("Codex CLI auth check failed")
        print(f"{YELLOW}[LLM]{RESET} provider=codex_cli model=default")
    except (CodexCliNotFoundError, CodexCliAuthError) as exc:
        codex_error = exc

    if llm is None and os.getenv("OPENROUTER_API_KEY"):
        try:
            from agent.llm.openrouter_client import OpenRouterClient
            llm = OpenRouterClient.from_env()
            print(f"{YELLOW}[LLM]{RESET} provider=openrouter model={llm.model}")
        except Exception as exc:
            print(f"{YELLOW}[WARN]{RESET} OpenRouter unavailable: {exc}")

    if llm is None and codex_error is not None:
        print(f"{RED}[ERROR]{RESET} {codex_error}")
        return

    print(f"\n{CYAN}[AUTO MODE]{RESET} {task}")
    planner_label = planner_mode + (" (auto)" if auto_selected else "")
    print(
        f"{YELLOW}[INFO]{RESET} Running closed-loop agent (planner={planner_label}, unsafe_mode={agent_cfg.unsafe_mode})."
    )

    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        mode_name="auto",
        agent_id="auto",
    )
    result = runner.run(task)

    if result.success:
        print(f"{GREEN}[DONE]{RESET} success=True stop_reason={result.stop_reason} steps={result.steps_executed}")
    else:
        print(f"{RED}[STOP]{RESET} success=False stop_reason={result.stop_reason} steps={result.steps_executed}")
    if result.trace_path:
        print(f"{CYAN}[TRACE]{RESET} {result.trace_path}")


__all__ = ["mode_autonomous"]
