from __future__ import annotations

from agent.autonomous.exceptions import (
    AgentException,
    ToolExecutionError,
    PlanningError,
    MemoryError,
    LLMError,
    ConfigurationError,
    DependencyError,
    ReflectionError,
    InteractionRequiredError,
)


def test_exception_hierarchy() -> None:
    for cls in (
        ToolExecutionError,
        PlanningError,
        MemoryError,
        LLMError,
        ConfigurationError,
        DependencyError,
        ReflectionError,
        InteractionRequiredError,
    ):
        assert issubclass(cls, AgentException)


def test_tool_execution_error_records_tool() -> None:
    err = ToolExecutionError("boom", context={"tool_name": "file_read"})
    assert err.message == "boom"
    assert err.context.get("tool_name") == "file_read"
    assert "tool_name=file_read" in str(err)


def test_interaction_required_error_questions() -> None:
    err = InteractionRequiredError("need input", questions=["Q1", "", None, "Q2"])
    assert err.questions == ["Q1", "", None, "Q2"]
