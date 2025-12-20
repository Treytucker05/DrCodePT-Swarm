from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.autonomous.config import AgentConfig
from agent.autonomous.tools.builtins import build_default_tool_registry


def check(condition: bool, label: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"{status}: {label}")
    return condition


def main() -> int:
    root = ROOT
    ok = True

    # Tools
    cfg = AgentConfig(enable_web_gui=True, enable_desktop=True, unsafe_mode=False)
    reg = build_default_tool_registry(cfg, root / "runs" / "audit")
    tool_names = {t.name for t in reg.list_tools()}
    ok &= check("web_find_elements" in tool_names, "web_find_elements tool")
    ok &= check("web_click" in tool_names, "web_click tool")
    ok &= check("web_type" in tool_names, "web_type tool")
    ok &= check("web_close_modal" in tool_names, "web_close_modal tool")
    ok &= check("desktop_som_snapshot" in tool_names, "desktop_som_snapshot tool")
    ok &= check("desktop_click" in tool_names, "desktop_click tool")

    # Schemas
    plan_schema = root / "agent" / "llm" / "schemas" / "plan.schema.json"
    reflection_schema = root / "agent" / "llm" / "schemas" / "reflection.schema.json"
    dppm_schema = root / "agent" / "llm" / "schemas" / "task_decomposition.schema.json"
    ok &= check(plan_schema.is_file(), "plan schema present")
    ok &= check(reflection_schema.is_file(), "reflection schema present")
    ok &= check(dppm_schema.is_file(), "task decomposition schema present")
    if plan_schema.is_file():
        data = json.loads(plan_schema.read_text(encoding="utf-8"))
        step_props = data.get("$defs", {}).get("step", {}).get("properties", {})
        ok &= check("preconditions" in step_props, "plan schema has preconditions")
        ok &= check("postconditions" in step_props, "plan schema has postconditions")

    # Memory backend
    mem_store = root / "agent" / "autonomous" / "memory" / "sqlite_store.py"
    ok &= check(mem_store.is_file(), "memory store present")
    if mem_store.is_file():
        text = mem_store.read_text(encoding="utf-8", errors="replace")
        ok &= check("memory_embeddings" in text, "embedding-backed memory store")

    # Benchmarks
    tasks_dir = root / "tasks"
    task_files = list(tasks_dir.glob("*.json")) if tasks_dir.is_dir() else []
    ok &= check(len(task_files) >= 10, "tasks/ has >=10 tasks")
    ok &= check((root / "scripts" / "agent_benchmark.py").is_file(), "benchmark runner present")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
