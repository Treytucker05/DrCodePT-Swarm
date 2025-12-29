# Agent Refactoring Plan: Unified Architecture

## REFACTORING COMPLETE

All modules have been implemented:

| Module | Status | Description |
|--------|--------|-------------|
| 0 - Baseline | COMPLETE | Docs, logs, safety rails |
| 1 - Single Entrypoint | COMPLETE | CLI, __main__.py |
| 2 - Unified Tool Registry | COMPLETE | Local + MCP tools merged |
| 3 - Model Router | COMPLETE | OpenRouter, Codex, Claude routing |
| 4 - Single ReAct Loop | COMPLETE | Runner + guards integration |
| 5 - Codex as Tool | COMPLETE | codex_task tool |
| 6 - Memory Integration | COMPLETE | memory_store, memory_search tools |
| 7 - Calendar MCP | COMPLETE | Calendar tool wrappers |
| 8 - Anti-Thrash Guards | COMPLETE | Loop detection |
| 9 - Cleanup | COMPLETE | Verified, legacy preserved |

### Quick Start
```python
# Use the unified runner
from agent.autonomous.runner import create_unified_runner
runner = create_unified_runner(profile="fast", use_router=True)
result = runner.run("Your task here")
```

---

## Goal Architecture

One unified agent with one loop and one tool registry:

- **Single loop**: `AgentRunner` (`agent/autonomous/runner.py`)
- **Single reasoning interface**: `react_loop.py` makes one decision per step
- **Single tool registry**: local tools + MCP tools merged (`agent/tools/registry.py`)
- **Model router**:
  - Cheap planner (OpenRouter) for: "choose next action", chat, summarization
  - Codex CLI only for: repo coding/audit tasks (as a tool, not the brain)
  - Claude optionally for: long-context review (rare, controlled)
- Playbooks deleted. "Modes" deleted as separate systems. "Swarm" parked/archived.

---

## Module 0 - Baseline and Safety Rails (COMPLETE)

### Outcome
You can refactor without breaking everything and you always have rollback.

### Change / Create
- [x] Create: `docs/REFRACTOR_PLAN.md` (this file)
- [x] Create: `docs/ACCEPTANCE_TESTS.md`
- [x] Create: `logs/` (if not present) and ensure it's gitignored if needed

### Definition of Done
- You can run the current agent, capture logs, and revert any changes via git.

### Quick Test
```bash
python -m agent.main --menu
# or
python -m agent.treys_agent
```
Should still run before you start.

---

## Module 1 - Single Entrypoint (COMPLETE)

### Outcome
User input goes straight into AgentRunner. No more keyword router. No more competing modes.

### Files Created
- [x] `agent/__main__.py` - enables `python -m agent`
- [x] `agent/cli.py` - unified CLI entrypoint with argparse

### Files Changed
- [x] `agent/main.py` - now defaults to unified agent (use `--menu` for legacy)
- [x] `launchers/TREYS_AGENT.bat` - updated to use `python -m agent --interactive`

### Files Archived
- [x] `agent/treys_agent.py` -> `agent/_legacy/treys_agent_legacy.py`
- [x] `agent/modes/` -> `agent/_legacy/modes/`

### Definition of Done
- `python -m agent` launches the unified agent and reaches AgentRunner without touching modes/router code.

### Quick Test
```bash
python -m agent --help
python -m agent "hello"
python -m agent --interactive
python -m agent --legacy  # runs old treys_agent if needed
```

---

## Module 2 - Unified Tool Registry (COMPLETE)

### Outcome
Single tool registry that merges local tools + MCP tools.

### Files Created
- [x] `agent/tools/types.py` - ToolSpec, ToolResult, LocalToolSpec, McpToolSpec
- [x] `agent/tools/mcp_proxy.py` - MCP tool adapter with known tool definitions
- [x] `agent/tools/unified_registry.py` - merged registry class

### Files Changed
- [x] `agent/mcp/registry.py` - added McpToolInfo, list_available_tools(), get_tool_info()
- [x] `agent/cli.py` - added --list-tools flag and 'tools' command

### Files to Delete/Archive
- None (keep existing for backward compat initially)

### Definition of Done
- [x] `UnifiedRegistry` can list both local and MCP tools
- [x] Tool calls work for both sources
- [x] No duplication of tool execution logic

### Quick Test
```bash
python -m agent --list-tools
```
Or in interactive mode:
```
> tools
```

```python
from agent.tools.unified_registry import UnifiedRegistry
reg = UnifiedRegistry()
reg.initialize()
tools = reg.get_tool_names()
print(f"Total tools: {len(tools)}")
# Should show local tools AND MCP tools (google-calendar.*, google-tasks.*, etc.)
```

---

## Module 3 - Model Router (COMPLETE)

### Outcome
Smart routing of LLM calls to appropriate backend.

### Files Created
- [x] `agent/llm/openrouter_client.py` - OpenAI-compatible client for cheap planning
- [x] `agent/llm/router.py` - model routing logic with TaskType enum
- [x] `agent/llm/schemas/next_action.schema.json` - minimal action schema
- [x] `agent/scripts/test_planner_json.py` - test script for validation

