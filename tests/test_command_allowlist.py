"""Tests for command allowlist."""

import pytest
from agent.autonomous.security.command_allowlist import CommandAllowlist


def test_command_allowlist_initialization():
    """Test CommandAllowlist initialization."""
    allowlist = CommandAllowlist()
    assert len(allowlist.allowed_tools) > 0


def test_is_command_allowed():
    """Test checking if command is allowed."""
    allowlist = CommandAllowlist()
    
    # Safe command
    assert allowlist.is_command_allowed("ls -la") is True
    
    # Dangerous command
    assert allowlist.is_command_allowed("rm -rf /") is False


def test_is_tool_allowed():
    """Test checking if tool is allowed."""
    allowlist = CommandAllowlist()
    
    # Safe tool
    assert allowlist.is_tool_allowed("ls") is True
    
    # Dangerous tool
    assert allowlist.is_tool_allowed("rm") is False


def test_add_allowed_tool():
    """Test adding tool to allowlist."""
    allowlist = CommandAllowlist()
    
    allowlist.add_allowed_tool("custom_tool")
    assert allowlist.is_tool_allowed("custom_tool") is True


def test_remove_allowed_tool():
    """Test removing tool from allowlist."""
    allowlist = CommandAllowlist()
    
    # Add then remove
    allowlist.add_allowed_tool("custom_tool")
    assert allowlist.is_tool_allowed("custom_tool") is True
    
    allowlist.remove_allowed_tool("custom_tool")
    assert allowlist.is_tool_allowed("custom_tool") is False


def test_dangerous_commands_blocked():
    """Test that dangerous commands are blocked."""
    allowlist = CommandAllowlist()
    
    dangerous = ["rm -rf", "format", "dd", "shutdown", "reboot"]
    
    for cmd in dangerous:
        assert allowlist.is_command_allowed(cmd) is False


def test_get_allowed_tools():
    """Test getting list of allowed tools."""
    allowlist = CommandAllowlist()
    
    tools = allowlist.get_allowed_tools()
    assert len(tools) > 0
    assert "ls" in tools
