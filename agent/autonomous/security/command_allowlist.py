"""Command allowlist for restricting tool execution."""

import logging
from typing import Set, Dict, List, Optional

logger = logging.getLogger(__name__)


class CommandAllowlist:
    """Restrict which commands/tools can be executed.
    
    Prevents execution of dangerous commands.
    """
    
    # Dangerous commands that should never be allowed
    DANGEROUS_COMMANDS = {
        "rm -rf",
        "format",
        "dd",
        "mkfs",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
    }
    
    # Safe commands that are always allowed
    SAFE_COMMANDS = {
        "ls",
        "cat",
        "grep",
        "find",
        "echo",
        "pwd",
        "cd",
        "mkdir",
        "cp",
        "mv",
        "head",
        "tail",
        "wc",
        "sort",
        "uniq",
    }
    
    def __init__(self, allowed_tools: Optional[Set[str]] = None):
        """Initialize command allowlist.
        
        Args:
            allowed_tools: Set of allowed tool names (None = use defaults)
        """
        if allowed_tools is None:
            self.allowed_tools = self.SAFE_COMMANDS.copy()
        else:
            self.allowed_tools = allowed_tools
        
        logger.info(f"CommandAllowlist initialized with {len(self.allowed_tools)} allowed tools")
    
    def is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed.
        
        Args:
            command: Command to check
        
        Returns:
            True if command is allowed
        """
        # Check dangerous commands first
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous in command.lower():
                logger.warning(f"Dangerous command blocked: {command}")
                return False
        
        # Check if command is in allowlist
        cmd_name = command.split()[0].lower()
        
        if cmd_name in self.allowed_tools:
            return True
        
        logger.warning(f"Command not in allowlist: {cmd_name}")
        return False
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if tool is allowed.
        
        Args:
            tool_name: Tool name to check
        
        Returns:
            True if tool is allowed
        """
        if tool_name in self.allowed_tools:
            return True
        
        logger.warning(f"Tool not in allowlist: {tool_name}")
        return False
    
    def add_allowed_tool(self, tool_name: str) -> None:
        """Add tool to allowlist.
        
        Args:
            tool_name: Tool name to allow
        """
        self.allowed_tools.add(tool_name)
        logger.info(f"Added tool to allowlist: {tool_name}")
    
    def remove_allowed_tool(self, tool_name: str) -> None:
        """Remove tool from allowlist.
        
        Args:
            tool_name: Tool name to remove
        """
        self.allowed_tools.discard(tool_name)
        logger.info(f"Removed tool from allowlist: {tool_name}")
    
    def get_allowed_tools(self) -> List[str]:
        """Get list of allowed tools.
        
        Returns:
            List of allowed tool names
        """
        return sorted(list(self.allowed_tools))
