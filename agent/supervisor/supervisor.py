from __future__ import annotations

"""Enhanced orchestration loop with Self-Healing, Active Learning, and Session Memory."""

import time
import json
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
from agent.supervisor.hardening import _last_events, self_heal_browser_failure

# Import the new 10/10 features
try:
    from agent.learning.self_healing_llm import apply_self_healing, log_healing_attempt, get_last_analysis
    SELF_HEALING_AVAILABLE = True
except ImportError:
    SELF_HEALING_AVAILABLE = False
    print("[WARNING] Self-healing module not available")

try:
    from agent.learning import ollama_client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[WARNING] Ollama client not available")

try:
    from agent.learning.active_learning import learn_from_success, suggest_playbook
    ACTIVE_LEARNING_AVAILABLE = True
except ImportError:
    ACTIVE_LEARNING_AVAILABLE = False
    print("[WARNING] Active learning module not available")

try:
    from agent.learning.session_memory import get_current_session
    SESSION_MEMORY_AVAILABLE = True
except ImportError:
    SESSION_MEMORY_AVAILABLE = False
    print("[WARNING] Session memory module not available")

# Lazy imports for components
try:
    from agent.learning.learning_store import (
        generate_failure_signature,
        retrieve_similar_cases,
        record_success,
        record_failure,
    )
except Exception:
    def generate_failure_signature(*args, **kwargs):
        return "signature_placeholder"
    
    def retrieve_similar_cases(*args, **kwargs):
        return []
    
    def record_success(*args, **kwargs):
        return None
    
    def record_failure(*args, **kwargs):
        return None

try:
    from agent.supervisor.hardening import escalate, abort, trigger_handoff, wait_for_continue
except Exception:
    def escalate(run_path, reason, task_id=None):
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
    return task


def plan_steps(task: TaskDefinition, learnings: List[Any]) -> List[TaskDefinition]:
    if task.type == TaskType.composite:
        return task.steps or []
    return [task]


def run_verifiers(verify_specs, tool_result, evidence: Dict[str, Any]):
    results = []
    context = {"last_result": tool_result.output if hasattr(tool_result, "output") else tool_result, "evidence": evidence}
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


