# Implementation Steps: Unified Agent

**This is your step-by-step guide. Follow these in order.**

Read UNIFIED_AGENT_PLAN.md first for context.

---

## Phase 1: Intelligent Orchestrator (This Week)

### Step 1: Create Intelligent Orchestrator (30 min)

**File:** `agent/core/intelligent_orchestrator.py`

```python
"""
Intelligent orchestrator that asks the LLM what capabilities it needs.
Replaces keyword-based routing with intelligent decision-making.
"""

from typing import Dict, Any
from agent.llm import CodexCliClient
from pathlib import Path
import json


class Strategy:
    """What the agent needs to complete a task."""
    def __init__(self, data: Dict[str, Any]):
        self.needs_tools = data.get("needs_tools", False)
        self.needs_web_search = data.get("needs_web_search", False)
        self.needs_deep_research = data.get("needs_deep_research", False)
        self.needs_deep_thinking = data.get("needs_deep_thinking", False)
        self.is_conversational = data.get("is_conversational", False)
        self.complexity = data.get("complexity", 5)
        self.approach = data.get("recommended_approach", "")
        self.raw = data


def decide_strategy(user_input: str, llm: CodexCliClient) -> Strategy:
    """
    Ask the LLM what capabilities it needs for this task.
    
    Returns a Strategy object describing what the agent needs.
    """
    
    prompt = f"""You are analyzing a user request to determine what capabilities you need.

User request: {user_input}

Analyze what you need to complete this request. Return ONLY valid JSON (no markdown, no explanation):

{{
  "needs_tools": boolean,           // Do you need to USE TOOLS (browser, files, code execution)?
  "needs_web_search": boolean,      // Do you need to search the web?
  "needs_deep_research": boolean,   // Do you need multi-source research with synthesis?
  "needs_deep_thinking": boolean,   // Do you need extended reasoning time?
  "is_conversational": boolean,     // Is this just a question/chat?
  "complexity": number,             // 1-10, how complex is this?
  "recommended_approach": "string"  // Brief strategy description
}}

Examples:

Request: "Set up Google Calendar OAuth"
Response: {{"needs_tools": true, "needs_web_search": true, "needs_deep_research": false, "needs_deep_thinking": false, "is_conversational": false, "complexity": 7, "recommended_approach": "Use browser automation to set up OAuth credentials"}}

Request: "Help me brainstorm gym business ideas"
Response: {{"needs_tools": false, "needs_web_search": false, "needs_deep_research": false, "needs_deep_thinking": true, "is_conversational": true, "complexity": 3, "recommended_approach": "Creative thinking and conversation"}}

Request: "Research gradient descent optimization techniques"
Response: {{"needs_tools": false, "needs_web_search": true, "needs_deep_research": true, "needs_deep_thinking": false, "is_conversational": false, "complexity": 8, "recommended_approach": "Multi-source research with synthesis"}}

Now analyze: {user_input}
"""

    # TODO: Use proper Codex schema here
    # For now, use simple exec call
    
    try:
        # This is placeholder - wire in actual Codex call
        result = llm.exec(prompt)
        data = json.loads(result)
        return Strategy(data)
    except Exception as e:
        # Fallback: assume needs tools
        return Strategy({
            "needs_tools": True,
            "complexity": 5,
            "recommended_approach": f"Error deciding strategy: {e}"
        })


def intelligent_orchestrator(user_input: str) -> Dict[str, Any]:
    """
    Replacement for smart_orchestrator.
    
    Instead of keyword matching, asks LLM what it needs.
    Returns routing decision for treys_agent.py
    """
    
    llm = CodexCliClient.from_env(workdir=Path.cwd())
    strategy = decide_strategy(user_input, llm)
    
    # Map strategy to mode
    if strategy.needs_tools:
        mode = "auto"
        reason = f"Needs tools: {strategy.approach}"
    elif strategy.needs_deep_research:
        mode = "research"
        reason = f"Needs research: {strategy.approach}"
    elif strategy.is_conversational:
        mode = "chat"
        reason = f"Conversational: {strategy.approach}"
    else:
        mode = "auto"  # Default to autonomous with tools available
        reason = "General task execution"
    
    return {
        "mode": mode,
        "reason": reason,
        "auto_execute": True,
        "strategy": strategy.raw,
        "clean_task": user_input
    }
```

**Create this file.**

---

### Step 2: Update treys_agent.py to Use It (10 min)

**File:** `agent/treys_agent.py`

Find the line that calls `smart_orchestrator()` (around line 2009):

```python
# OLD:
routing = smart_orchestrator(user_input)

# NEW:
from agent.core.intelligent_orchestrator import intelligent_orchestrator
routing = intelligent_orchestrator(user_input)
```

**Also add a debug print to see what it decides:**

