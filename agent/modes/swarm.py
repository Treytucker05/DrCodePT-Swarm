from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, replace
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import traceback

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.exceptions import AgentException
from agent.autonomous.models import SwarmResult
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
from agent.preflight.repo_fish import PreflightResult, run_preflight
from agent.preflight.clarify import ClarifyResult, run_clarifier
from agent.autonomous.repo_scan import RepoScanner, is_repo_review_task
from agent.config.profile import resolve_profile
from agent.autonomous.runner import AgentRunner
from agent.autonomous.task_orchestrator import TaskOrchestrator
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm import schemas as llm_schemas

logger = logging.getLogger(__name__)


_CODEX_CONFIG_CACHE: dict | None = None


def _load_codex_config() -> dict:
    global _CODEX_CONFIG_CACHE
    if _CODEX_CONFIG_CACHE is not None:
        return _CODEX_CONFIG_CACHE
    path = Path.home() / ".codex" / "config.toml"
    if not path.is_file():
        _CODEX_CONFIG_CACHE = {}
        return _CODEX_CONFIG_CACHE
    raw = ""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            import tomllib  # type: ignore

            _CODEX_CONFIG_CACHE = tomllib.loads(raw)
            return _CODEX_CONFIG_CACHE or {}
        except Exception:
            pass
    except Exception:
        _CODEX_CONFIG_CACHE = {}
        return _CODEX_CONFIG_CACHE

    cfg: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("["):
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in {"model", "model_reasoning_effort"}:
            cfg[key] = value
    _CODEX_CONFIG_CACHE = cfg
    return _CODEX_CONFIG_CACHE


def _normalize_effort(value: str) -> str:
    effort = (value or "").strip().lower()
    if effort in {"xhigh", "extra_high", "xh"}:
        return "high"
    if effort in {"xlow", "extra_low", "xl"}:
        return "low"
    if effort in {"high", "medium", "low"}:
        return effort
    return "medium"


def _debug_agent_banner(agent_label: str) -> None:
    cfg = _load_codex_config() or {}
    profiles = cfg.get("profiles") if isinstance(cfg.get("profiles"), dict) else {}
    profile_name = (os.getenv("CODEX_PROFILE_REASON") or "reason").strip()
    profile_cfg = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
    model = (os.getenv("CODEX_MODEL") or profile_cfg.get("model") or cfg.get("model") or "default").strip()
    effort_raw = os.getenv("CODEX_REASONING_EFFORT") or profile_cfg.get("model_reasoning_effort") or cfg.get("model_reasoning_effort") or "medium"
    effort = _normalize_effort(str(effort_raw))
    print(f"[MODEL: {model} | EFFORT: {effort} | AGENT: {agent_label}]")


def _simple_repo_roles(kind: str) -> list[str]:
    kind = (kind or "").strip().lower()
    if kind in {"gap_analysis", "gaps"}:
        return ["Gap Analysis", "Coverage & Testing Gaps", "Quick Wins"]
    if kind in {"architecture_review", "architecture"}:
        return ["Architecture Review", "Dependency Boundaries", "Risk Hotspots"]
    if kind in {"documentation", "docs"}:
        return ["Documentation Gaps", "Onboarding Clarity", "Quick Wins"]
    if kind in {"code_search"}:
        return ["Code Search", "Where It Lives", "Quick Pointers"]
    return ["Gap Analysis", "Architecture Review", "Quick Wins"]


def _role_focus_instructions(role: str) -> str:
    role_lower = (role or "").lower()
    if "gap analysis" in role_lower:
        return (
            "Scan for TODO/FIXME comments, incomplete implementations, "
            "missing error handling, and risky assumptions."
        )
    if "coverage" in role_lower or "testing" in role_lower:
        return (
            "Scan for missing test files, low coverage indicators, CI/CD configuration gaps, "
            "missing test assertions, and untested critical paths. Skip observation and go "
            "straight to analysis."
        )
    if "quick wins" in role_lower:
        return (
            "Find easy improvements: typos, unused imports, obvious refactors, "
            "outdated dependencies, or small cleanup tasks."
        )
    if "architecture" in role_lower:
        return "Review architecture boundaries, module coupling, and layering issues."
    if "dependency" in role_lower or "risk" in role_lower:
        return "Identify dependency or integration risks and high-risk areas."
    if "documentation" in role_lower:
        return "Identify missing or outdated documentation and onboarding gaps."
    if "code search" in role_lower or "where it lives" in role_lower:
        return "Locate likely file paths and entry points for the requested area."
    return "Provide focused findings relevant to your role."


