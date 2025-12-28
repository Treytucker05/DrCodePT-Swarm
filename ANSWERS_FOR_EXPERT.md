# Answers to Architecture Questions

## 1. Current Repo Tree (Key Structure)

```
DrCodePT-Swarm/
├── agent/
│   ├── autonomous/              # Core autonomous agent
│   │   ├── runner.py           # AgentRunner - main execution loop
│   │   ├── react_loop.py       # ReAct logic (think→plan→execute→reflect)
│   │   ├── config.py           # Configuration
│   │   ├── tools/              # Tool definitions
│   │   ├── memory/             # Memory system
│   │   ├── planning/           # Planning logic
│   │   ├── supervisor/         # Supervisor orchestration
│   │   └── workers/            # Worker processes
│   │
│   ├── modes/                  # Different execution modes (BLOAT)
│   │   ├── autonomous.py       # Launcher for autonomous mode
│   │   ├── swarm.py           # Swarm mode (1200+ lines)
│   │   ├── collaborative.py   # Collaborative mode
│   │   ├── execute.py         # Playbook execution mode
│   │   ├── research.py        # Research mode
│   │   └── [others]
│   │
│   ├── tools/                 # Tool implementations
│   │   ├── registry.py        # Tool registry
│   │   ├── browser.py         # Browser automation
│   │   ├── fs.py             # File system operations
│   │   ├── shell.py          # Shell command execution
│   │   ├── python_exec.py    # Python execution
│   │   └── [others]
│   │
│   ├── llm/                   # LLM clients
│   │   ├── codex_cli_client.py # Codex CLI wrapper (currently using gpt-5)
│   │   ├── base.py
│   │   └── schemas/           # JSON schemas for responses
│   │
│   ├── memory/                # Memory/persistence
│   │   ├── autonomous_memory.sqlite3
│   │   ├── memory_manager.py
│   │   └── credentials.json
│   │
│   ├── mcp/                   # MCP server integration
│   │   ├── client.py
│   │   ├── registry.py
│   │   └── servers.json       # MCP server configs
│   │
│   ├── playbooks/             # Rigid playbook system (WANT TO DELETE)
│   │   └── index.json
│   │
│   └── treys_agent.py         # Main launcher (2096 lines - TOO COMPLEX)
│
├── launchers/
│   └── TREYS_AGENT.bat        # Launch script
│
├── requirements.txt
├── .env                       # Environment variables
└── [documentation files]
```

## 2. Main Loop Location

**Primary loop:** `agent/autonomous/runner.py` (AgentRunner class)
- Uses: `agent/autonomous/react_loop.py` for ReAct logic
- Entry point: `agent/treys_agent.py` (routes to different modes)
- Autonomous launcher: `agent/modes/autonomous.py`

**Current flow:**
```
treys_agent.py (2096 lines)
  → smart_orchestrator() (keyword-based routing - BROKEN)
    → modes/autonomous.py
      → autonomous/runner.py (AgentRunner)
        → react_loop.py (actual ReAct execution)
```

**The problem:** Too many layers between user input and AgentRunner.

## 3. Implemented Tools

### ✅ Fully Implemented

**File Operations:**
- `read_file` - Read file contents
- `write_file` - Write/overwrite files
- `list_dir` - List directory contents
- `file_search` - Search for files by pattern
- `scan_repo` - Repository scanning

**Web:**
- `web_search` - Web search (available)
- `web_fetch` - Fetch webpage contents (available)

**Browser Automation (via Windows-MCP):**
- `browser_navigate` - Navigate to URLs
- `browser_click` - Click elements
- `browser_type` - Type text
- `browser_screenshot` - Take screenshots
- Full browser automation suite via MCP

**Desktop Automation (via Windows-MCP):**
- Window management
- Mouse/keyboard control
- Screen capture
- Desktop interaction

**Shell:**
- `execute_command` - Run shell commands
- Allowlist-based (safe commands only)
- Blocklist for dangerous commands

**Python:**
- `python_exec` - Execute Python code
- Sandboxed execution

**Git (Basic):**
- `git_status` - Get repo status
- `git_diff` - Show diffs
- `git_commit` - Make commits
- Basic operations implemented

