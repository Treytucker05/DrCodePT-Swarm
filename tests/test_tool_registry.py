from __future__ import annotations

from agent.autonomous.config import AgentConfig
from agent.autonomous.tools.builtins import build_default_tool_registry


def test_tool_registry_includes_new_tools(tmp_path) -> None:
    cfg = AgentConfig(enable_web_gui=False, enable_desktop=False)
    run_dir = tmp_path / "run"
    registry = build_default_tool_registry(cfg, run_dir)

    assert registry.has_tool("web_search")
    assert registry.has_tool("delegate_task")

    schema = registry.tool_args_schema("web_search") or {}
    props = schema.get("properties") or {}
    assert "query" in props

    assert registry.requires_approval("shell_exec") is False