def _find_key_docs(repo_root: Path) -> dict:
    targets = ["README.md", "README.txt", "ARCHITECTURE.md", "ENHANCEMENT_SUMMARY.md"]
    found: dict[str, Path] = {}
    for name in targets:
        direct = repo_root / name
        if direct.is_file():
            found[name] = direct
    if len(found) < len(targets):
        # Case-insensitive fallback search (shallow)
        try:
            for path in repo_root.rglob("*.md"):
                if path.name.upper() in {t.upper() for t in targets}:
                    found[path.name] = path
        except Exception:
            pass
    return found


def _read_text_snippet(path: Path, *, max_chars: int = 6000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        return ""


def _extract_bullets(section: str) -> list[str]:
    bullets: list[str] = []
    for line in section.splitlines():
        ln = line.strip()
        if ln.startswith("- "):
            bullets.append(ln[2:].strip())
    return bullets


def _extract_section(text: str, header: str) -> str:
    lines = text.splitlines()
    header_lower = header.lower()
    capture = False
    buf: list[str] = []
    for line in lines:
        raw = line.strip()
        if raw.lower().startswith(header_lower):
            capture = True
            continue
        if capture and raw.endswith(":") and raw[:-1].strip().isupper():
            break
        if capture:
            buf.append(line)
    return "\n".join(buf).strip()


def _is_incomplete_observation(output: str) -> bool:
    if not output:
        return False
    text = output.strip().lower()
    if text in {"phase: observe", "phase:observe", "observe"}:
        return True
    lines = [ln.strip().lower() for ln in output.splitlines() if ln.strip()]
    if len(lines) == 1 and lines[0].startswith("phase: observe"):
        return True
    joined = " ".join(lines)
    if "observe" in joined and "now" in joined and "scanning" in joined:
        return True
    return False


def _extract_repo_kind(objective: str) -> str:
    text = (objective or "").strip()
    match = re.match(r"^\[REPO MODE:\s*([^\]]+)\]", text, flags=re.IGNORECASE)
    if not match:
        return ""
    kind = match.group(1).strip().lower().replace(" ", "_")
    return kind


def _format_repo_map(repo_root: Path, repo_map: list) -> str:
    lines: list[str] = []
    for entry in repo_map:
        path = getattr(entry, "path", "") or ""
        desc = getattr(entry, "description", "") or ""
        try:
            rel = str(Path(path).resolve().relative_to(repo_root))
        except Exception:
            rel = path
        if desc:
            lines.append(f"- {rel}: {desc}")
        else:
            lines.append(f"- {rel}")
        if len(lines) >= 30:
            break
    return "\n".join(lines)


def mode_swarm_simple(
    objective: str,
    *,
    unsafe_mode: bool = False,
    profile: str | None = None,
    max_agents: int | None = None,
    timeout_seconds: int | None = None,
) -> None:
    """Simple swarm: spawn lightweight LLM agents (no planning/reflection loop)."""
    _load_dotenv()
    repo_root = Path(__file__).resolve().parents[2]
    run_root = repo_root / "runs" / "swarm_simple" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_root.mkdir(parents=True, exist_ok=True)

    profile_cfg = resolve_profile(profile, env_keys=("SWARM_SIMPLE_PROFILE", "SWARM_PROFILE", "AUTO_PROFILE", "AGENT_PROFILE"))
    max_agents = max_agents or _int_env("SWARM_SIMPLE_MAX_AGENTS", 3)
    timeout_seconds = _int_env("SWARM_SIMPLE_TIMEOUT_SECONDS", 300)
    agent_timeout = None

    scan_dir = run_root / "repo_scan"
    scanner = RepoScanner(
        repo_root=repo_root,
        run_dir=scan_dir,
        max_results=min(profile_cfg.max_glob_results, 200),
        profile=profile_cfg,
        usage=None,
    )
    index, repo_map = scanner.scan()

    root_entries = []
    try:
        root_entries = sorted([p.name for p in repo_root.iterdir()])[:40]
    except Exception:
        root_entries = []

    repo_context = _format_repo_map(repo_root, repo_map)
    kind = _extract_repo_kind(objective)
    roles = _simple_repo_roles(kind)[: max(1, max_agents)]
    role_timeouts: dict[str, int] = {
        "Gap Analysis": _int_env("SWARM_SIMPLE_TIMEOUT_GAP_SECONDS", 240),
        "Coverage & Testing Gaps": _int_env("SWARM_SIMPLE_TIMEOUT_COVERAGE_SECONDS", 240),
        "Quick Wins": _int_env("SWARM_SIMPLE_TIMEOUT_QUICK_SECONDS", 180),
    }
    prev_effort = os.environ.get("CODEX_REASONING_EFFORT")
    if kind == "gap_analysis":
        os.environ["CODEX_REASONING_EFFORT"] = "medium"

    print("\n[SWARM SIMPLE] Objective:", objective)
    if roles:
        print("[SWARM SIMPLE] Agents:", ", ".join(roles))

    def _run_role(role: str) -> tuple[str, str, float]:
        start = time.time()
        _debug_agent_banner(role)
        try:
            llm = CodexCliClient.from_env(workdir=repo_root, log_dir=run_root / role.replace(" ", "_"))
        except (CodexCliNotFoundError, CodexCliAuthError) as exc:
            return role, f"[ERROR] {exc}", time.time() - start

        role_focus = _role_focus_instructions(role)
        role_timeout = role_timeouts.get(role, timeout_seconds)

        docs = _find_key_docs(repo_root)
        docs_block = []
        for name, path in docs.items():
            content = _read_text_snippet(path)
            if content:
                docs_block.append(f"## {name}\n{content}")
        docs_text = "\n\n".join(docs_block).strip()

        # PHASE 1: UNDERSTAND
        understand_prompt = (
            f"You are the {role} agent.\n"
            "PHASE 1 - UNDERSTAND: Read docs and summarize what the system claims to do.\n"
            "Return two sections:\n"
            "SUMMARY:\n- ...\n"
            "CLAIMS:\n- feature claim\n"
            "Do NOT mention workspace rules.\n"
            f"Focus: {role_focus}\n\n"
            f"Docs:\n{docs_text}\n"
        )
        understand = llm.reason_json(
            understand_prompt, schema_path=llm_schemas.CHAT_RESPONSE, timeout_seconds=role_timeout
        )
        understand_text = (understand.get("response") or "").strip()
        claims_section = _extract_section(understand_text, "CLAIMS")
        claims = _extract_bullets(claims_section)

        # PHASE 2: VERIFY
        verify_prompt = (
            f"You are the {role} agent.\n"
            "PHASE 2 - VERIFY: Check whether the claimed features exist in the repo.\n"
            "Return two sections:\n"
            "VERIFICATION:\n- ...\n"
            "GAPS:\n- Gap Topic: details (file refs)\n"
            "Do NOT mention workspace rules.\n"
            f"Focus: {role_focus}\n\n"
            f"Claims:\n{chr(10).join('- ' + c for c in claims) or '- (none found)'}\n\n"
            f"Repo root entries: {', '.join(root_entries)}\n\n"
            "Repo map (selected files with short descriptions):\n"
            f"{repo_context}\n"
        )
        verify = llm.reason_json(
            verify_prompt, schema_path=llm_schemas.CHAT_RESPONSE, timeout_seconds=role_timeout
        )
        verify_text = (verify.get("response") or "").strip()
        gaps_section = _extract_section(verify_text, "GAPS")
        gap_items = _extract_bullets(gaps_section)
        gap_topics = []
        for item in gap_items:
            topic = item.split(":")[0].strip()
            if topic:
                gap_topics.append(topic)
        gap_topics = gap_topics[:3]

        # PHASE 3: RESEARCH (web_search)
        research_snippets: list[str] = []
        try:
            from agent.autonomous.config import RunContext
            from agent.autonomous.tools.builtins import WebSearchArgs, web_search

            ctx = RunContext(
                run_id=f"swarm_simple_{role.replace(' ', '_')}",
                run_dir=run_root,
                workspace_dir=run_root,
                profile=None,
                usage=None,
            )
            for topic in gap_topics:
                query = f"best practices for {topic}"
                search = web_search(ctx, WebSearchArgs(query=query, max_results=4))
                results = (search.output or {}).get("results") or []
                for result in results[:3]:
                    title = result.get("title") or "Untitled"
                    url = result.get("url") or ""
                    snippet = result.get("snippet") or ""
                    research_snippets.append(f"- {title} | {url} | {snippet}")
        except Exception as exc:
            research_snippets.append(f"- [ERROR] web_search failed: {exc}")

        # PHASE 4: RECOMMEND
        recommend_prompt = (
            f"You are the {role} agent.\n"
            "PHASE 4 - RECOMMEND: Synthesize gaps + research into recommendations.\n"
            "Return structured output with sections:\n"
            "PHASE 1 - UNDERSTAND:\n- summary\n"
            "PHASE 2 - VERIFY:\n- gaps with file refs\n"
            "PHASE 3 - RESEARCH:\n- best practices with citations (raw URLs)\n"
            "PHASE 4 - RECOMMEND:\n- actionable fixes with citations\n"
            "QUESTIONS:\n- clarifying questions (if any)\n"
            "Do NOT mention workspace rules.\n"
            f"Focus: {role_focus}\n\n"
            f"UNDERSTAND OUTPUT:\n{understand_text}\n\n"
            f"VERIFY OUTPUT:\n{verify_text}\n\n"
            f"RESEARCH SNIPPETS:\n{chr(10).join(research_snippets) if research_snippets else '- None'}\n"
        )
        recommend = llm.reason_json(
            recommend_prompt, schema_path=llm_schemas.CHAT_RESPONSE, timeout_seconds=role_timeout
        )
        response = (recommend.get("response") or "").strip()
        if _is_incomplete_observation(response):
            return role, "[INCOMPLETE] Observation-only response", time.time() - start
        return role, response or "[ERROR] Empty response", time.time() - start

    results_by_role: dict[str, tuple[str, float]] = {}
    with ThreadPoolExecutor(max_workers=len(roles)) as executor:
        future_map = {executor.submit(_run_role, role): role for role in roles}
        start_times = {future: time.time() for future in future_map}
        for future, role in list(future_map.items()):
            try:
                _, output, elapsed = future.result()
                results_by_role[role] = (output, elapsed)
            except Exception as exc:
                elapsed = time.time() - start_times.get(future, time.time())
                results_by_role[role] = (f"[FAILED - {type(exc).__name__}]", elapsed)

    print("\n[SWARM SIMPLE] Results:")
    for role in roles:
        output, elapsed = results_by_role.get(role, ("[FAILED - no result]", 0.0))
        header = f"[{role}] ({elapsed:.1f}s)"
        if output.startswith("[ERROR]") or output.startswith("[FAILED"):
            print(f"\n{header} {output}")
        elif output.startswith("[INCOMPLETE]"):
            print(f"\n{header} {output}")
        else:
            print(f"\n{header}\n{output}")
    if prev_effort is None:
        os.environ.pop("CODEX_REASONING_EFFORT", None)
    else:
        os.environ["CODEX_REASONING_EFFORT"] = prev_effort


def aggregate_swarm_results(
    futures: List,
    timeout: int = 30,
) -> SwarmResult:
    """Aggregate results from all workers, handling failures.

    This function collects results from all workers, handling timeouts
    and exceptions gracefully. It always returns a SwarmResult with
    whatever results were successfully collected.

    Args:
        futures: List of futures from worker tasks
        timeout: Timeout per worker in seconds

    Returns:
        SwarmResult with results and failures
    """
    results = []
    failures = []

    for future in as_completed(futures, timeout=timeout):
        try:
            result = future.result(timeout=timeout)
            results.append(result)
            logger.info("Worker completed: %s", getattr(result, "task_id", "unknown"))

        except TimeoutError as exc:
            logger.error("Worker timed out: %s", exc)
            failures.append({
                "type": "timeout",
                "error": str(exc),
                "task_id": getattr(future, "task_id", "unknown"),
            })

        except AgentException as exc:
            logger.error("Agent error in worker: %s", exc)
            failures.append({
                "type": "agent_error",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "task_id": getattr(future, "task_id", "unknown"),
            })

        except Exception as exc:
            logger.error("Worker failed: %s", exc, exc_info=True)
            failures.append({
                "type": "exception",
                "error": str(exc),
                "error_type": type(exc).__name__,
                "task_id": getattr(future, "task_id", "unknown"),
            })

    # Determine overall status
    if not failures:
        status = "success"
    elif results:
        status = "partial_failure"
    else:
        status = "failure"

    # Create summary
    summary = f"Completed {len(results)}/{len(futures)} tasks"
    if failures:
        summary += f" ({len(failures)} failures)"

    return SwarmResult(
        status=status,
        results=results,
        failures=failures,
        summary=summary,
    )


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


def _build_agent_cfg(
    repo_root: Path,
    *,
    unsafe_mode: bool,
    profile_name: str | None,
    allow_interactive_tools: bool = True,
) -> AgentConfig:
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
        allow_interactive_tools=bool(allow_interactive_tools),
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


def _decompose(
    llm: CodexCliClient,
    objective: str,
    *,
    max_items: int,
    clarify: ClarifyResult,
    preflight: PreflightResult,
) -> List[Subtask]:
    prompt = (
        "You are a swarm coordinator. Decompose the objective into 2-4 parallelizable subtasks.\n"
        "Only add dependencies when truly required. Use short IDs like A, B, C.\n"
        "Use the preflight repo_map and root listing; do NOT scan the entire repo.\n"
        "If the objective is a repo review, review only selected files from repo_map.\n"
        "If task_type is find_filepath, follow this structure:\n"
        "  A: Use repo_map + search_terms to list candidate paths.\n"
        "  B: Validate by opening only those candidate files/paths.\n"
        "  C: Return best match + rationale + next candidates.\n"
        f"Normalized objective: {objective}\n"
        f"Task type: {clarify.task_type}\n"
        f"Search terms: {clarify.search_terms}\n"
        f"Glob patterns: {clarify.glob_patterns}\n"
        f"Candidate roots: {clarify.candidate_roots}\n"
        f"Expected output: {clarify.expected_output}\n"
        f"Preflight repo_map: {preflight.repo_map_path}\n"
        f"Preflight root listing: {preflight.root_listing_path}\n"
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


def _ask_blocking_questions(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    prompts: List[str] = []
    for q in questions:
        question = str(q.get("question") or "").strip()
        if not question:
            continue
        prompts.append(question)
    return {
        "error": "interaction_required",
        "questions": prompts,
        "context": "swarm_initialization",
    }


def _format_answers(answers: Dict[str, str]) -> str:
    lines = []
    for key, val in answers.items():
        if not val:
            continue
        lines.append(f"{key}: {val}")
    return "\n".join(lines)


def _annotate_subtasks(
    subtasks: List[Subtask],
    *,
    clarify: ClarifyResult,
    preflight: PreflightResult,
) -> List[Subtask]:
    prefix_lines = [
        f"Preflight repo_map: {preflight.repo_map_path}",
        f"Preflight root listing: {preflight.root_listing_path}",
    ]
    if clarify.search_terms:
        prefix_lines.append(f"Search terms: {clarify.search_terms}")
    if clarify.glob_patterns:
        prefix_lines.append(f"Glob patterns: {clarify.glob_patterns}")
    if clarify.candidate_roots:
        prefix_lines.append(f"Candidate roots: {clarify.candidate_roots}")
    prefix = "\n".join(prefix_lines).strip()
    if not prefix:
        return subtasks
    updated = []
    for s in subtasks:
        updated.append(Subtask(id=s.id, goal=f"{prefix}\n\n{s.goal}".strip(), depends_on=s.depends_on, notes=s.notes))
    return updated


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
    _debug_agent_banner(f"Swarm {subtask.id}")
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

    preflight_dir = run_root / "preflight"
    preflight = run_preflight(
        repo_root=repo_root,
        objective=objective,
        run_dir=preflight_dir,
        max_results=min(profile_cfg.max_glob_results, 200),
        max_map_files=min(profile_cfg.max_files_to_read, 20),
        max_total_bytes=min(profile_cfg.max_total_bytes_to_read, 200_000),
    )
    clarify = run_clarifier(
        llm,
        objective=objective,
        root_listing=preflight.root_listing,
        repo_map=preflight.repo_map,
        run_dir=preflight_dir,
        workdir=repo_root,
        timeout_seconds=profile_cfg.plan_timeout_s,
    )
    if not clarify.ready_to_run and clarify.blocking_questions:
        print("\n[SWARM] Clarification needed before starting workers:")
        answers = _ask_blocking_questions(clarify.blocking_questions)
        if isinstance(answers, dict) and answers.get("error") == "interaction_required":
            _write_result(
                run_root,
                {
                    "ok": False,
                    "mode": "swarm",
                    "run_id": run_root.name,
                    "error": {
                        "type": "interaction_required",
                        "message": "interaction_required",
                        "data": answers,
                    },
                },
            )
            print("[SWARM] interaction_required:", answers.get("questions"))
            return
        if answers:
            augmented = objective + "\n\nUser answers:\n" + _format_answers(answers)
            clarify = run_clarifier(
                llm,
                objective=augmented,
                root_listing=preflight.root_listing,
                repo_map=preflight.repo_map,
                run_dir=preflight_dir,
                workdir=repo_root,
                timeout_seconds=profile_cfg.plan_timeout_s,
            )
    normalized_objective = clarify.normalized_objective or objective

    subtasks = _decompose(
        llm,
        normalized_objective,
        max_items=max_subtasks,
        clarify=clarify,
        preflight=preflight,
    )
    if not subtasks:
        print("[SWARM] Could not decompose; running as a single Auto task.")
        from agent.modes.autonomous import mode_autonomous

        mode_autonomous(normalized_objective, unsafe_mode=unsafe_mode)
        return
    subtasks = _annotate_subtasks(subtasks, clarify=clarify, preflight=preflight)
    _ensure_repo_scan_subtask(subtasks, objective=normalized_objective, max_items=max_subtasks)

    print(f"\n[SWARM] Objective: {objective}")
    print(f"[SWARM] Subtasks: {len(subtasks)} | Workers: {workers}")
    for s in subtasks:
        deps = f" (deps: {', '.join(s.depends_on)})" if s.depends_on else ""
        print(f"  - {s.id}: {s.goal}{deps}")

    agent_cfg = _build_agent_cfg(
        repo_root,
        unsafe_mode=unsafe_mode,
        profile_name=profile,
        allow_interactive_tools=False,
    )
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
    orchestrator = TaskOrchestrator()

    while remaining:
        ready = [s for s in remaining.values() if all(d in completed for d in s.depends_on)]
        if not ready:
            ready = list(remaining.values())

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map: Dict[Any, tuple[Subtask, Path]] = {}
            for s in ready:
                _reduce, dep_failures = orchestrator.should_reduce(s.depends_on, status_by_id)
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


__all__ = ["mode_swarm", "mode_swarm_simple"]


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
