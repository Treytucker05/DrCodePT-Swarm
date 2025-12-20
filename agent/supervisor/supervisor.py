from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from agent.learning.self_healing_llm import apply_self_healing, log_healing_attempt
from agent.logging.run_logger import finalize_run, init_run, log_event
from agent.schemas.task_schema import OnFailAction, TaskDefinition, TaskType, load_task_from_yaml
from agent.supervisor.hardening import _last_events, abort, escalate, trigger_handoff, wait_for_continue
from agent.tools.base import ToolResult
from agent.tools.registry import get_tool
from agent.verifiers.registry import get_verifier


@dataclass
class _Counters:
    tool_calls: int = 0


def _env_flag(name: str) -> bool:
    import os

    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_unsafe_mode(cli_flag: bool) -> bool:
    return bool(cli_flag or _env_flag("AGENT_UNSAFE_MODE"))


def _trace_write(run_path: Path, record: Dict[str, Any]) -> None:
    (run_path / "trace.jsonl").open("a", encoding="utf-8", errors="replace", newline="\n").write(
        json.dumps(record, ensure_ascii=False) + "\n"
    )


def _tool_inputs(task: TaskDefinition, run_path: Path) -> Dict[str, Any]:
    inputs: Dict[str, Any] = dict(task.inputs or {})
    # Add common context for tools that write artifacts
    inputs.setdefault("run_path", str(run_path))

    if task.type == TaskType.shell:
        inputs.setdefault("command", task.command)
        if task.timeout_seconds:
            inputs.setdefault("timeout_seconds", task.timeout_seconds)

    if task.type == TaskType.python:
        inputs.setdefault("script", task.script)
        if task.timeout_seconds:
            inputs.setdefault("timeout_seconds", task.timeout_seconds)

    if task.type == TaskType.fs:
        inputs.setdefault("path", task.path)
        if task.content:
            inputs.setdefault("content", task.content)
        if task.mode:
            inputs.setdefault("mode", task.mode)

    if task.type == TaskType.api:
        if task.endpoint:
            inputs.setdefault("endpoint", task.endpoint)
        if task.method:
            inputs.setdefault("method", task.method)
        if task.headers:
            inputs.setdefault("headers", task.headers)
        if task.params:
            inputs.setdefault("params", task.params)
        if task.body is not None:
            inputs.setdefault("body", task.body)
        if task.timeout_seconds:
            inputs.setdefault("timeout_seconds", task.timeout_seconds)

    if task.type == TaskType.browser:
        if task.login_site:
            inputs.setdefault("login_site", task.login_site)
        if task.url:
            inputs.setdefault("url", task.url)
        if task.session_state_path:
            inputs.setdefault("session_state_path", task.session_state_path)
        if task.headless is not None:
            inputs.setdefault("headless", task.headless)

    if task.type == TaskType.notify:
        inputs.setdefault("title", task.name)
        inputs.setdefault("message", task.goal)

    return inputs


def _run_verifiers(task: TaskDefinition, result: ToolResult) -> List[Dict[str, Any]]:
    verify_results: List[Dict[str, Any]] = []
    specs = task.verify or []
    ctx = {
        "tool_success": bool(result.success),
        "last_result": result.output if result.output is not None else {},
        "evidence": result.evidence or {},
    }
    # Convenience passthrough for html/DOM verifiers
    if isinstance(result.metadata, dict) and result.metadata.get("dom_snapshot"):
        ctx["html"] = result.metadata.get("dom_snapshot")

    for spec in specs:
        v = get_verifier(spec.id, spec.args)
        r = v.verify(ctx)
        verify_results.append(
            {"id": r.id, "passed": bool(r.passed), "details": r.details, "metadata": r.metadata or {}}
        )
    return verify_results


def _all_passed(results: List[Dict[str, Any]]) -> bool:
    return all(bool(r.get("passed")) for r in results)


def _execute_single_task(
    task: TaskDefinition,
    *,
    run_path: Path,
    unsafe_mode: bool,
    counters: _Counters,
) -> Tuple[bool, ToolResult, List[Dict[str, Any]]]:
    tool_name = task.type.value
    spec = get_tool(tool_name)
    if spec is None:
        return False, ToolResult(False, error=f"Unknown tool: {tool_name}"), []

    if task.tools_allowed and tool_name not in task.tools_allowed:
        return False, ToolResult(False, error=f"Tool not allowed for task: {tool_name}"), []

    if spec.dangerous and not unsafe_mode:
        return (
            False,
            ToolResult(
                False,
                error=f"Blocked unsafe tool: {tool_name}. Re-run with --unsafe-mode or set AGENT_UNSAFE_MODE=true.",
                metadata={"unsafe_blocked": True},
            ),
            [],
        )

    inputs = _tool_inputs(task, run_path)
    counters.tool_calls += 1

    _trace_write(
        run_path,
        {
            "ts": time.time(),
            "observation": {"task_id": task.id, "type": task.type.value, "goal": task.goal},
            "action": {"tool": tool_name, "inputs": inputs},
        },
    )

    result = spec.adapter.execute(task, inputs)
    verify_results = _run_verifiers(task, result)

    _trace_write(
        run_path,
        {
            "ts": time.time(),
            "result": {
                "success": bool(result.success),
                "error": result.error,
                "output": result.output,
                "metadata": result.metadata,
                "evidence": result.evidence,
                "verifiers": verify_results,
            },
            "reflection": {
                "status": "success" if (result.success and _all_passed(verify_results)) else "replan",
                "explanation_short": "ok" if result.success else (result.error or "failed"),
            },
        },
    )

    ok = bool(result.success) and _all_passed(verify_results)
    return ok, result, verify_results


