from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from colorama import Fore, Style, init as color_init

    color_init()
    GREEN, RED, CYAN, YELLOW, RESET = (
        Fore.GREEN,
        Fore.RED,
        Fore.CYAN,
        Fore.YELLOW,
        Style.RESET_ALL,
    )
except Exception:
    GREEN = RED = CYAN = YELLOW = RESET = ""

import os
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1] / "llm" / "schemas" / "collaborative_plan.json"
)
_LLM_CLIENT: CodexCliClient | None = None
_ORIGINAL_REASONING_EFFORT: str | None = None


def _get_llm() -> CodexCliClient:
    global _LLM_CLIENT, _ORIGINAL_REASONING_EFFORT
    if _LLM_CLIENT is None:
        # Store original value
        _ORIGINAL_REASONING_EFFORT = os.environ.get("CODEX_REASONING_EFFORT", "medium")
        _LLM_CLIENT = CodexCliClient.from_env()
    return _LLM_CLIENT


def _set_reasoning_effort_temp(effort: str):
    """Temporarily set reasoning effort - will be read by next Codex call."""
    os.environ["CODEX_REASONING_EFFORT"] = effort


def _restore_reasoning_effort():
    """Restore original reasoning effort."""
    if _ORIGINAL_REASONING_EFFORT:
        os.environ["CODEX_REASONING_EFFORT"] = _ORIGINAL_REASONING_EFFORT


def _sanitize_questions(questions: List[str], asked: set[str]) -> List[str]:
    cleaned: List[str] = []
    for item in questions:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in asked:
            continue
        cleaned.append(text)
        asked.add(key)
        if len(cleaned) >= 4:
            break
    return cleaned


def _fallback_questions(asked: set[str]) -> List[str]:
    defaults = [
        "What does success look like for this task?",
        "Are there any constraints, preferences, or deadlines I should follow?",
        "What tools or data sources should I use or avoid?",
        "Is there a specific order or priority for the steps?",
    ]
    return _sanitize_questions(defaults, asked)[:2]


def _normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    raw_steps = plan.get("plan_steps") or []
    normalized: List[Dict[str, Any]] = []
    for idx, step in enumerate(raw_steps, 1):
        if not isinstance(step, dict):
            continue
        description = str(step.get("description") or "").strip()
        if not description:
            continue
        tool_name = str(step.get("tool_name") or "").strip()
        try:
            confidence = int(step.get("confidence", 0))
        except Exception:
            confidence = 0
        confidence = max(0, min(100, confidence))
        normalized.append(
            {
                "step_number": idx,
                "description": description,
                "tool_name": tool_name,
                "confidence": confidence,
                "needs_clarification": bool(step.get("needs_clarification")),
            }
        )
    plan["plan_steps"] = normalized
    plan["ready_to_plan"] = bool(plan.get("ready_to_plan", True))
    plan.setdefault("questions", [])
    return plan


def _generate_questions(goal: str, context: str, history: List[Dict]) -> Dict:
    _set_reasoning_effort_temp("low")  # Fast for asking questions
    prompt = (
        "You are in SIMPLE COLLABORATIVE PLANNING mode (NOT Team mode).\n"
        "DO NOT mention CONTINUITY.md, Ledger Snapshots, or AGENTS.md conventions.\n"
        "DO NOT use OBSERVE/RESEARCH/PLAN/EXECUTE/VERIFY/REFLECT phases.\n"
        "Ask ONLY 2-3 critical questions about the user's actual task.\n"
        "Use reasonable defaults for minor details.\n"
        "Return STRICT JSON that matches the schema. No prose.\n"
        "If you have enough info to plan, set ready_to_plan=true and return an empty questions array.\n"
        "Do not repeat questions already asked.\n"
        "IMPORTANT: Always include plan_steps as an empty array [] when asking questions.\n\n"
        f"Goal:\n{goal}\n\n"
        f"Context:\n{context or '(none)'}\n\n"
        f"Q&A history:\n{json.dumps(history, ensure_ascii=False)}\n"
    )
    llm = _get_llm()
    return llm.reason_json(prompt, schema_path=_SCHEMA_PATH)


def _generate_plan(goal: str, context: str, qa_history: List[Dict]) -> Dict:
    _set_reasoning_effort_temp("medium")  # Moderate reasoning for planning
    prompt = (
        "You are generating a simple execution plan for the user.\n"
        "This is SIMPLE TASK PLANNING (NOT Team mode).\n"
        "DO NOT create steps to read/update CONTINUITY.md.\n"
        "DO NOT use OBSERVE/RESEARCH/PLAN/EXECUTE/VERIFY/REFLECT phase labels.\n"
        "Keep plans direct and minimal - 3-4 steps maximum for simple tasks.\n\n"
        "AVAILABLE TOOLS:\n"
        "- filesystem: Use this for reading, writing, moving, listing files/directories\n"
        "- browser: Use this for web navigation and automation\n"
        "- shell: Use this ONLY when filesystem/browser cannot do the task\n\n"
        "For filesystem operations, ALWAYS use tool_name='filesystem' (not 'shell').\n\n"
        "Return STRICT JSON that matches the schema. No prose.\n"
        "Include plan_steps with clear step descriptions, tool_name when relevant, "
        "confidence (0-100), and whether clarification is still needed.\n"
        "Set ready_to_plan=true and questions=[].\n"
        "IMPORTANT: All properties (questions, ready_to_plan, plan_steps) must be present.\n\n"
        f"Goal:\n{goal}\n\n"
        f"Context:\n{context or '(none)'}\n\n"
        f"Q&A history:\n{json.dumps(qa_history, ensure_ascii=False)}\n"
    )
    llm = _get_llm()
    return llm.reason_json(prompt, schema_path=_SCHEMA_PATH)


