from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List

from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
from agent.llm import CodexCliAuthError, CodexCliClient, CodexCliNotFoundError
from agent.llm import schemas as llm_schemas


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{text}{suffix}: ").strip()
    return val if val else (default or "")


def _print_section(title: str) -> None:
    bar = "-" * max(8, len(title))
    print(f"\n{bar}\n{title}\n{bar}")


def _open_memory_store() -> SqliteMemoryStore:
    root = Path(__file__).resolve().parents[1]
    return SqliteMemoryStore(root / "memory" / "autonomous_memory.sqlite3")


def _render_list(label: str, items: List[str]) -> None:
    print(f"\n{label}:")
    if not items:
        print("  (none)")
        return
    for i, item in enumerate(items, 1):
        print(f"  {i:>2}. {item}")


def _generate_plan(llm: CodexCliClient, task: str, notes: List[str], memories: List[dict]) -> dict:
    prompt = (
        "You are helping a user collaborate on organizing thoughts into an actionable plan.\n"
        "Return STRICT JSON that matches the schema. No prose.\n\n"
        f"Task:\n{task}\n\n"
        f"Notes:\n{json.dumps(notes, ensure_ascii=False)}\n\n"
        f"Memory (recent):\n{json.dumps(memories, ensure_ascii=False)}\n"
    )
    return llm.reason_json(prompt, schema_path=llm_schemas.COLLAB_PLAN)


def run_collab_session(task: str) -> None:
    _print_section("COLLAB: Plan + Execute (interactive)")
    print("Add notes, refine, then pick actions to execute. Type Enter on a blank line to continue.\n")

    try:
        llm = CodexCliClient.from_env()
    except CodexCliNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return
    except CodexCliAuthError as exc:
        print(f"[ERROR] {exc}")
        return

    store = _open_memory_store()
    raw_memories = store.search(task, limit=6)
    memories = [asdict(m) for m in raw_memories]

    notes: List[str] = []
    while True:
        note = _prompt("Add a thought (blank to continue)", "")
        if not note:
            break
        notes.append(note)

    plan = _generate_plan(llm, task, notes, memories)
    _print_section("Summary")
    print(plan.get("summary", ""))

    _render_list("Goals", plan.get("goals") or [])
    _render_list("Decisions", plan.get("decisions") or [])
    _render_list("Open questions", plan.get("questions") or [])
    _render_list("Next actions", plan.get("next_actions") or [])
    _render_list("Risks", plan.get("risks") or [])
    _render_list("Assumptions", plan.get("assumptions") or [])

    if plan.get("questions"):
        _print_section("Answer questions")
        answers: List[str] = []
        for q in plan.get("questions") or []:
            ans = _prompt(f"{q}", "")
            if ans:
                answers.append(f"{q} -> {ans}")
        if answers:
            notes.extend(answers)
            plan = _generate_plan(llm, task, notes, memories)
            _print_section("Updated plan")
            print(plan.get("summary", ""))
            _render_list("Next actions", plan.get("next_actions") or [])

    # Save to memory for future learning
    payload = {
        "task": task,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "notes": notes,
        "plan": plan,
    }
    rec_id = store.upsert(
        kind="procedure",
        key=f"collab:{task[:120]}",
        content=json.dumps(payload, ensure_ascii=False),
        metadata={"source": "collab_session"},
    )
    store.close()
    print(f"\n[COLLAB] Saved session to memory (id={rec_id}).")

    actions = plan.get("next_actions") or []
    if not actions:
        return

    choice = _prompt("Execute a next action now? Enter number or 'no'", "no").strip().lower()
    if choice in {"no", "n", ""}:
        return
    try:
        idx = int(choice)
    except Exception:
        print("[COLLAB] Invalid choice.")
        return
    if idx < 1 or idx > len(actions):
        print("[COLLAB] Choice out of range.")
        return

    # Delegate execution to Auto mode
    from agent.modes.autonomous import mode_autonomous

    action = actions[idx - 1]
    _print_section("Executing")
    mode_autonomous(action, unsafe_mode=False)
