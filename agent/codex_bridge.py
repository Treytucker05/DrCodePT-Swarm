from __future__ import annotations

"""Bridge Codex planner output into the DrCodePT-Swarm supervisor."""

import sys
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import ValidationError

# Ensure repository root is importable when launched from other folders
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from agent.schemas.task_schema import TaskDefinition  # noqa: E402
from agent.supervisor.supervisor import run_task  # noqa: E402


def read_stdin() -> str:
    """Read the full YAML plan from stdin."""
    plan_text = sys.stdin.read()
    if not plan_text.strip():
        raise ValueError("No YAML plan received on stdin from Codex.")
    return plan_text


def parse_plan(plan_text: str) -> TaskDefinition:
    """Parse and validate the YAML plan into a TaskDefinition."""
    try:
        data = yaml.safe_load(plan_text)
    except yaml.YAMLError as exc:  # pragma: no cover - simple CLI script
        raise ValueError(f"Failed to parse YAML from Codex: {exc}")

    if not isinstance(data, dict):
        raise ValueError("Codex plan must deserialize into a mapping/dictionary.")

    try:
        return TaskDefinition.parse_obj(data)
    except ValidationError as exc:  # pragma: no cover - simple CLI script
        raise ValueError(f"Plan failed validation: {exc}")


def persist_plan(plan_text: str) -> Path:
    """Persist the plan under agent/tasks for traceability."""
    tasks_dir = REPO_ROOT / "agent" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    plan_path = tasks_dir / f"codex_plan_{timestamp}.yaml"
    plan_path.write_text(plan_text, encoding="utf-8")
    return plan_path


def main():
    try:
        plan_text = read_stdin()
        task_def = parse_plan(plan_text)
        plan_path = persist_plan(plan_text)

        print(f"--- Supervisor: Starting Task: {task_def.goal} ---")
        run_task(str(plan_path))
        print("--- Task Complete ---")
    except Exception as exc:  # pragma: no cover - simple CLI script
        preview = plan_text[:500] if 'plan_text' in locals() else "<no content>"
        print("\n--- Execution Bridge Error ---", file=sys.stderr)
        print(f"An error occurred during task processing: {exc}", file=sys.stderr)
        print(f"Raw YAML received:\n{preview}...", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
