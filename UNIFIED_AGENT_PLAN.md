# DrCodePT-Swarm: Unified Agent Architecture Plan

**Status:** Historical/Archive. Do not update as a source of truth. See `AGENT_BEHAVIOR.md` and `conductor/tracks.md`.



Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
## Vision: One Agent for Everything

**Goal:** A single intelligent agent that handles ANY request by deciding what capabilities it needs and executing accordingly.

**User asks anything:**
- Tasks ("set up OAuth", "clean email")
- Conversations ("help me brainstorm")
- Research ("deep dive into RL")
- Analysis ("examine my codebase")
- Creative work ("design a game mechanic")

**Agent decides strategy and executes.**

---

## Current State: What We Have

### ✅ Good Parts (KEEP)
```
agent/
├── autonomous/
│   ├── runner.py           # AgentRunner - core execution loop
│   ├── react_loop.py       # ReAct: think → plan → execute → observe → reflect
│   ├── config.py           # Configuration
│   └── tools/
│       └── registry.py     # Tool definitions (browser, files, python, web, etc.)
├── llm/
│   └── codex_client.py     # GPT-5 interface
└── memory/
    └── [memory system]     # Saves experiences and learnings
```

**These ~500 lines ARE the agent. Everything else is overhead.**

### ❌ Bloat (CAUSING PROBLEMS)
```
agent/
├── modes/
│   ├── swarm.py            # 1200+ lines - separate mode
│   ├── collaborative.py    # Separate mode
│   ├── execute.py          # Playbook system (DELETE GOAL)
│   └── autonomous_enhanced.py
├── playbooks/              # Rigid workflows (DELETE GOAL)
├── treys_agent.py          # 2096 lines of routing chaos
└── AGENTS.md               # Conflicting rules
```

**Problem:** Multiple separate "modes" instead of one intelligent agent.

---

## The Problem

### Current Flow (BROKEN)
```
User Input 
  → smart_orchestrator (keyword matching)
    → Routes to separate mode
      → Each mode has different rules
        → Modes fight each other
          → Agent gets confused
            → Nothing works
```

### What We Want
```
User Input
  → Unified Agent
    → Asks itself: "What do I need?"
      → Decides: tools, research, thinking, conversation
        → Executes with needed capabilities
          → Learns from result
            → Done
```

---

## The New Architecture

### Phase 1: Intelligent Orchestrator (This Week)

**Replace keyword matching with LLM decision:**

```python
# agent/core/intelligent_orchestrator.py

def decide_strategy(user_input: str) -> Strategy:
    """
    Ask the LLM what capabilities it needs for this task.
    Returns a strategy, not a "mode".
    """
    
    prompt = f"""
    User request: {user_input}
    
    Analyze what you need to complete this. Return JSON:
    {{
      "needs_tools": bool,           // Browser, files, code execution
      "needs_web_search": bool,      // Web search
      "needs_deep_research": bool,   // Multi-source research
      "needs_deep_thinking": bool,   // Extended reasoning time
      "is_conversational": bool,     // Just chat/help
      "complexity": 1-10,            // Task complexity
      "recommended_approach": "string" // Brief strategy
    }}
    """
    
    return ask_llm(prompt)
```

**Benefits:**
- No more keyword matching failures
- Agent decides intelligently
- Same code path for everything
- Still one unified agent

### Phase 2: Unified Execution (Next Week)

**One agent that switches behaviors based on needs:**

```python
# agent/core/unified_agent.py

class UnifiedAgent:
    def __init__(self):
        self.tools = load_all_tools()  # Browser, files, Python, web, etc.
        self.memory = Memory()
        self.llm = CodexCliClient()
    
    def run(self, user_input: str) -> Result:
        # Decide what we need
        strategy = decide_strategy(user_input)
        
        # Execute with appropriate capabilities
        if strategy.needs_tools:
            return self._run_with_tools(user_input, strategy)
        elif strategy.needs_deep_research:
            return self._run_research(user_input, strategy)
        elif strategy.is_conversational:
            return self._run_chat(user_input, strategy)
        else:
            return self._run_reasoning(user_input, strategy)
    
    def _run_with_tools(self, task, strategy):
        # Use existing AgentRunner (autonomous/runner.py)
        # This is the ReAct loop we already have
        return self.agent_runner.run(task)
    
    def _run_research(self, task, strategy):
        # Use web tools + synthesis
        # Can use existing research mode or build simple version
        pass
    
    def _run_chat(self, task, strategy):
        # Simple conversational response
        # Use memory for context
        pass
    
    def _run_reasoning(self, task, strategy):
        # Pure thinking, no tools
        # Extended reasoning time
        pass
```

### Phase 3: Delete the Bloat (After Testing)

**Once unified agent works, delete:**
- `modes/swarm.py`
- `modes/collaborative.py`
- `modes/execute.py` (playbook system)
- `playbooks/` directory
- `smart_orchestrator()` old version
- 90% of `treys_agent.py` routing logic

**Keep only:**
- `agent/core/unified_agent.py` (new)
- `agent/core/intelligent_orchestrator.py` (new)
- `agent/autonomous/` (existing ReAct loop)
- `agent/llm/` (LLM client)
- `agent/memory/` (memory system)
- Simple launcher script

