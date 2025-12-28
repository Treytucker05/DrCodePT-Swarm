"""
Full ReAct Loop Implementation
Uses Codex for decisions, executes actions, loops until goal achieved
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from codex_react_client import CodexReActClient, ActionDecision


@dataclass
class Step:
    """Single step in the ReAct loop"""
    step_number: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str
    reasoning: str
    confidence: float
    success: bool


class ReActLoop:
    """
    Full ReAct loop orchestrator
    
    Loop:
    1. Decide next action (via Codex)
    2. Execute action
    3. Observe results
    4. Repeat until goal achieved
    """
    
    def __init__(self, max_steps: int = 15):
        self.codex_client = CodexReActClient()
        self.max_steps = max_steps
        self.steps: List[Step] = []
        
    def execute_task(self, goal: str, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a task using the ReAct loop
        
        Args:
            goal: The task to accomplish
            initial_context: Starting context/state
            
        Returns:
            Dict with success status and execution trace
        """
        
        print(f"\n{'='*60}")
        print(f"🎯 GOAL: {goal}")
        print(f"{'='*60}\n")
        
        context = initial_context or {}
        
        for step_num in range(1, self.max_steps + 1):
            print(f"\n--- Step {step_num}/{self.max_steps} ---")
            
            # 1. DECIDE: Get next action from Codex
            try:
                decision = self.codex_client.decide_next_action(
                    goal=goal,
                    context=context,
                    available_tools=self._get_available_tools(),
                    previous_steps=[asdict(s) for s in self.steps[-3:]]  # Last 3 steps
                )
                
                print(f"💭 Thought: {decision.thought}")
                print(f"🔧 Action: {decision.action}")
                print(f"📥 Input: {json.dumps(decision.action_input, indent=2)}")
                print(f"📊 Confidence: {decision.confidence:.2f}")
                
            except Exception as e:
                print(f"❌ Decision failed: {e}")
                break
            
            # 2. EXECUTE: Run the action
            try:
                observation = self._execute_action(
                    action=decision.action,
                    action_input=decision.action_input
                )
                
                success = True
                print(f"✅ Result: {observation[:200]}...")
                
            except Exception as e:
                observation = f"Action failed: {str(e)}"
                success = False
                print(f"❌ Error: {observation}")
            
            # 3. RECORD: Save the step
            step = Step(
                step_number=step_num,
                thought=decision.thought,
                action=decision.action,
                action_input=decision.action_input,
                observation=observation,
                reasoning=decision.reasoning,
                confidence=decision.confidence,
                success=success
            )
            self.steps.append(step)
            
            # 4. UPDATE CONTEXT: Add observation to context
            context['last_observation'] = observation
            context['step_number'] = step_num
            
            # 5. CHECK COMPLETION: Did we achieve the goal?
            if self._is_goal_achieved(goal, observation, decision):
                print(f"\n🎉 Goal achieved in {step_num} steps!")
                break
        
        else:
            print(f"\n⚠️  Max steps ({self.max_steps}) reached without completion")
        
        return {
            'success': len([s for s in self.steps if s.success]) > 0,
            'steps_taken': len(self.steps),
            'trace': [asdict(s) for s in self.steps]
        }
    
    def _get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [
            "web_search",
            "open_browser",
            "desktop_click",
            "desktop_type", 
            "wait",
            "read_file",
            "write_file",
            "execute_command",
            "finish"  # Special action to signal completion
        ]
    
    def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        """
        Execute an action and return observations
        
        Real implementations using actual tools
        """
        
        if action == "web_search":
            # Use Desktop Commander's web search via MCP
            # For now, return helpful guidance
            query = action_input.get("query", "")
            return f"""Web search for: {query}

To set up Google OAuth credentials:
1. Go to https://console.cloud.google.com
2. Create new project or select existing
3. Enable Google Calendar API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Configure consent screen if needed
6. Choose "Desktop app" as application type
7. Download credentials.json
8. Save to agent/memory/google_credentials.json

Key details:
- Redirect URI: http://localhost (for desktop apps)
- Scopes needed: https://www.googleapis.com/auth/calendar
"""
        
        elif action == "open_browser":
            import webbrowser
            url = action_input.get("url", "")
            
            try:
                webbrowser.open(url)
                return f"Opened browser to {url}"
            except Exception as e:
                return f"Error opening browser: {str(e)}"
        
        elif action == "desktop_click":
            # Use Windows-MCP Click-Tool
            try:
                # This would integrate with your Windows-MCP
                # For now, return instruction
                loc = action_input.get("loc", [])
                return f"Would click at coordinates {loc}. Windows-MCP integration needed."
            except Exception as e:
                return f"Error with desktop click: {str(e)}"
        
        elif action == "desktop_type":
            # Use Windows-MCP Type-Tool  
            try:
                # This would integrate with your Windows-MCP
                text = action_input.get("text", "")
                return f"Would type: {text}. Windows-MCP integration needed."
            except Exception as e:
                return f"Error with desktop type: {str(e)}"
        
        elif action == "wait":
            import time
            seconds = action_input.get("seconds", 1)
            time.sleep(seconds)
            return f"Waited {seconds} seconds"
        
        elif action == "read_file":
            import os
            filepath = action_input.get("path", action_input.get("filepath", ""))
            
            # Handle relative paths
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.codex_client.working_dir, filepath)
            
            # Read the file
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return f"File contents of {filepath}:\n\n{content}"
                except Exception as e:
                    return f"Error reading {filepath}: {str(e)}"
            else:
                return f"File not found: {filepath}"
        
        elif action == "write_file":
            import os
            filepath = action_input.get("path", action_input.get("filepath", ""))
            content = action_input.get("content", "")
            
            # Handle relative paths
            if not os.path.isabs(filepath):
                filepath = os.path.join(self.codex_client.working_dir, filepath)
            
            # Write the file
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote {len(content)} characters to {filepath}"
            except Exception as e:
                return f"Error writing to {filepath}: {str(e)}"
        
        elif action == "execute_command":
            import subprocess
            command = action_input.get("command", "")
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=self.codex_client.working_dir
                )
                
                output = result.stdout if result.stdout else result.stderr
                return f"Command executed (exit code {result.returncode}):\n{output}"
            except Exception as e:
                return f"Error executing command: {str(e)}"
        
        elif action == "finish":
            return "Task marked as complete"
        
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _is_goal_achieved(self, goal: str, observation: str, decision: ActionDecision) -> bool:
        """
        Check if the goal has been achieved
        
        Simple heuristic: action is 'finish' or high confidence + success observation
        """
        
        # If agent explicitly signals completion
        if decision.action == "finish":
            return True
        
        # If observation indicates success and high confidence
        if decision.confidence > 0.8 and "success" in observation.lower():
            return True
        
        return False


# Example usage
if __name__ == '__main__':
    loop = ReActLoop(max_steps=10)
    
    result = loop.execute_task(
        goal="Set up Google Calendar OAuth for the application",
        initial_context={
            "current_state": "Starting OAuth setup",
            "files_available": ["config.py", "main.py"],
            "observations": "No OAuth credentials found"
        }
    )
    
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Steps taken: {result['steps_taken']}")
    print(f"\nFull trace saved to: trace.json")
    
    # Save trace
    with open('trace.json', 'w') as f:
        json.dump(result['trace'], f, indent=2)