```python
routing = intelligent_orchestrator(user_input)
print(f"[STRATEGY] {routing.get('strategy', {})}")  # Debug
print(f"Result: {routing}")
```

---

### Step 3: Test with Different Task Types (20 min)

**Create test script:** `test_orchestrator.py`

```python
from agent.core.intelligent_orchestrator import intelligent_orchestrator

test_cases = [
    "Set up Google Calendar OAuth",
    "Help me brainstorm gym business ideas",
    "Research gradient descent optimization",
    "Clean up my Downloads folder",
    "Explain how transformers work",
    "Find bugs in my codebase",
    "What should I focus on this week?",
]

for task in test_cases:
    print(f"\n{'='*60}")
    print(f"TASK: {task}")
    print(f"{'='*60}")
    
    result = intelligent_orchestrator(task)
    
    print(f"Mode: {result['mode']}")
    print(f"Reason: {result['reason']}")
    print(f"Strategy: {result.get('strategy', {})}")
```

**Run it:**
```bash
python test_orchestrator.py
```

**Expected results:**
- OAuth → mode: auto (needs tools)
- Brainstorm → mode: chat (conversational)
- Research → mode: research (needs research)
- Clean Downloads → mode: auto (needs tools)
- Explain → mode: chat (conversational)
- Find bugs → mode: auto (needs tools)
- Focus → mode: chat (conversational)

---

### Step 4: Fix Issues (variable time)

**Common issues:**

1. **LLM returns invalid JSON**
   - Add retry logic
   - Add JSON validation
   - Provide better examples

2. **Wrong mode decisions**
   - Improve prompt
   - Add more examples
   - Tweak strategy mapping

3. **Codex integration issues**
   - Use proper schema
   - Handle errors gracefully

---

## Phase 2: Unified Agent (Next Week)

### Step 5: Create Unified Agent Class (1 hour)

**File:** `agent/core/unified_agent.py`

```python
"""
Unified agent that handles any request by deciding what it needs.
"""

from typing import Any, Dict
from pathlib import Path
from agent.autonomous.runner import AgentRunner
from agent.autonomous.config import AgentConfig, RunnerConfig, PlannerConfig
from agent.llm import CodexCliClient
from agent.core.intelligent_orchestrator import decide_strategy


class UnifiedAgent:
    """
    One agent that handles everything:
    - Tool tasks (OAuth setup, file operations)
    - Research (web search, synthesis)
    - Conversations (chat, brainstorming)
    - Analysis (code review, debugging)
    """
    
    def __init__(self, unsafe_mode: bool = False):
        self.llm = CodexCliClient.from_env(workdir=Path.cwd())
        self.unsafe_mode = unsafe_mode
        
        # Reuse existing AgentRunner for tool tasks
        self.agent_runner = AgentRunner(
            cfg=RunnerConfig(max_steps=50, timeout_seconds=600),
            agent_cfg=AgentConfig(unsafe_mode=unsafe_mode),
            planner_cfg=PlannerConfig(mode="react"),
            llm=self.llm,
            mode_name="unified",
            agent_id="unified"
        )
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Main entry point. Decides strategy and executes.
        """
        
        # Ask: what do I need?
        strategy = decide_strategy(user_input, self.llm)
        
        print(f"[UNIFIED AGENT] Strategy: {strategy.approach}")
        print(f"[UNIFIED AGENT] Complexity: {strategy.complexity}/10")
        
        # Execute with appropriate method
        if strategy.needs_tools:
            return self._run_with_tools(user_input, strategy)
        elif strategy.needs_deep_research:
            return self._run_research(user_input, strategy)
        elif strategy.is_conversational:
            return self._run_chat(user_input, strategy)
        else:
            return self._run_reasoning(user_input, strategy)
    
    def _run_with_tools(self, task: str, strategy) -> Dict[str, Any]:
        """
        Use existing AgentRunner for tool-based tasks.
        This is the ReAct loop we already have.
        """
        print(f"[MODE] Autonomous with tools")
        
        result = self.agent_runner.run(task)
        
        return {
            "success": result.success,
            "stop_reason": result.stop_reason,
            "steps": result.steps_executed,
            "mode": "tools"
        }
    
    def _run_research(self, task: str, strategy) -> Dict[str, Any]:
        """
        Research mode: web search + synthesis.
        TODO: Implement or integrate existing research mode.
        """
        print(f"[MODE] Research")
        
        # For now, fall back to tools
        # Later: implement multi-source research
        return self._run_with_tools(f"Research: {task}", strategy)
    
    def _run_chat(self, task: str, strategy) -> Dict[str, Any]:
        """
        Conversational mode: just chat, no tools.
        """
        print(f"[MODE] Conversational")
        
        # Simple LLM call for conversation
        # TODO: Add memory context
        response = self.llm.exec(f"User: {task}\n\nRespond naturally:")
        
        print(f"\n{response}\n")
        
        return {
            "success": True,
            "response": response,
            "mode": "chat"
        }
    
    def _run_reasoning(self, task: str, strategy) -> Dict[str, Any]:
        """
        Pure reasoning: extended thinking, no tools.
        """
        print(f"[MODE] Deep reasoning")
        
        # Extended reasoning time
        # TODO: Use higher effort setting
        response = self.llm.exec(f"Think deeply about: {task}")
        
        print(f"\n{response}\n")
        
        return {
            "success": True,
            "response": response,
            "mode": "reasoning"
        }


def run_unified(task: str, unsafe_mode: bool = False):
    """
    Simple launcher for unified agent.
    """
    agent = UnifiedAgent(unsafe_mode=unsafe_mode)
    return agent.run(task)
```

