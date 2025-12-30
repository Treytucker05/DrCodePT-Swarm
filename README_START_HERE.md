# Quick Start: Unified Agent Project

**Start here when you come back to this project.**

Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
Docs index: `DOCS_INDEX.md`

---

## What Happened Tonight (Dec 28, 2024)

**Problem:** Agent got stuck in mode routing loops. Couldn't complete simple tasks.

**Root Cause:** Too many competing systems (orchestrator, playbooks, modes, CONTINUITY.md)

**Solution:** Building unified agent with intelligent routing.

---

## Read These Files IN ORDER

1. **UNIFIED_AGENT_PLAN.md** ← The vision (what we're building)
2. **IMPLEMENTATION_STEPS.md** ← Step-by-step guide (how to build it)
3. **STATUS.md** ← Current status (where we are)
4. **This file** ← Quick reference

---

## What To Do Next

### Next Session (Start Here)

**Phase 1, Step 1: Create Intelligent Orchestrator**

1. Create file: `agent/core/intelligent_orchestrator.py`
2. Copy code from IMPLEMENTATION_STEPS.md Step 1
3. Test with `test_orchestrator.py`
4. Fix any issues

**Time: 30-60 minutes**

---

## Key Files

### Documentation (Read These)
```
DrCodePT-Swarm/
├── README_START_HERE.md          ← This file
├── UNIFIED_AGENT_PLAN.md         ← The vision
├── IMPLEMENTATION_STEPS.md       ← How to build it
├── STATUS.md                     ← Current status
└── SESSION_2025-12-28_CHANGES.md ← What changed tonight
```

### Code to Create (Phase 1)
```
agent/
└── core/
    ├── intelligent_orchestrator.py  ← Create first
    └── unified_agent.py             ← Create later (Phase 2)
```

### Code to Keep (Don't Delete Yet)
```
agent/
├── autonomous/
│   ├── runner.py        ← Core execution engine (KEEP)
│   ├── react_loop.py    ← ReAct logic (KEEP)
│   └── tools/           ← Tool registry (KEEP)
├── llm/
│   └── codex_client.py  ← LLM interface (KEEP)
└── memory/              ← Memory system (KEEP)
```

### Code to Delete (Later, Phase 3)
```
agent/
├── modes/
│   ├── swarm.py           ← DELETE after testing
│   ├── collaborative.py   ← DELETE after testing
│   └── execute.py         ← DELETE after testing
├── playbooks/             ← DELETE after testing
└── treys_agent.py         ← SIMPLIFY after testing
```

---

## Current State

### ✅ What Works
- AgentRunner (autonomous mode core)
- ReAct loop (think-plan-execute)
- Tool registry (browser, files, python, etc.)
- Memory system
- LLM integration (Codex)

### ❌ What's Broken
- Smart orchestrator (keyword matching fails)
- Playbook system (MCP not wired)
- Mode routing (sends to wrong mode)
- CONTINUITY.md (optional now, but still confusing)

### 🔄 What We're Building
- Intelligent orchestrator (LLM decides strategy)
- Unified agent (one class for everything)
- Simple launcher (no complex routing)

---

## The Plan (3 Phases)

### Phase 1: Intelligent Orchestrator (This Week)
**Goal:** Replace keyword matching with LLM decision-making

**Tasks:**
1. Create intelligent_orchestrator.py
2. Update treys_agent.py to use it
3. Test with different tasks
4. Fix issues

**Time:** 2-3 hours

### Phase 2: Unified Agent (Next Week)
**Goal:** One agent class that handles everything

**Tasks:**
1. Create unified_agent.py
2. Create run_unified.py launcher
3. Test all task types
4. Refine execution

**Time:** 4-5 hours

### Phase 3: Clean Up (After Testing)
**Goal:** Delete bloat and simplify

**Tasks:**
1. Delete old modes
2. Delete playbooks
3. Simplify launcher
4. Verify everything works

**Time:** 2 hours

---

## Quick Reference

### Test Cases for Orchestrator

When testing intelligent_orchestrator, use these:

**Should route to "auto" (needs tools):**
- "Set up Google Calendar OAuth"
- "Clean up my Downloads folder"

**Should route to "research" (needs research):**
- "Research gradient descent techniques"
- "Find best PT study approaches"

**Should route to "chat" (conversational):**
- "Help me brainstorm gym ideas"
- "Explain transformers"

---

### Common Commands

**Start agent:**
```bash
launchers\TREYS_AGENT.bat
```

**Test orchestrator:**
```bash
python test_orchestrator.py
```

**Run unified agent (later):**
```bash
python run_unified.py "your task here"
```

---

## Don't Get Lost

### When You Get Confused

1. **Read UNIFIED_AGENT_PLAN.md** - Remember the vision
2. **Read IMPLEMENTATION_STEPS.md** - Follow the steps
3. **Check STATUS.md** - See where you are

### When Something Doesn't Work

1. **Don't try to fix old code** - It's broken by design
2. **Stick to the plan** - Build new, delete old later
3. **Test frequently** - Small steps, verify often

### When You're Tempted to Add Features

1. **Stop** - Finish the plan first
2. **Document the idea** - Add to STATUS.md "Future Ideas"
3. **Stay focused** - One thing at a time

---

## Remember

**The Goal:**
One intelligent agent that handles ANY request by deciding what it needs and executing accordingly.

**The Strategy:**
1. Build intelligent routing
2. Build unified execution
3. Delete the bloat

**The Rule:**
Don't fix the old broken system. Build the new simple one.

---

## Next Steps

**Right now:**
- Get some sleep
- Clear your head

**Next session:**
1. Read UNIFIED_AGENT_PLAN.md
2. Read IMPLEMENTATION_STEPS.md
3. Start Phase 1, Step 1
4. Create intelligent_orchestrator.py

**Don't overthink it. Just follow the steps.**

---

Good luck! 🚀