**Calendar (MCP - Connected but not fully integrated):**
- Google Calendar MCP server connected
- Tools exist but not wired to main loop
- OAuth setup incomplete

**Memory:**
- SQLite-based storage (`autonomous_memory.sqlite3`)
- Memory manager exists
- Not fully integrated into loop

### ❌ Not Implemented / Needs Work

**Calendar Integration:**
- MCP server connected but not integrated into autonomous loop
- OAuth credentials not set up
- Tools not accessible from main agent

**Email:**
- Some Yahoo mail integration exists
- Not reliable
- Needs work

**Advanced Git:**
- Branch management incomplete
- Complex operations missing

### 🔧 Tool Infrastructure

**Registry:** `agent/tools/registry.py`
- All tools defined and loadable
- AgentRunner can access them
- MCP tools not fully integrated into registry

**Guardrails:**
- Command allowlist exists
- Dangerous command blocking works
- File system restrictions in place
- Logs all tool calls

**MCP Integration:**
- MCP client: `agent/mcp/client.py`
- Server configs: `agent/mcp/servers.json`
- Connected servers:
  - Google Calendar
  - Google Tasks
  - Windows-MCP (browser/desktop)
- **Problem:** MCP tools not accessible in playbook mode

## 4. Current Architecture Issues

### The Routing Problem

**Current (Broken):**
```python
# smart_orchestrator uses keyword matching
if "research" in query: → research mode
if "repo" in query: → repo mode
if "oauth" in query: → ??? (fails)
```

**Result:** Fragile, unpredictable routing

### The Mode Fragmentation Problem

**Too many separate modes:**
- autonomous mode (ReAct loop)
- swarm mode (multi-agent)
- collaborative mode
- playbook mode (execute.py)
- research mode
- chat mode

**Each mode has different:**
- Tool access
- Planning logic
- Error handling
- Memory integration

### The Codex Usage Problem

**Currently using Codex (gpt-5) for:**
- Routing decisions
- Planning steps
- Executing tools
- Everything

**Issues:**
- Expensive
- Sometimes flaky for structured JSON
- Overkill for simple routing

## 5. What We Want

**One unified agent that:**
- Decides intelligently what it needs (cheap planner)
- Routes to appropriate execution:
  - Code tasks → Codex
  - Tool tasks → Python executor
  - Chat → Cheap model
  - Research → Multi-step with tools
- Learns from experience (memory)
- Stays cheap (use right model for each job)

## 6. Current Dependencies

From `requirements.txt`:
```
openai>=1.0.0
anthropic
python-dotenv
colorama
playwright
google-auth-oauthlib
google-api-python-client
sqlite-utils
sentence-transformers
torch
[many others]
```

**Codex CLI:** Installed globally via npm
- Path: `C:\Users\treyt\AppData\Roaming\npm\node_modules\@openai\codex`
- Using for all LLM calls currently

## 7. Key Files Mentioned in Plans

**Your unified agent plan created:**
- `UNIFIED_AGENT_PLAN.md` - Vision
- `IMPLEMENTATION_STEPS.md` - How to build
- `STATUS.md` - Progress tracking
- `README_START_HERE.md` - Quick reference

**Wants to create:**
- `agent/core/intelligent_orchestrator.py` - LLM-based routing
- `agent/core/unified_agent.py` - Single agent class

**Wants to delete (eventually):**
- `agent/modes/swarm.py`
- `agent/modes/collaborative.py`
- `agent/modes/execute.py`
- `agent/playbooks/`
- Most of `treys_agent.py`

## Summary

**We have:**
- ✅ Solid core: AgentRunner + ReAct loop
- ✅ Good tools: File, web, browser, desktop, shell, Python
- ✅ Basic guardrails: Allowlists, blocklists, logging
- ❌ Broken routing: Keyword-based, fragile
- ❌ Too many modes: Fighting each other
- ❌ Codex for everything: Expensive, wrong tool for routing
- ❌ MCP not integrated: Calendar/Tasks connected but not accessible
- ❌ Playbooks broken: Want to delete anyway

**We need:**
- Cheap planner for routing/decisions (OpenRouter gpt-4o-mini?)
- Codex only for coding tasks
- Unified agent structure
- Delete the bloat
- Wire up MCP tools properly
