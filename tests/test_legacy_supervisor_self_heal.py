from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
import yaml

from agent.schemas.task_schema import OnFailAction, StopRules, TaskDefinition, TaskType
from agent.tools.base import ToolAdapter, ToolResult
from agent.tools.registry import ToolSpec


class _FailingApiTool(ToolAdapter):
    tool_name = "api"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:  # noqa: ARG002
        return ToolResult(False, error="api_fail", output={"status_code": 500})


class _FsOkTool(ToolAdapter):
    tool_name = "fs"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        p = Path(inputs["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(inputs.get("content", "")), encoding="utf-8")
        return ToolResult(True, output={"path": str(p)})


def test_supervisor_self_heal_replans_and_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from agent.logging import run_logger
    from agent.supervisor import supervisor as sup
    import agent.tools.registry as tool_reg

    # Keep test artifacts in tmp.
    monkeypatch.setattr(run_logger, "RUNS_DIR", tmp_path / "runs", raising=True)

    # Replace tool registry with test stubs.
    tool_reg._TOOLS.clear()
    tool_reg._TOOLS.update(
        {
            "api": ToolSpec(adapter=_FailingApiTool(), dangerous=False),
            "fs": ToolSpec(adapter=_FsOkTool(), dangerous=True),
        }
    )

    out_file = tmp_path / "out.txt"

    corrected_task = {
        "id": "fixed",
        "name": "fixed",
        "type": "fs",
        "goal": "write file",
        "inputs": {"path": str(out_file), "content": "ok", "mode": "overwrite"},
        "output": {},
        "definition_of_done": "file written",
        "verify": [{"id": "file_exists", "args": {"path": str(out_file)}}],
        "allowed_paths": [],
        "tools_allowed": ["fs"],
        "stop_rules": {"max_attempts": 1, "max_minutes": 1, "max_tool_calls": 2},
        "on_fail": "abort",
    }

    def _stub_self_heal(**kwargs) -> Dict[str, Any]:  # noqa: ARG001
        return {
            "corrected_plan": yaml.safe_dump(corrected_task, sort_keys=False),
            "root_cause": "stub",
            "suggested_tool_or_step_changes": ["swap to fs"],
            "stop_condition_if_applicable": None,
        }

    monkeypatch.setattr(sup, "apply_self_healing", _stub_self_heal, raising=True)

    failing_task = TaskDefinition(
        id="t1",
        name="t1",
        type=TaskType.api,
        goal="fail then heal",
        definition_of_done="done",
        stop_rules=StopRules(max_attempts=2, max_minutes=1, max_tool_calls=10),
        on_fail=OnFailAction.abort,
        endpoint="https://example.invalid",
        method="GET",
        tools_allowed=["api"],
        verify=[],
    )

    sup.run_task(failing_task, unsafe_mode=True, enable_self_heal=True)

    assert out_file.exists()

    run_dirs = sorted((tmp_path / "runs").glob("*_t1"))
    assert run_dirs, "expected a run directory to be created"
    result_path = run_dirs[-1] / "result.json"
    assert result_path.exists()
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "success"