---

## Implementation Plan

### Week 1: Get Unblocked

**Day 1-2 (Now):**
- [ ] Create `intelligent_orchestrator.py` with LLM-based routing
- [ ] Update `treys_agent.py` to use new orchestrator
- [ ] Test with multiple task types:
  - Tool task: "set up OAuth"
  - Research: "find papers on X"
  - Chat: "help me brainstorm"
  - Analysis: "examine my repo"

**Day 3-4:**
- [ ] Fix any routing issues
- [ ] Improve prompt for strategy detection
- [ ] Add logging to see decisions

**Day 5:**
- [ ] Document what works/doesn't work
- [ ] Plan Phase 2 based on learnings

### Week 2: Unify Execution

**Goal:** One `UnifiedAgent` class that handles everything

- [ ] Create `agent/core/unified_agent.py`
- [ ] Wire in existing AgentRunner for tool tasks
- [ ] Add simple research capability (web search + synthesis)
- [ ] Add conversational fallback
- [ ] Test extensively

### Week 3: Clean Up

**Goal:** Delete unnecessary code

- [ ] Remove old modes one by one
- [ ] Simplify `treys_agent.py` to simple launcher
- [ ] Update documentation
- [ ] Verify everything still works

---

## Success Criteria

**The agent should handle ALL of these naturally:**

1. **Tool Tasks**
   - "Set up Google Calendar OAuth"
   - "Clean up my Downloads folder"
   - "Create a Python script to analyze this CSV"

2. **Research Tasks**
   - "Research gradient descent optimization techniques"
   - "Find the best approaches to PT school studying"
   - "Compare React vs Vue for my use case"

3. **Conversational**
   - "Help me brainstorm gym business ideas"
   - "Explain how transformers work"
   - "What should I focus on this week?"

4. **Analysis**
   - "Examine my codebase and find bugs"
   - "Analyze my calendar and suggest optimizations"
   - "Review this code for security issues"

5. **Creative**
   - "Design a workout program"
   - "Write a blog post about AI agents"
   - "Generate ideas for my next project"

**Same agent. Different strategies. One codebase.**

---

## Key Principles

1. **Intelligence over Rules**
   - Let LLM decide strategy, not keyword matching
   - Agent figures out what it needs

2. **Simplicity over Features**
   - One execution path, not many modes
   - Delete code that doesn't help

3. **Learning over Rigidity**
   - Save what works/fails to memory
   - Improve over time, not fixed playbooks

4. **Flexibility over Structure**
   - Agent adapts to task
   - Not forced into predetermined workflows

---

## What NOT To Do

❌ **Don't add more modes**
❌ **Don't make routing more complex**
❌ **Don't force CONTINUITY.md for simple tasks**
❌ **Don't keep playbooks (we want to delete them)**
❌ **Don't make the agent follow rigid rules**

✅ **Do make the agent intelligent**
✅ **Do simplify the codebase**
✅ **Do let the agent decide its approach**
✅ **Do save learnings to memory**
✅ **Do delete code that gets in the way**

---

## Current Blockers (As of Dec 28, 2024)

### Why We Got Stuck Tonight

1. **Smart orchestrator routes wrong** (keyword matching fails)
   - "Auto:" → went to chat instead of autonomous
   - Fixed by adding prefix detection, but still fragile

2. **Autonomous mode reads CONTINUITY.md obsessively**
   - Made it optional in AGENTS.md
   - But agent still tries to read it
   - Need to remove the requirement entirely

3. **Playbook system not working**
   - MCP tools not wired up
   - Agent pretends to execute but does nothing
   - DELETE PLAYBOOKS instead of fixing

4. **Too many code paths**
   - Can't predict which mode will run
   - Each mode has different behavior
   - Need ONE path

### The Fix (This Week)

**Stop trying to fix the broken routing.**
**Build intelligent orchestrator instead.**
**Let agent decide what it needs.**

---

## Questions to Answer

Before building unified agent, decide:

1. **Memory System:**
   - How should agent save learnings?
   - What format? (Currently using some system)
   - How to retrieve relevant memories?

2. **Tool Registry:**
   - Keep all tools always available?
   - Or load based on strategy?
   - How to handle tool failures?

3. **Research Mode:**
   - Build simple web search + synthesis?
   - Or keep existing research mode and integrate?
   - How deep should research go?

4. **Conversational Mode:**
   - Pure chat response?
   - Or always have tools available?
   - When to search vs just answer?

5. **Error Recovery:**
   - What happens when agent fails?
   - Retry? Ask user? Save failure?
   - How to learn from mistakes?

---

## Next Session Checklist

When you come back to this:

1. **Read this file first** (you are here)
2. **Read IMPLEMENTATION_STEPS.md** (next file - step by step)
3. **Check STATUS.md** (track progress)
4. **Don't get lost in old code** - focus on the plan

**The goal is ONE agent, not fixing many modes.**

---

## Files in This Plan

- `UNIFIED_AGENT_PLAN.md` ← You are here (the vision)
- `IMPLEMENTATION_STEPS.md` ← Next (step-by-step guide)
- `STATUS.md` ← Track progress
- `DECISIONS.md` ← Record key decisions

**Start with IMPLEMENTATION_STEPS.md for concrete next actions.**