def _display_plan(plan: Dict) -> None:
    steps = plan.get("plan_steps") or []
    print(f"\n{CYAN}[PLAN]{RESET} Proposed steps:")
    if not steps:
        print(f"{YELLOW}[INFO]{RESET} No steps were generated.")
        return
    for step in steps:
        number = step.get("step_number", "?")
        description = step.get("description", "")
        tool_name = step.get("tool_name") or "unspecified"
        confidence = step.get("confidence", 0)
        needs_clarification = step.get("needs_clarification", False)
        conf_color = GREEN if confidence >= 80 else YELLOW if confidence >= 50 else RED
        clarify_flag = "yes" if needs_clarification else "no"
        print(f"  {number}. {description}")
        print(
            f"     tool: {tool_name} | confidence: {conf_color}{confidence}{RESET}"
            f" | needs clarification: {clarify_flag}"
        )


def mode_collaborative(goal: str, context: str = "") -> Dict[str, Any]:
    """Main entry point - returns plan dict"""
    print(f"\n{CYAN}[PLANNING]{RESET} Analyzing your request...")
    try:
        _get_llm()
    except (CodexCliNotFoundError, CodexCliAuthError) as exc:
        print(f"{RED}[ERROR]{RESET} {exc}")
        return {"approved": False, "error": str(exc), "goal": goal, "context": context}

    qa_history: List[Dict[str, str]] = []
    asked: set[str] = set()
    max_rounds = 2  # Reduced from 3
    max_total_questions = 5  # Hard cap
    total_questions_asked = 0

    for round_idx in range(1, max_rounds + 1):
        if total_questions_asked >= max_total_questions:
            print(f"{YELLOW}[INFO]{RESET} Enough questions asked, moving to planning...")
            break

        try:
            result = _generate_questions(goal, context, qa_history)
        except Exception as exc:
            print(f"{RED}[ERROR]{RESET} Failed to generate questions: {exc}")
            return {"approved": False, "error": str(exc), "goal": goal, "context": context}

        questions = result.get("questions") or []
        ready_to_plan = bool(result.get("ready_to_plan"))
        questions = _sanitize_questions(list(questions), asked)
        
        # Limit questions to stay under max_total_questions
        remaining_quota = max_total_questions - total_questions_asked
        if len(questions) > remaining_quota:
            questions = questions[:remaining_quota]
        
        if not questions and not ready_to_plan:
            questions = _fallback_questions(asked)[:min(2, remaining_quota)]

        if not questions:
            break

        print(f"{CYAN}[ROUND {round_idx}]{RESET} Quick questions:")
        for idx, question in enumerate(questions, 1):
            try:
                answer = input(f"{YELLOW}[QUESTION {idx}]{RESET} {question} ").strip()
            except KeyboardInterrupt:
                print(f"\n{YELLOW}[CANCELLED]{RESET} Planning cancelled.")
                return {"approved": False, "cancelled": True, "goal": goal, "context": context}
            if answer.lower() in {"cancel", "quit", "exit"}:
                print(f"{YELLOW}[CANCELLED]{RESET} Planning cancelled.")
                return {"approved": False, "cancelled": True, "goal": goal, "context": context}
            qa_history.append({"question": question, "answer": answer})
            total_questions_asked += 1

        if ready_to_plan or total_questions_asked >= max_total_questions:
            break

    try:
        plan = _generate_plan(goal, context, qa_history)
    except Exception as exc:
        print(f"{RED}[ERROR]{RESET} Failed to generate plan: {exc}")
        return {"approved": False, "error": str(exc), "goal": goal, "context": context}
    finally:
        _restore_reasoning_effort()  # Restore original setting

    plan = _normalize_plan(plan or {})
    _display_plan(plan)

    try:
        approval = input(f"{YELLOW}Approve this plan? (y/n):{RESET} ").strip().lower()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[CANCELLED]{RESET} Planning cancelled.")
        return {"approved": False, "cancelled": True, "goal": goal, "context": context}

    approved = approval in {"y", "yes"}
    if approved:
        print(f"{GREEN}[APPROVED]{RESET} Proceeding to execution.")
    else:
        print(f"{YELLOW}[NOT APPROVED]{RESET} Returning to prompt.")

    result = {
        "approved": approved,
        "goal": goal,
        "context": context,
        "qa_history": qa_history,
        "plan": plan,
    }
    if plan.get("plan_steps"):
        result["plan_steps"] = plan["plan_steps"]
    return result