### Files Changed
- [x] `agent/llm/base.py` - added generate_text, generate_json, get_default_llm

### Definition of Done
- [x] Planning calls go to cheap planner (OpenRouter)
- [x] Coding tasks route to Codex CLI
- [x] Long-context review routes to Claude (optional)
- [x] Routing keywords detect task type

### Quick Test
```bash
python -m agent.scripts.test_planner_json
```
Or:
```python
from agent.llm.router import get_model_router
router = get_model_router()
print(router.route_for_task("plan next step"))  # -> openrouter
print(router.route_for_task("fix this bug"))    # -> codex
```

---

## Module 4 - Single ReAct Loop (COMPLETE)

### Outcome
One loop to rule them all - ReAct pattern as the core.

### Files Created
- [x] `agent/autonomous/state.py` - added UnifiedAgentState, StopReason, StepRecord

### Files Changed
- [x] `agent/autonomous/runner.py` - integrated with router and thrash guard:
  - Added `model_router` parameter for smart LLM routing
  - Added `thrash_guard` integration using ThrashGuard
  - Added `_check_thrash_guard()` method for loop detection
  - Added `create_unified_runner()` factory function
- [x] `agent/autonomous/planning/react.py` - refactored for clarity:
  - Added `_get_planning_llm()` for router integration
  - Added `_build_tool_catalog()` and `_build_plan_prompt()` helpers
  - Added `_validate_plan()` for plan validation
  - Improved docstrings and code organization

### Files Archived (from Module 1)
- [x] `agent/modes/` -> `agent/_legacy/modes/`

### Definition of Done
- [x] UnifiedAgentState tracks all execution state
- [x] StopReason enum for termination conditions
- [x] One decision per step (ReAct planner returns single step)
- [x] Clear observation -> thought -> action -> result cycle
- [x] Model router integration for LLM selection
- [x] Thrash guard integration for loop detection

### Quick Test
```python
from agent.autonomous.state import create_unified_state, StopReason
state = create_unified_state("List files", max_steps=10)
print(state.is_running)  # True
print(state.should_stop())  # StopReason.NONE

# Or use the factory:
from agent.autonomous.runner import create_unified_runner
runner = create_unified_runner(profile="fast", use_router=True)
result = runner.run("List files in current directory")
```

---

## Module 5 - Codex as Tool (COMPLETE)

### Outcome
Codex CLI is a tool, not the brain.

### Files Created
- [x] `agent/tools/codex_task.py` - Codex CLI wrapper tool with:
  - `CodexTaskArgs` - task, constraints, target_paths, test_command, timeout
  - `CodexTaskResult` - success, summary, files_changed, diff_summary
  - `codex_task()` - main execution function
  - `codex_task_tool()` - tool registry wrapper
  - Convenience functions: `codex_fix_bug()`, `codex_add_feature()`, `codex_audit()`, `codex_refactor()`

### Files Changed
- [x] `agent/tools/unified_registry.py` - registers codex_task tool

### Definition of Done
- [x] Can call `codex_task` from the agent loop
- [x] Codex handles repo coding/audit tasks
- [x] Results flow back to the main loop

### Quick Test
```python
from agent.tools.codex_task import CodexTaskArgs, codex_task
result = codex_task(CodexTaskArgs(task="list python files", target_paths=["."]))
print(result.success)
```

---

## Module 6 - Memory Integration (COMPLETE)

### Outcome
Memory tools available through unified registry.

### Files Created
- [x] `agent/tools/memory.py` - Memory tool wrappers with:
  - Pydantic models: `MemoryStoreArgs`, `MemorySearchArgs`, `MemoryRetrieveArgs`, `MemoryDeleteArgs`
  - Functions: `memory_store()`, `memory_search()`, `memory_retrieve()`, `memory_delete()`
  - `MEMORY_TOOL_SPECS` for registry integration
  - `register_memory_tools()` helper

### Files Changed
- [x] `agent/tools/unified_registry.py` - registers memory tools via `_register_memory_tools()`

### Definition of Done
- [x] Can store and retrieve memories from agent loop
- [x] Similar memory search works for context
- [x] Integrated with unified tool registry

### Quick Test
```python
from agent.tools.memory import MemoryStoreArgs, memory_store, MemorySearchArgs, memory_search
# Store a memory
result = memory_store(None, MemoryStoreArgs(content="Test memory", kind="knowledge"))
print(result.success)  # True

# Search memories
result = memory_search(None, MemorySearchArgs(query="test", limit=5))
print(result.output["count"])  # Number of matches
```

---

## Module 7 - Calendar MCP (COMPLETE)

### Outcome
Calendar tools wrapped as stable interfaces.

### Files Created
- [x] `agent/tools/calendar.py` - Calendar tool wrappers with:
  - Pydantic models: `ListEventsArgs`, `CreateEventArgs`, `UpdateEventArgs`, `DeleteEventArgs`, `FindFreeSlotsArgs`
  - Functions: `calendar_list_events()`, `calendar_create_event()`, `calendar_update_event()`, `calendar_delete_event()`, `calendar_find_free_slots()`
  - `CALENDAR_TOOL_SPECS` for registry integration
  - `register_calendar_tools()` helper