**Create this file.**

---

### Step 6: Create Simple Launcher (5 min)

**File:** `run_unified.py` (in repo root)

```python
#!/usr/bin/env python3
"""
Simple launcher for unified agent.
Usage: python run_unified.py "your task here"
"""

import sys
from agent.core.unified_agent import run_unified

def main():
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    else:
        task = input("Task: ")
    
    print(f"\n{'='*60}")
    print(f"UNIFIED AGENT")
    print(f"{'='*60}\n")
    
    result = run_unified(task, unsafe_mode=True)
    
    print(f"\n{'='*60}")
    print(f"Result: {result}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
```

---

### Step 7: Test Unified Agent (30 min)

**Test cases:**

```bash
# Tool task
python run_unified.py "Set up Google Calendar OAuth"

# Chat
python run_unified.py "Help me brainstorm gym ideas"

# Research
python run_unified.py "Research gradient descent techniques"

# Analysis
python run_unified.py "Examine my codebase for bugs"
```

**Expected:** Each routes to appropriate execution method.

---

## Phase 3: Clean Up (After Testing)

### Step 8: Document What Works (30 min)

Update `STATUS.md` with:
- What works
- What doesn't
- What to delete
- What to keep

### Step 9: Delete Bloat (1 hour)

**Only after unified agent works well:**

```bash
# Delete old modes
rm agent/modes/swarm.py
rm agent/modes/collaborative.py
rm agent/modes/execute.py
rm -rf agent/playbooks/

# Delete old orchestrator
# (Remove smart_orchestrator function from treys_agent.py)
```

### Step 10: Simplify Launcher (30 min)

Replace complex `treys_agent.py` with simple launcher:

```python
# new_agent.py (simple version)

from agent.core.unified_agent import run_unified

def main():
    while True:
        task = input("\n> ")
        if not task or task.lower() in ["exit", "quit"]:
            break
        
        run_unified(task, unsafe_mode=True)

if __name__ == "__main__":
    main()
```

---

## Troubleshooting

### "Intelligent orchestrator not working"

**Check:**
1. Is Codex responding?
2. Is JSON valid?
3. Are examples clear?

**Fix:**
- Add more examples to prompt
- Add JSON validation
- Add fallback defaults

### "Agent still using old routing"

**Check:**
1. Did you import intelligent_orchestrator?
2. Is cache cleared? (restart Python)
3. Are you calling the right function?

**Fix:**
- Add debug prints
- Verify import path
- Restart agent

### "Tools not working in unified agent"

**Check:**
1. Is AgentRunner initialized correctly?
2. Are tools loaded?
3. Is MCP running?

**Fix:**
- Check AgentRunner config
- Verify tool registry
- Check MCP server status

---

## Success Metrics

**You'll know it's working when:**

1. ✅ Orchestrator correctly decides strategy for different tasks
2. ✅ Tool tasks execute with AgentRunner
3. ✅ Chat tasks respond conversationally
4. ✅ Research tasks search and synthesize
5. ✅ No more mode routing confusion
6. ✅ One clear execution path

**Then you can delete the bloat.**

---

## Next Steps After This Works

1. **Improve Memory Integration**
   - Save successful strategies
   - Learn from failures
   - Use past context

2. **Better Research Mode**
   - Multi-source gathering
   - Synthesis and comparison
   - Citation tracking

3. **Enhanced Tool Registry**
   - Better error handling
   - Tool selection intelligence
   - Dynamic tool loading

4. **Learning System**
   - Track what works
   - Adapt strategies
   - Improve over time

---

## Files Created in This Plan

- `agent/core/intelligent_orchestrator.py` ← Create first
- `agent/core/unified_agent.py` ← Create second
- `run_unified.py` ← Create third
- `test_orchestrator.py` ← Create for testing

**Start with intelligent_orchestrator.py**
