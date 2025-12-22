import logging
from typing import Set, Optional, List

logger = logging.getLogger(__name__)

class CommandAllowlist:
    DANGEROUS_COMMANDS = {"rm -rf", "format", "dd", "mkfs", "shutdown", "reboot", "halt", "poweroff"}
    SAFE_COMMANDS = {"ls", "cat", "grep", "find", "echo", "pwd", "cd", "mkdir", "cp", "mv", "head", "tail", "wc", "sort", "uniq"}
    
    def __init__(self, allowed_tools: Optional[Set[str]] = None):
        if allowed_tools is None:
            self.allowed_tools = self.SAFE_COMMANDS.copy()
        else:
            self.allowed_tools = allowed_tools
    
    def is_command_allowed(self, command: str) -> bool:
        for dangerous in self.DANGEROUS_COMMANDS:
            if dangerous in command.lower():
                return False
        cmd_name = command.split()[0].lower()
        return cmd_name in self.allowed_tools
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        return tool_name in self.allowed_tools
    
    def add_allowed_tool(self, tool_name: str) -> None:
        self.allowed_tools.add(tool_name)
    
    def remove_allowed_tool(self, tool_name: str) -> None:
        self.allowed_tools.discard(tool_name)
    
    def get_allowed_tools(self) -> List[str]:
        return sorted(list(self.allowed_tools))
