# Agent Principles

**READ THIS BEFORE MAKING CHANGES**

This document defines what the agent IS and what it IS NOT.
Every change should be checked against these principles.

---

## Core Philosophy

### The agent LEARNS, it doesn't follow scripts

The agent should be like a human assistant who gets smarter over time,
NOT like a macro that replays recorded actions.

**RIGHT:**
- Agent sees a login page, recognizes it, figures out where to type
- Agent remembers "last time I logged into OpenAI, the email field was first"
- Agent adapts when a website changes its layout

**WRONG:**
- Hardcoded steps: "click at x=100, y=200, then type, then click submit"
- Rigid scripts that break when anything changes
- Pre-programmed sequences for specific tasks

---

## The Three Layers

### 1. Memory (Knowledge)
**What the agent has learned from experience**

- Observations: "OpenAI login has email field, then password"
- Outcomes: "This approach worked 3/3 times"
- Failures: "Clicking too fast caused an error"

Memory INFORMS decisions, it doesn't REPLACE thinking.

### 2. Reasoning (The LLM)
**The agent's brain - decides what to do**

- Looks at current screen state
- Consults memory for relevant experience
- Decides the next action
- Adapts to unexpected situations

The LLM should ALWAYS be in the loop for decisions.

### 3. Execution (Hybrid Executor)
**How the agent interacts with the computer**

- UI Automation: Click elements by NAME (preferred)
- Vision: Look at screenshots when UI tree fails
- Both are just TOOLS for the reasoning layer

---

## What NOT To Do

### Don't Create Rigid Scripts
```python
# BAD - This is a script, not learning
def login_to_openai():
    click("email_field")
    type(email)
    click("continue")
    type(password)
    click("login")
```

### Don't Bypass the LLM
```python
# BAD - No reasoning, just pattern matching
if "login" in task:
    run_login_script()
```

### Don't Over-Engineer
```python
# BAD - Too many specialized handlers
class OpenAILoginHandler:
class GoogleLoginHandler:
class OutlookLoginHandler:
```

---

## What TO Do

### Let the Agent Figure It Out
```python
# GOOD - Agent reasons about the situation
result = executor.run_task(
    objective="Log into OpenAI",
    context="Email: user@example.com, Password: ..."
)
# Agent looks at screen, finds fields, completes login
```

### Store Observations, Not Scripts
```python
# GOOD - Memory stores what was observed
memory.store({
    "situation": "OpenAI login page",
    "observation": "Email field appears first, password after clicking continue",
    "success": True
})
```

### Keep It Simple
```python
# GOOD - One executor that handles everything
executor.run_task(objective, context)
# Works for login, for clicking buttons, for filling forms, etc.
```

---

## Architecture Summary

```
User Request
    ↓
Parse Intent (LLM)
    ↓
Check Memory (Have I done this before?)
    ↓
Research if Needed (Web search)
    ↓
Create Plan (LLM)
    ↓
Execute with Hybrid Executor
    ├── UI Automation (preferred)
    └── Vision (fallback)
    ↓
Store Observations in Memory
    ↓
Learn from Success/Failure
```

---

## Key Files

| File | Purpose |
|------|---------|
| `learning_agent.py` | Main orchestrator - the brain |
| `hybrid_executor.py` | Executes actions (UI + vision) |
| `windows_ui.py` | Windows UI Automation |
| `skill_library.py` | Stores learned observations |
| `credential_store.py` | Stores passwords (just data) |

---

## Before Adding Code, Ask:

1. **Does this make the agent smarter, or just add rules?**
2. **Will this work if the website/app changes?**
3. **Is the LLM still making the decisions?**
4. **Am I storing observations or hardcoding steps?**

If you're writing specific steps for a specific task, you're probably
going in the wrong direction. The agent should LEARN those steps by doing.

---

## The Goal

A single agent that can:
1. Receive ANY task
2. Figure out how to do it (research if needed)
3. Execute by watching and interacting
4. Get smarter with each attempt
5. Eventually become a "one stop shop" that knows how to do everything

NOT a collection of scripts for specific tasks.