### Files Changed
- [x] `agent/tools/unified_registry.py` - registers calendar tools

### Definition of Done
- [x] Calendar operations work through MCP
- [x] Clean Pydantic interfaces for all calendar operations
- [x] Integrated with unified tool registry

### Quick Test
```python
from agent.tools.calendar import ListEventsArgs, calendar_list_events
args = ListEventsArgs(max_results=5)
result = calendar_list_events(None, args)
print(result.success)
```

---

## Module 8 - Anti-Thrash Guards (COMPLETE)

### Outcome
Prevent agent from getting stuck in loops.

### Files Created
- [x] `agent/autonomous/guards.py` - Anti-thrash detection with:
  - `ThrashType` enum: NONE, REPEATED_ACTION, REPEATED_FILE_READ, NO_PROGRESS, SAME_ERROR
  - `EscalationAction` enum: CONTINUE, WARN, SWITCH_STRATEGY, USE_CODEX, ASK_USER, STOP
  - `ThrashGuard` class with detection and escalation logic
  - `GuardConfig` for configurable thresholds
  - `check_guards()` convenience function

### Definition of Done
- [x] Detects repeated actions (same action called N times)
- [x] Detects repeated file reads (same file read N times)
- [x] Detects no progress (steps without advancement)
- [x] Detects repeated errors (same error message)
- [x] Provides escalation suggestions (switch strategy, use Codex, ask user)

### Quick Test
```python
from agent.autonomous.guards import ThrashGuard, GuardConfig
from agent.autonomous.state import create_unified_state

guard = ThrashGuard(GuardConfig(max_repeated_actions=3))
state = create_unified_state("test task")
detection = guard.check(state)
print(detection.detected)  # False initially
```

---

## Module 9 - Cleanup and Archive (COMPLETE)

### Outcome
Unified architecture verified, legacy code preserved for rollback.

### Files Archived (in `agent/_legacy/`)
- [x] `agent/_legacy/modes/` - Old mode system (copy of agent/modes/)
- [x] `agent/_legacy/treys_agent_legacy.py` - Old agent entry point

### Status
- Legacy code preserved in `_legacy/` directory for rollback capability
- Original `agent/modes/` kept for backward compatibility during transition
- All new unified architecture modules verified working
- Clean import graph confirmed

### Definition of Done
- [x] Clean import graph - all modules import successfully
- [x] No circular dependencies
- [x] Factory functions available for easy instantiation
- [x] Legacy code archived but accessible

### Quick Test
```bash
# Test all unified components
python -c "from agent.autonomous.runner import AgentRunner, create_unified_runner; print('OK')"
python -c "from agent.tools.unified_registry import UnifiedRegistry, get_unified_registry; print('OK')"
python -c "from agent.llm.router import get_model_router; print('OK')"
python -c "from agent.autonomous.guards import ThrashGuard, check_guards; print('OK')"
python -c "from agent.tools.codex_task import codex_task, CodexTaskArgs; print('OK')"
python -c "from agent.tools.calendar import CALENDAR_TOOL_SPECS; print('OK')"
python -c "from agent.tools.memory import MEMORY_TOOL_SPECS; print('OK')"
```

---

## Current State Analysis

### Existing Structure
```
agent/
  autonomous/
    runner.py          # Main loop (keep, refactor)
    planning/
      react.py         # ReAct planner (keep, simplify)
      plan_first.py    # Multi-step planner (archive)
    tools/
      registry.py      # Tool registry (merge with mcp)
  mcp/
    registry.py        # MCP server registry (integrate)
  tools/
    base.py            # Tool base classes (keep)
    *.py               # Individual tools (keep)
  modes/               # Mode system (archive)
  llm/
    base.py            # LLM interface (add router)
```

### Key Dependencies
- `runner.py` depends on `react.py` or `plan_first.py`
- `react.py` depends on `tools/registry.py`
- `tools/registry.py` is self-contained

### Integration Points
1. Tool execution flows through `ToolRegistry.call()`
2. LLM calls flow through `LLMClient.complete_json()` or `reason_json()`
3. MCP tools loaded from `mcp/servers.json`

---

## Migration Strategy

1. **Don't break existing** - keep backward compat during transition
2. **Feature flags** - use env vars to enable new code paths
3. **Parallel run** - run old and new, compare results
4. **Gradual rollout** - one module at a time

### Environment Variables
```bash
AGENT_USE_UNIFIED_REGISTRY=1   # Enable unified tool registry
AGENT_USE_MODEL_ROUTER=1       # Enable model routing
AGENT_USE_REACT_ONLY=1         # Force ReAct mode
```

---

## Rollback Plan

Each module is reversible:
1. Revert git commits
2. Remove feature flags
3. Old code remains functional

Keep dated backups in `archive/` with timestamps.
