"""
Codex CLI Client for ReAct Loop - Single-Step JSON Decisions
Based on DrCodePT-Swarm pattern and OpenAI best practices
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ActionDecision:
    """Single-step action decision from Codex"""
    thought: str
    action: str
    action_input: Dict[str, Any]
    reasoning: str
    confidence: float


class CodexReActClient:
    """
    Codex CLI client configured for single-step ReAct decisions.
    
    Uses the 'reason' profile with:
    - Tools disabled (read-only sandbox)
    - gpt-5 model (better schema compliance)
    - Low reasoning effort (fast turnaround)
    - Strict prompt wrapper to prevent tool execution
    """
    
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or str(Path.cwd())
        self.schema_path = None
        
    def decide_next_action(
        self,
        goal: str,
        context: Dict[str, Any],
        available_tools: list[str],
        previous_steps: list[Dict] = None
    ) -> ActionDecision:
        """
        Get next single-step action decision from Codex.
        
        Args:
            goal: The overall task goal
            context: Current state and observations
            available_tools: List of available tool names
            previous_steps: History of previous steps taken
            
        Returns:
            ActionDecision with the next step to take
        """
        
        # Build the prompt with CRITICAL constraint wrapper
        prompt = self._build_reasoning_prompt(
            goal=goal,
            context=context,
            available_tools=available_tools,
            previous_steps=previous_steps or []
        )
        
        # Get JSON schema for action decisions
        schema = self._get_action_schema()
        
        # Call Codex with reason profile
        result = self._call_codex_reasoning(prompt, schema)
        
        # Parse and return
        return ActionDecision(**result)
    
    def _build_reasoning_prompt(
        self,
        goal: str,
        context: Dict[str, Any],
        available_tools: list[str],
        previous_steps: list[Dict]
    ) -> str:
        """Build prompt with critical constraint wrapper"""
        
        # Format previous steps
        steps_summary = ""
        if previous_steps:
            steps_summary = "\n\nPREVIOUS STEPS:\n"
            for i, step in enumerate(previous_steps[-5:], 1):  # Last 5 steps
                steps_summary += f"{i}. {step.get('action', 'unknown')}: {step.get('observation', 'N/A')}\n"
        
        # Format available tools
        tools_list = "\n".join(f"  - {tool}" for tool in available_tools)
        
        prompt = f"""
CRITICAL INSTRUCTIONS FOR REASONING ENGINE:

You are a JSON reasoning engine. You MUST follow these rules EXACTLY:

1. DO NOT execute any commands or use any tools
2. DO NOT create multi-step plans
3. DO NOT attempt to solve the entire task
4. ONLY analyze the current situation and decide the SINGLE NEXT ACTION
5. Your ENTIRE response must be VALID JSON matching the schema provided

FAILURE TO FOLLOW THESE RULES WILL RESULT IN SYSTEM FAILURE.

---

TASK GOAL:
{goal}

CURRENT CONTEXT:
{json.dumps(context, indent=2)}

AVAILABLE TOOLS:
{tools_list}
{steps_summary}

YOUR JOB:
Analyze the current situation and decide what SINGLE action to take next.
Return ONLY a JSON object with:
- thought: Your reasoning about what to do next
- action: The tool name to use
- action_input: The parameters for that tool
- reasoning: Why this is the best next step
- confidence: Your confidence (0.0 to 1.0)

OUTPUT FORMAT:
Only valid JSON. No markdown, no explanation, no code blocks.
"""
        
        return prompt
    
    def _get_action_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action decisions"""
        return {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Your reasoning about the current situation"
                },
                "action": {
                    "type": "string",
                    "description": "Name of the tool to use next"
                },
                "action_input": {
                    "type": "object",
                    "description": "Parameters for the action",
                    "additionalProperties": {"type": "string"}  # Flexible: any key with string value
                },
                "reasoning": {
                    "type": "string",
                    "description": "Why this action is best"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Confidence in this decision"
                }
            },
            "required": ["thought", "action", "reasoning", "confidence"],
            "additionalProperties": False
        }
    
    def _call_codex_reasoning(
        self,
        prompt: str,
        schema: Dict[str, Any],
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Call Codex CLI with reason profile for single-step decision.
        
        Uses:
        - --profile reason (tools disabled)
        - --output-schema (enforce JSON)
        - --dangerously-bypass-approvals-and-sandbox (no pauses)
        - stdin for prompt
        """
        
        print("🔍 Calling Codex with reason profile...")
        print(f"⏱️  Timeout: {timeout}s")
        
        # Write schema to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(schema, f, indent=2)
            schema_file = f.name
        
        print(f"📄 Schema file: {schema_file}")
        
        try:
            # Build command
            # On Windows, use codex.cmd; on Unix, use codex
            codex_bin = 'codex.cmd' if Path.cwd().drive else 'codex'
            cmd = [
                codex_bin, 'exec',
                '--profile', 'reason',
                '--output-schema', schema_file,
                '--dangerously-bypass-approvals-and-sandbox',
                '--skip-git-repo-check',
                '-'  # Read from stdin
            ]
            
            print(f"🚀 Running command: {' '.join(cmd[:3])}...")
            
            # Run Codex (in working directory)
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',  # Force UTF-8 encoding
                errors='replace',   # Replace invalid characters
                timeout=timeout,
                cwd=self.working_dir  # Set working directory here
            )
            
            print(f"✅ Codex completed with return code: {result.returncode}")
            
            # Check if we have output
            if not result.stdout or not result.stdout.strip():
                raise RuntimeError(
                    f"Codex returned no output\n"
                    f"Stderr: {result.stderr[:500]}"
                )
            
            print(f"📊 Stderr length: {len(result.stderr)} chars")
            print(f"📊 Stdout length: {len(result.stdout)} chars")
            
            if result.returncode != 0:
                raise RuntimeError(
                    f"Codex reasoning failed:\n"
                    f"Return code: {result.returncode}\n"
                    f"Stderr: {result.stderr}\n"
                    f"Stdout: {result.stdout}"
                )
            
            # Parse JSON from stdout
            # Codex should output ONLY the JSON to stdout
            output = result.stdout.strip()
            
            # Handle potential markdown wrapping
            if output.startswith('```'):
                # Extract JSON from markdown code block
                lines = output.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('```'):
                        if in_json:
                            break
                        in_json = True
                        continue
                    if in_json:
                        json_lines.append(line)
                output = '\n'.join(json_lines).strip()
            
            # Parse
            decision = json.loads(output)
            
            return decision
            
        finally:
            # Clean up schema file
            Path(schema_file).unlink(missing_ok=True)



# Example usage
if __name__ == '__main__':
    client = CodexReActClient()
    
    decision = client.decide_next_action(
        goal="Set up Google Calendar OAuth for the application",
        context={
            "current_state": "Starting OAuth setup",
            "files_available": ["config.py", "main.py"],
            "observations": "No OAuth credentials found"
        },
        available_tools=[
            "web_search",
            "read_file",
            "write_file",
            "execute_command"
        ]
    )
    
    print(f"Next Action: {decision.action}")
    print(f"Thought: {decision.thought}")
    print(f"Input: {json.dumps(decision.action_input, indent=2)}")
    print(f"Confidence: {decision.confidence}")
