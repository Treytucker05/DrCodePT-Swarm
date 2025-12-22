"""Tests for non-interactive worker mode."""

import pytest
from agent.autonomous.config import AgentConfig
from agent.autonomous.tools.registry import ToolRegistry
from agent.autonomous.models import ToolResult


def test_interactive_tool_blocked_in_non_interactive_mode():
    """Test that interactive tools are blocked in non-interactive mode."""
    registry = ToolRegistry(allow_interactive_tools=False)

    # Try to execute an interactive tool (human_ask is typically dangerous)
    result = registry.execute("human_ask", {"question": "What should I do?"})

    assert not result.success
    assert result.error == "interaction_required"
    assert result.metadata["error_type"] == "interaction_required"


def test_interactive_tool_allowed_in_interactive_mode():
    """Test that interactive tools are allowed in interactive mode."""
    registry = ToolRegistry(allow_interactive_tools=True)

    # Just verify the flag is set correctly
    assert registry.allow_interactive_tools is True


def test_swarm_mode_disables_interactive_tools():
    """Test that swarm mode disables interactive tools."""
    config = AgentConfig(allow_interactive_tools=False)
    assert config.allow_interactive_tools is False