def run_task(yaml_path: str, healing_depth: int = 0):
    """
    Enhanced run_task with Self-Healing, Active Learning, and Session Memory.
    """
    task = load_task_from_yaml(yaml_path)
    validate_task(task)
    run_path = init_run(task.id)
    
    # Save original task YAML for self-healing
    original_yaml_path = Path(run_path) / "original_task.yaml"
    original_yaml_path.write_text(Path(yaml_path).read_text())
    
    # Get session context
    session_context = {}
    if SESSION_MEMORY_AVAILABLE:
        session = get_current_session()
        session_context = session.get_context_for_task(task.goal)
        log_event(run_path, "session_context", session_context)
    
    # Check for existing playbook
    if ACTIVE_LEARNING_AVAILABLE:
        playbook = suggest_playbook(task.goal)
        if playbook:
            log_event(run_path, "playbook_suggested", {"playbook_id": playbook["id"], "name": playbook["name"]})
            print(f"[LEARNING] Found playbook: {playbook['name']} (used {playbook['success_count']} times)")
    
    learnings = retrieve_relevant_learnings(task)
    steps = plan_steps(task, learnings)
    
    attempts = 0
    tool_calls = 0
    start_time = time.time()
    last_signatures: List[str] = []
    execution_log = {"events": [], "tool_calls": 0, "start_time": start_time}
    healing_attempts = 0
    max_healing_attempts = 2

    def _record_failure_analysis(reason: str):
        if not OLLAMA_AVAILABLE:
            return
        try:
            analysis = ollama_client.analyze_failure(task.goal, reason, execution_log)
            Path(run_path, "failure_analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[WARNING] Ollama failure analysis skipped: {exc}")
    
    for step in steps:
        handoff_used = False
        while True:
            # Stop rules
            if attempts >= step.stop_rules.max_attempts:
                if SELF_HEALING_AVAILABLE and healing_attempts < max_healing_attempts and healing_depth < max_healing_attempts:
                    print(f"[SELF-HEALING] Attempting to heal task (attempt {healing_attempts + 1}/{max_healing_attempts})...")
                    corrected_yaml = apply_self_healing(
                        Path(run_path),
                        task,
                        "max_attempts_exceeded",
                        execution_log
                    )
                    meta = get_last_analysis()
                    confidence = float(meta.get("confidence", 0) or 0)
                    if corrected_yaml and confidence >= 0.7:
                        healing_attempts += 1
                        log_healing_attempt(Path(run_path), healing_attempts, True, {"corrected_yaml": corrected_yaml, "confidence": confidence})
                        log_event(run_path, "self_heal_plan_generated", {"confidence": confidence, "corrected_yaml": corrected_yaml})
                        finalize_run(run_path, "retrying_with_heal", "Retrying with corrected plan generated by Ollama")
                        return run_task(corrected_yaml, healing_depth + 1)
                    else:
                        reason = "low_confidence" if confidence < 0.7 else "no_fix_generated"
                        log_healing_attempt(Path(run_path), healing_attempts + 1, False, {"reason": reason, "confidence": confidence})
                
                _record_failure_analysis("max_attempts_exceeded")
                escalate(run_path, "max_attempts", task_id=task.id)
                return
            
            if time.time() - start_time >= step.stop_rules.max_minutes * 60:
                _record_failure_analysis("max_time_exceeded")
                escalate(run_path, "max_time", task_id=task.id)
                return
            
            if tool_calls >= step.stop_rules.max_tool_calls:
                _record_failure_analysis("max_tool_calls_exceeded")
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
            execution_log["tool_calls"] = tool_calls
            execution_log["events"].append({
                "type": "tool_execute",
                "step": step.id,
                "tool": step.type.value,
                "success": result.success,
                "timestamp": time.time()
            })
            
            log_event(run_path, "tool_execute", {"step": step.id, "result": getattr(result, 'output', None), "success": result.success})
            action_value = combined_inputs.get("action") or combined_inputs.get("op")
            
            if result.success:
                log_event(run_path, "tool_success", {"tool": step.type.value, "action": action_value, "output": result.output})
                execution_log["events"].append({
                    "type": "tool_success",
                    "tool": step.type.value,
                    "action": action_value
                })
            else:
                log_event(run_path, "tool_failure", {"tool": step.type.value, "action": action_value, "error": result.error, "metadata": result.metadata})
                if step.type == TaskType.browser and result.metadata.get("dom_snapshot"):
                    heal_metadata = dict(result.metadata)
                    if result.error:
                        heal_metadata["error"] = result.error
                    if getattr(result, "evidence", None):
                        heal_metadata["evidence"] = result.evidence
                    self_heal_browser_failure(run_path, step, heal_metadata)
            
            # Verify
            evidence = {}
            verify_results = run_verifiers(step.verify if step.type == TaskType.composite else task.verify, result, evidence)
            failure_reason = ""
            
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
                    attempts -= 1
                    handoff_used = True
                handoff_payload = evidence if isinstance(evidence, dict) else {"evidence": str(evidence)}
                trigger_handoff(run_path, task, handoff_payload)
                wait_for_continue()
                continue
            
            if attempts < step.stop_rules.max_attempts:
                continue
            else:
                _record_failure_analysis(f"verification_failed:{failure_reason or 'unknown'}")
                escalate(run_path, "verification_failed", task_id=task.id)
                return
    
    # Task succeeded!
    execution_log["total_time"] = time.time() - start_time
    finalize_run(run_path, "success", task.definition_of_done)
    
    if OLLAMA_AVAILABLE:
        try:
            patterns = ollama_client.extract_patterns(task.goal, execution_log)
            Path(run_path, "success_patterns.json").write_text(json.dumps(patterns, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[WARNING] Ollama pattern extraction skipped: {exc}")
    
    # Active Learning: Generate playbook from success
    if ACTIVE_LEARNING_AVAILABLE:
        try:
            playbook = learn_from_success(task, execution_log, Path(run_path))
            if playbook:
                log_event(run_path, "playbook_generated", {"playbook_id": playbook["id"]})
        except Exception as e:
            print(f"[WARNING] Failed to generate playbook: {e}")
    
    # Session Memory: Record task completion
    if SESSION_MEMORY_AVAILABLE:
        try:
            session = get_current_session()
            session.add_task(task, {
                "outcome": "success",
                "artifacts": [],  # Would extract from execution_log
                "duration": execution_log["total_time"]
            })
        except Exception as e:
            print(f"[WARNING] Failed to update session memory: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m agent.supervisor.supervisor_enhanced <task_yaml>")
        sys.exit(1)
    run_task(sys.argv[1])
