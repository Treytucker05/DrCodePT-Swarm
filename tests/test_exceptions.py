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
    err = ToolExecutionError("file_read", "boom")
    assert err.tool_name == "file_read"
    assert err.data.get("tool_name") == "file_read"
    assert "boom" in str(err)


def test_interaction_required_error_questions() -> None:
    err = InteractionRequiredError(questions=["Q1", "", None, "Q2"])
    assert err.questions == ["Q1", "Q2"]
    assert err.data.get("questions") == ["Q1", "Q2"]