def _execute_task_tree(
    task: TaskDefinition,
    *,
    run_path: Path,
    unsafe_mode: bool,
    counters: _Counters,
) -> Tuple[bool, str, Optional[ToolResult]]:
    if task.type == TaskType.composite:
        for step in task.steps or []:
            ok, err, last = _execute_task_tree(step, run_path=run_path, unsafe_mode=unsafe_mode, counters=counters)
            if not ok:
                return False, err, last
        return True, "", None

    if task.requires_human:
        trigger_handoff(run_path, task, {"goal": task.goal})
        continued = wait_for_continue(timeout_minutes=task.stop_rules.max_minutes)
        if not continued:
            return False, "handoff_timeout", None
        return True, "", None

    ok, result, verify_results = _execute_single_task(task, run_path=run_path, unsafe_mode=unsafe_mode, counters=counters)
    if ok:
        log_event(run_path, "step_success", {"task_id": task.id, "type": task.type.value})
        return True, "", result
    reason = result.error or ("verification_failed" if not _all_passed(verify_results) else "failed")
    log_event(
        run_path,
        "step_failed",
        {
            "task_id": task.id,
            "type": task.type.value,
            "error": result.error,
            "verifiers": verify_results,
            "metadata": result.metadata,
        },
    )
    return False, reason, result


def run_task(
    task_or_path: str | Path | TaskDefinition,
    *,
    unsafe_mode: bool = False,
    enable_self_heal: bool = True,
) -> None:
    if isinstance(task_or_path, TaskDefinition):
        task = task_or_path
        task_yaml = yaml.safe_dump(task.model_dump(mode="json"), sort_keys=False)  # type: ignore[attr-defined]
    else:
        task_path = Path(task_or_path)
        task_yaml = task_path.read_text(encoding="utf-8", errors="replace")
        task = load_task_from_yaml(str(task_path))

    unsafe = _is_unsafe_mode(unsafe_mode)

    run_path = Path(init_run(task.id))
    (run_path / "original_task.yaml").write_text(task_yaml, encoding="utf-8", errors="replace")

    start = time.time()
    counters = _Counters()

    max_attempts = int(task.stop_rules.max_attempts)
    max_seconds = int(task.stop_rules.max_minutes) * 60
    max_tool_calls = int(task.stop_rules.max_tool_calls)

    last_plan_yaml = task_yaml
    action_sigs: List[str] = []

    for attempt in range(1, max_attempts + 1):
        if time.time() - start > max_seconds:
            escalate(run_path, "timeout", task_id=task.id)
        if counters.tool_calls >= max_tool_calls:
            escalate(run_path, "max_tool_calls_exceeded", task_id=task.id)

        log_event(run_path, "attempt_start", {"attempt": attempt, "task_id": task.id})

        ok, reason, last_result = _execute_task_tree(task, run_path=run_path, unsafe_mode=unsafe, counters=counters)
        if ok:
            finalize_run(run_path, "success", task.definition_of_done)
            return

        # Loop detection: repeated identical failure reasons with no task delta.
        sig = json.dumps({"reason": reason, "task_id": task.id}, sort_keys=True)
        action_sigs.append(sig)
        action_sigs = action_sigs[-8:]
        if action_sigs.count(sig) >= 3:
            escalate(run_path, "loop_detected", task_id=task.id)

        if not enable_self_heal:
            break

        if reason and "unsafe tool" in reason.lower():
            abort(run_path, reason)

        # Re-plan / self-heal
        try:
            healing = apply_self_healing(
                goal=task.goal,
                failed_task_yaml=last_plan_yaml,
                error=reason,
                recent_events=_last_events(run_path, limit=10),
            )
            log_healing_attempt(run_path, {"attempt": attempt, **healing})
        except Exception as exc:
            log_event(run_path, "self_heal_error", {"error": str(exc)})
            healing = {}

        stop = healing.get("stop_condition_if_applicable")
        if stop:
            if "abort" in str(stop).lower():
                abort(run_path, str(stop))
            escalate(run_path, str(stop), task_id=task.id)

        corrected = (healing.get("corrected_plan") or "").strip()
        if corrected:
            try:
                corrected_data = yaml.safe_load(corrected)
                if isinstance(corrected_data, dict):
                    task = TaskDefinition(**corrected_data)
                    last_plan_yaml = corrected
                    log_event(run_path, "self_heal_applied", {"attempt": attempt, "new_task_id": task.id})
                    continue
            except Exception as exc:
                log_event(run_path, "self_heal_invalid_yaml", {"error": str(exc)})

        # No fix produced.
        break

    # If we get here, attempts exhausted or self-heal couldn't recover.
    if task.on_fail == OnFailAction.abort:
        abort(run_path, "task_failed")
    escalate(run_path, "task_failed", task_id=task.id)


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m agent.supervisor.supervisor")
    p.add_argument("task_yaml", help="Path to YAML task definition")
    p.add_argument("--unsafe-mode", action="store_true", help="Allow unsafe tools/actions (shell/browser/desktop/etc).")
    p.add_argument("--no-self-heal", action="store_true", help="Disable self-healing replanning.")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        run_task(args.task_yaml, unsafe_mode=bool(args.unsafe_mode), enable_self_heal=not bool(args.no_self_heal))
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1


if __name__ == "__main__":
    raise SystemExit(main())
