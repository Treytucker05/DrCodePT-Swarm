"""
Direct plan execution using MCP tools (no playbooks, no shell commands).
This is the fast path for simple filesystem/browser operations.
"""

from __future__ import annotations
from typing import List, Dict, Any
from agent.mcp.client import MCPClient

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def execute_plan_direct(plan_steps: List[Dict[str, Any]]) -> bool:
    """
    Execute a collaborative plan directly using MCP tools.
    
    Args:
        plan_steps: List of steps from collaborative planning
        
    Returns:
        True if all steps succeeded, False otherwise
    """
    print(f"{YELLOW}[DIRECT EXECUTION]{RESET} Using MCP tools (fast path)...\n")
    
    for idx, step in enumerate(plan_steps, 1):
        step_num = step.get("step_number", idx)
        description = step.get("description", "Unknown step")
        tool_name = step.get("tool_name", "shell")
        confidence = step.get("confidence", 0)
        
        print(f"{YELLOW}[STEP {step_num}]{RESET} {description}")
        print(f"  Tool: {tool_name} | Confidence: {confidence}%")
        
        # Normalize tool names (handle "filesystem.list_directory" → "filesystem")
        tool_base = tool_name.split(".")[0].lower() if tool_name else "shell"
        
        # Route to appropriate handler
        if tool_base in {"filesystem", "fs", "file"}:
            success = _execute_filesystem_step(step)
        elif tool_base in {"browser", "playwright", "web"}:
            success = _execute_browser_step(step)
        elif tool_base in {"shell", "command"}:
            success = _execute_shell_step(step)
        else:
            print(f"{YELLOW}  → Unknown tool type, skipping{RESET}")
            continue
        
        if not success:
            print(f"{RED}[FAILED]{RESET} Execution stopped at step {step_num}\n")
            return False
        
        print(f"{GREEN}  ✓ Success{RESET}\n")
    
    print(f"{GREEN}[COMPLETE]{RESET} All steps executed successfully!")
    return True


def _execute_filesystem_step(step: Dict[str, Any]) -> bool:
    """Execute a filesystem operation via MCP."""
    try:
        # Get the filesystem MCP server spec
        from agent.mcp.registry import get_server
        spec = get_server("filesystem")
        if not spec:
            print(f"{RED}  ✗ Filesystem MCP server not configured{RESET}")
            return False
        
        # Create MCP client
        client = MCPClient(spec, timeout_seconds=30)
        
        # Extract action from description (simple heuristic)
        desc_lower = step.get("description", "").lower()
        
        # Determine which tool to call based on description
        if "list" in desc_lower or "inventory" in desc_lower:
            tool = "list_directory"
            path = _extract_path(step)
            print(f"  → DEBUG: Extracted path = '{path}'")
            if not path:
                print(f"{RED}  ✗ No path found in description: {step.get('description')}{RESET}")
                return False
            args = {"path": path}
        elif "move" in desc_lower:
            tool = "move_file"
            args = {
                "source": _extract_path(step, "from"),
                "destination": _extract_path(step, "to")
            }
        elif "create" in desc_lower and "folder" in desc_lower:
            tool = "create_directory"
            args = {"path": _extract_path(step)}
        elif "read" in desc_lower:
            tool = "read_file"
            args = {"path": _extract_path(step)}
        else:
            print(f"{YELLOW}  → Cannot determine filesystem action{RESET}")
            return False
        
        # Call the tool
        print(f"  → Calling {tool}...")
        response = client.call_tool(tool, args)
        
        if response.error:
            print(f"{RED}  ✗ Error: {response.error}{RESET}")
            return False
        
        # Print result summary
        if response.result:
            content = response.result.get("content", [])
            if content and isinstance(content, list):
                # Print first item as sample
                print(f"  → Result: {str(content[0])[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"{RED}  ✗ Exception: {e}{RESET}")
        return False


def _execute_browser_step(step: Dict[str, Any]) -> bool:
    """Execute browser operation via Playwright MCP or fall back to playbook."""
    print(f"{YELLOW}  → Browser automation not yet implemented in direct mode{RESET}")
    print(f"{YELLOW}  → Recommend using playbook for browser tasks{RESET}")
    return False


def _execute_shell_step(step: Dict[str, Any]) -> bool:
    """Execute shell command (fallback for operations not yet supported by MCP)."""
    print(f"{YELLOW}  → Shell commands not yet implemented in direct mode{RESET}")
    return False


def _extract_path(step: Dict[str, Any], key: str = "path") -> str:
    """Extract a file path from step description or arguments."""
    # Check if step has explicit arguments
    if "args" in step and key in step["args"]:
        path = step["args"][key]
    else:
        # Try to extract from description
        desc = step.get("description", "")
        
        # Simple heuristic: look for Windows paths
        import re
        path_pattern = r'[A-Za-z]:\\[^"\s]+'
        matches = re.findall(path_pattern, desc)
        path = matches[0] if matches else ""
    
    # Resolve shortcuts
    if path.lower().endswith('.lnk'):
        path = _resolve_shortcut(path)
    
    return path


def _resolve_shortcut(lnk_path: str) -> str:
    """Resolve a Windows .lnk shortcut to its target path."""
    try:
        import subprocess
        result = subprocess.run(
            ['powershell', '-Command', 
             f"(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk_path}').TargetPath"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            target = result.stdout.strip()
            if target:
                print(f"  → Resolved shortcut: {lnk_path} → {target}")
                return target
    except Exception as e:
        print(f"{YELLOW}  → Could not resolve shortcut: {e}{RESET}")
    
    # Return original if resolution fails
    return lnk_path
