# Collaborative Planning Mode Implementation

## Objective
Add an interactive planning mode to DrCodePT-Swarm that asks clarifying questions before execution.

## Problem
Current flow: User request → Agent assumes details → Poor execution
Desired flow: User request → Q&A clarification → Detailed plan → User approval → Execution

## Implementation Tasks

### Task 1: Create Collaborative Planning Module

**File**: `agent/modes/collaborative.py`

**Requirements**:
1. Accept user goal + context
2. Generate 2-4 clarifying questions using LLM
3. Interactive Q&A loop (max 3 rounds)
4. Generate detailed plan with confidence scores (0-100)
5. Display plan and get user approval
6. Return plan + Q&A context for execution

**LLM Integration**:
- Use `CodexCliClient.from_env()` (same pattern as other modes)
- Create schema: `agent/llm/schemas/collaborative_plan.json`
- Import colorama for output formatting (copy from treys_agent.py)

**Schema Structure** (`collaborative_plan.json`):
```json
{
  "type": "object",
  "required": ["questions", "ready_to_plan"],
  "properties": {
    "questions": {
      "type": "array",
      "items": {"type": "string"},
      "maxItems": 4
    },
    "ready_to_plan": {"type": "boolean"},
    "plan_steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "step_number": {"type": "integer"},
          "description": {"type": "string"},
          "tool_name": {"type": "string"},
          "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
          "needs_clarification": {"type": "boolean"}
        }
      }
    }
  }
}
```

**Function Signatures**:
```python
def mode_collaborative(goal: str, context: str = "") -> Dict[str, any]:
    """Main entry point - returns plan dict"""
    
def _generate_questions(goal: str, context: str, history: List[Dict]) -> Dict:
    """Call LLM to generate clarifying questions"""
    
def _generate_plan(goal: str, context: str, qa_history: List[Dict]) -> Dict:
    """Call LLM to generate detailed execution plan"""
    
def _display_plan(plan: Dict) -> None:
    """Pretty-print plan with colors"""
```

### Task 2: CLI Integration

**File**: `agent/treys_agent.py`

**Changes**:
1. Add "Collab:" prefix detection (around line 600 in main loop)
2. Import collaborative mode: `from agent.modes.collaborative import mode_collaborative`
3. Route to collaborative mode when detected
4. After planning, hand off to execute mode with enriched context

**Pseudo-code**:
```python
if user_input.lower().startswith("collab:"):
    goal = user_input[7:].strip()
    result = mode_collaborative(goal, context)
    if result.get("approved"):
        # Hand off to execute with plan context
        mode_execute(goal, context=result)
```

### Task 3: Add Help Text

**File**: `agent/treys_agent.py` in `show_help()` function

Add entry:
```
Collaborative Planning:
  Collab: [goal]  - Interactive planning with Q&A before execution
  Example:
    - Collab: organize my downloads folder
```

## Key Patterns to Follow

**LLM Call Pattern** (copy from other modes):
```python
from agent.llm import CodexCliClient
llm = CodexCliClient.from_env()
response = llm.reason_json(prompt, schema_path=Path("agent/llm/schemas/collaborative_plan.json"))
```

**Color Output** (copy from treys_agent.py):
```python
print(f"{CYAN}[PLANNING]{RESET} Analyzing your request...")
print(f"{YELLOW}[QUESTION 1]{RESET} What categories should I use?")
```

## Testing Commands

After implementation:
```bash
python -m agent.treys_agent
> Collab: organize my downloads folder
```

Expected behavior:
1. Agent asks 2-4 questions
2. User answers
3. Agent shows detailed plan
4. User approves (y/n)
5. Execution begins (or returns to prompt if declined)

## Files to Create/Modify

CREATE:
- `agent/modes/collaborative.py`
- `agent/llm/schemas/collaborative_plan.json`

MODIFY:
- `agent/treys_agent.py` (imports, routing, help text)

## Success Criteria

- [ ] Can trigger with "Collab: <goal>"
- [ ] Asks 2-4 relevant clarifying questions
- [ ] Generates plan with confidence scores
- [ ] Displays plan in readable format
- [ ] Gets user approval before execution
- [ ] Integrates with existing execute mode
