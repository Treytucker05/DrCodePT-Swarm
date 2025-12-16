from __future__ import annotations

"""Main orchestration loop for DrCodePT Agent."""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv

from agent.schemas.task_schema import TaskDefinition, TaskType, load_task_from_yaml
from agent.tools.registry import get_tool
from agent.verifiers.registry import get_verifier
from agent.logging.run_logger import init_run, log_event, finalize_run
from agent.evidence.capture import bundle_evidence
from agent.supervisor.hardening import _last_events

# Lazy imports for components that may be filled later
try:  # pragma: no cover - populated in Component 7/8
    from agent.learning.learning_store import (
        generate_failure_signature,
        retrieve_similar_cases,
        record_success,
        record_failure,
    )
except Exception:  # pragma: no cover
    def generate_failure_signature(*args, **kwargs):
        return "signature_placeholder"

    def retrieve_similar_cases(*args, **kwargs):
        return []

    def record_success(*args, **kwargs):
        return None

    def record_failure(*args, **kwargs):
        return None

try:  # pragma: no cover
    from agent.supervisor.hardening import escalate, abort, trigger_handoff, wait_for_continue
except Exception:  # pragma: no cover
    def escalate(run_path, reason):
        finalize_run(run_path, "escalated", f"Escalated: {reason}")

    def abort(run_path, reason):
        finalize_run(run_path, "aborted", f"Aborted: {reason}")

    def trigger_handoff(run_path, task, evidence):
        log_event(run_path, "handoff_wait", {"reason": "requires_human", "task": task.id})

    def wait_for_continue():
        time.sleep(1)


load_dotenv()

HANDOFF_DIR = Path(__file__).resolve().parents[1] / "handoff"


def validate_task(task: TaskDefinition):
    # Pydantic validation already applied via load_task_from_yaml
    return task


def plan_steps(task: TaskDefinition, learnings: List[Any]) -> List[TaskDefinition]:
    if task.type == TaskType.composite:
        return task.steps or []
    return [task]


def run_verifiers(verify_specs, tool_result, evidence: Dict[str, Any]):
    results = []
    context = {"last_result": tool_result.output if hasattr(tool_result, "output") else tool_result, "evidence": evidence}
    # include html if available
    if isinstance(tool_result.output, dict):
        if "html" in tool_result.output:
            context["html"] = tool_result.output["html"]
    for spec in verify_specs or []:
        verifier = get_verifier(spec.id if hasattr(spec, "id") else spec.get("id"), spec.args if hasattr(spec, "args") else spec.get("args"))
        results.append(verifier.verify(context))
    return results


def all_passed(results) -> bool:
    return all(r.passed for r in results)


def retrieve_relevant_learnings(task):
    return retrieve_similar_cases("task_" + task.id, top_k=3)


def retrieve_fix_for_signature(signature):
    # Placeholder: would look up fix from learning store
    return None


def record_success_signature(signature, fix_applied):
    try:
        record_success(signature, fix_applied)
    except Exception:
        pass


def record_failure_signature(signature: str, reason: str, task_id: str, step_id: str, attempt: int, verify_results):
    metadata = {
        "task_id": task_id,
        "step_id": step_id,
        "attempt": attempt,
    }
    if verify_results:
        metadata["verifiers"] = [
            {
                "id": getattr(r, "id", None),
                "passed": getattr(r, "passed", None),
            }
            for r in verify_results
        ]
    try:
        record_failure(signature, reason, task_id=task_id, step_id=step_id, metadata=metadata)
    except Exception:
        pass


def run_task(yaml_path: str):
    task = load_task_from_yaml(yaml_path)
    validate_task(task)
    run_path = init_run(task.id)

    learnings = retrieve_relevant_learnings(task)
    steps = plan_steps(task, learnings)

    attempts = 0
    tool_calls = 0
    start_time = time.time()
    last_signatures: List[str] = []

    for step in steps:
        handoff_used = False
        while True:
            # Stop rules
            if attempts >= step.stop_rules.max_attempts:
                escalate(run_path, "max_attempts", task_id=task.id)
                return
            if time.time() - start_time >= step.stop_rules.max_minutes * 60:
                escalate(run_path, "max_time", task_id=task.id)
                return
            if tool_calls >= step.stop_rules.max_tool_calls:
                escalate(run_path, "max_tool_calls", task_id=task.id)
                return

            signature = generate_failure_signature(
                tool=step.type.value,
                site=step.url if hasattr(step, "url") else "",
                url=step.url if hasattr(step, "url") else "",
                exception_type="",
                verifier_failed="",
                dom_hints={},
            )
            if last_signatures.count(signature) >= 3:
                escalate(run_path, "blocked_state", task_id=task.id)
                return

            # Execute
            if step.type.value not in (step.tools_allowed or []):
                abort(run_path, f"Tool {step.type.value} not allowed")
                return
            tool = get_tool(step.type)
            combined_inputs = {}
            combined_inputs.update(task.inputs or {})
            if hasattr(step, "inputs") and step.inputs:
                combined_inputs.update(step.inputs)
            combined_inputs["run_path"] = run_path
            result = tool.execute(step, combined_inputs)
            tool_calls += 1
            log_event(run_path, "tool_execute", {"step": step.id, "result": getattr(result, 'output', None), "success": result.success})

            # Verify
            evidence = {}
            verify_results = run_verifiers(step.verify if step.type == TaskType.composite else task.verify, result, evidence)
            failure_reason = ""

            # Capture evidence when anything fails
            if (not result.success) or (not all_passed(verify_results)):
                evidence = bundle_evidence(run_path, {"output": getattr(result, "output", None)})
                failure_reason = result.error or "verification_failed"
            log_event(run_path, "verify_results", {"step": step.id, "results": [r.__dict__ for r in verify_results]})

            # Human input trigger
            if (not result.success) and result.error and "requires human input" in result.error.lower():
                waiting = HANDOFF_DIR / "WAITING.yaml"
                HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
                payload = {
                    "task_id": task.id,
                    "run_path": str(Path(run_path).resolve()),
                    "blocked_at": datetime.now().isoformat(),
                    "reason": result.error,
                    "evidence": result.evidence,
                    "last_10_events": _last_events(Path(run_path)),
                }
                waiting.write_text(yaml.safe_dump(payload), encoding="utf-8")
                wait_for_continue()
                continue

            if result.success and all_passed(verify_results):
                log_event(run_path, "step_success", {"step": step.id})
                record_success_signature(signature, None)
                break  # proceed to next step

            # Failed
            attempts += 1
            last_signatures.append(signature)
            log_event(run_path, "step_failed", {"step": step.id, "attempt": attempts})
            record_failure_signature(
                signature,
                failure_reason or "step_failed",
                task.id,
                step.id,
                attempts,
                verify_results,
            )

            fix = retrieve_fix_for_signature(signature)
            if fix:
                log_event(run_path, "apply_fix", {"signature": signature, "fix": fix})
                continue

            if getattr(task, "requires_human", False):
                if attempts > 0 and not handoff_used:
                    attempts -= 1  # allow one retry after human help
                    handoff_used = True
                handoff_payload = evidence if isinstance(evidence, dict) else {"evidence": str(evidence)}
                trigger_handoff(run_path, task, handoff_payload)
                wait_for_continue()
                continue

            if attempts < step.stop_rules.max_attempts:
                continue
            else:
                escalate(run_path, "verification_failed", task_id=task.id)
                return

    finalize_run(run_path, "success", task.definition_of_done)


if __name__ == "__main__":  # Manual run helper
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m agent.supervisor.supervisor <task_yaml>")
        sys.exit(1)
    run_task(sys.argv[1])
