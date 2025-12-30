# DrCodePT-Swarm Architecture

Terminology note: The agent has no visible modes; it uses a single unified loop with internal planner types (react/plan_first).



Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
## Overview

DrCodePT-Swarm is a production-grade autonomous agent with a closed-loop architecture designed for complex, multi-step task execution. The system combines LLM-powered planning with structured tool execution, memory persistence, and self-healing capabilities.

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER TASK                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT RUNNER                               │
│  • Orchestrates the closed-loop                                 │
│  • Enforces safety limits (steps, time, cost)                   │
│  • Manages state and observations                               │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐       ┌──────────┐
    │ PLANNER  │       │  TOOLS   │       │ MEMORY   │
    │ (LLM)    │◄─────►│ REGISTRY │◄─────►│  STORE   │
    └──────────┘       └──────────┘       └──────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      REFLECTOR                                  │
│  • Evaluates step outcomes                                      │
│  • Determines next action (success/repair/replan)               │
│  • Extracts lessons for memory                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Loop

The agent operates in a continuous perception-action-reflection loop:

```
1. PERCEIVE    → Gather observations from environment
2. RETRIEVE    → Query long-term memory for relevant context
3. PLAN        → LLM generates next step(s)
4. EXECUTE     → Run tool with pre/post condition checks
5. OBSERVE     → Capture tool result as new observation
6. REFLECT     → LLM evaluates outcome, extracts lessons
7. REMEMBER    → Store experiences/procedures in memory
8. REPEAT      → Continue until goal achieved or limit hit
```

## Directory Structure

```
DrCodePT-Swarm/
├── agent/
│   ├── autonomous/           # Core autonomous agent
│   │   ├── runner.py         # Main orchestration loop
│   │   ├── config.py         # Configuration dataclasses
│   │   ├── models.py         # Pydantic models (Step, Plan, Observation, etc.)
│   │   ├── state.py          # Agent state management
│   │   ├── perception.py     # Observation processing
│   │   ├── reflection.py     # Outcome evaluation
│   │   ├── loop_detection.py # Stuck/loop detection
│   │   ├── trace.py          # JSONL tracing
│   │   ├── planning/
│   │   │   ├── react.py      # Single-step reactive planner
│   │   │   ├── plan_first.py # Multi-step planner with ToT
│   │   │   └── base.py       # Planner interface
│   │   ├── tools/
│   │   │   ├── registry.py   # Tool registration system
│   │   │   └── builtins.py   # Built-in tools (web, fs, shell, etc.)
│   │   └── memory/
│   │       └── sqlite_store.py # Persistent memory with embeddings
│   │
│   ├── integrations/         # External service integrations
│   │   ├── yahoo_mail.py     # IMAP/SMTP for Yahoo Mail
│   │   └── google_apis.py    # Google Calendar, Drive, etc.
│   │
│   ├── llm/                  # LLM backends
│   │   ├── base.py           # LLMClient interface
│   │   ├── codex_cli_client.py # Codex CLI backend
│   │   └── schemas/          # JSON schemas for structured output
│   │
│   ├── memory/               # Memory subsystem
│   │   ├── credentials.py    # Secure credential storage
│   │   └── procedures/       # Procedural memory (e.g., mail rules)
│   │
│   ├── logging/              # Logging infrastructure
│   │   ├── run_logger.py     # Run-level event logging
│   │   └── structured_logger.py # Structured JSON logging
│   │
│   └── run.py                # CLI entrypoint
│
├── tests/                    # Test suite
├── runs/                     # Execution traces (gitignored)
├── docs/                     # Additional documentation
└── scripts/                  # Utility scripts
```

## Component Details

### 1. AgentRunner (`runner.py`)

The central orchestrator managing the agent lifecycle:

**Key Responsibilities:**
- Initialize run context (ID, directories, tracer)
- Enforce safety limits:
  - `max_steps`: Maximum execution steps (default: 30)
  - `timeout_seconds`: Wall-clock timeout (default: 600s)
  - `cost_budget_usd`: Optional LLM cost cap
  - Kill switch file/env var
- Detect stuck states:
  - Loop detection (repeated action signatures)
  - No-state-change detection (fingerprint comparison)
- Manage LLM/tool retries with exponential backoff
- Coordinate planning → execution → reflection cycle

**Stop Conditions:**
| Reason | Description |
|--------|-------------|
| `goal_achieved` | Task completed successfully |
| `max_steps` | Step limit reached |
| `timeout` | Time limit exceeded |
| `budget_exceeded` | Cost cap hit |
| `loop_detected` | Repeated action pattern |
| `no_state_change` | State hasn't changed |
| `no_progress` | Consecutive failures |
| `kill_switch` | Manual abort |
| `unsafe_action_blocked` | Safety system triggered |

### 2. Planners

Two planning strategies available:

#### ReAct Planner (`react.py`)
- Single-step reactive planning
- Best for: Simple tasks, exploratory work
- Replans after every action
- Lower latency, more flexible

#### Plan-First Planner (`plan_first.py`)
- Multi-step upfront planning
- Best for: Complex, multi-stage tasks
- Features:
  - Multiple candidate plans (configurable)
  - DPPM (Dynamic Plan Priority Model) ranking
  - ToT-lite (Tree of Thoughts) fallback branches
  - Plan repair on step failure

**Auto-Selection Heuristics:**
- Word count > 12 → plan_first
- Contains conjunctions (and, then, after) → plan_first
- Contains planning keywords (implement, build, create) → plan_first
- Otherwise → react

### 3. Tool Registry (`tools/`)

Centralized tool management with:
- Dynamic registration
- Schema validation
- Approval gates for dangerous operations
- Retry logic

**Built-in Tool Categories:**

| Category | Tools | Description |
|----------|-------|-------------|
| **Web** | `web_fetch`, `web_search`, `web_gui_snapshot`, `web_click`, `web_type` | HTTP requests, search, browser automation |
| **Filesystem** | `file_read`, `file_write`, `list_dir`, `glob_paths`, `file_copy`, `file_move`, `file_delete` | File operations |
| **Shell** | `shell_exec`, `python_exec` | Command/script execution |
| **Desktop** | `desktop_som_snapshot`, `desktop_click`, `desktop_type` | GUI automation |
| **Memory** | `memory_store`, `memory_search` | Long-term memory operations |
| **Control** | `finish`, `delegate_task`, `human_ask` | Flow control |

### 4. Memory System (`memory/sqlite_store.py`)

Hybrid memory with semantic search:

**Memory Kinds:**
| Kind | Purpose | Example |
|------|---------|---------|
| `experience` | Past task outcomes | "Search for X usually works with DuckDuckGo" |
| `procedure` | Reusable workflows | "To clear Yahoo spam: select all → delete" |
| `knowledge` | Factual information | Web fetch results, documentation |
| `user_info` | User preferences | (Disabled by default for privacy) |

**Search Algorithm:**
1. Generate query embedding (Sentence Transformer or hash fallback)
2. If FAISS available: ANN search for top-k candidates
3. Score = 0.85 × cosine_similarity + 0.15 × recency
4. Return top results

**Embedding Models:**
- Primary: `all-MiniLM-L6-v2` (384 dims)
- Fallback: Hash-based (256 dims, no ML dependency)

### 5. Reflection System (`reflection.py`)

Post-action analysis:

```python
class Reflection:
    status: "success" | "minor_repair" | "replan"
    explanation_short: str
    next_hint: str
    failure_type: str
    lesson: str  # Stored to memory
    memory_write: Optional[Dict]  # Explicit memory update
```

**Reflection Outcomes:**
- `success`: Proceed to next step
- `minor_repair`: Attempt localized fix
- `replan`: Discard current plan, generate new one

### 6. LLM Backend (`llm/codex_cli_client.py`)

Uses local Codex CLI for inference:
- No API keys required (uses `codex login`)
- Two profiles:
  - `reason`: Planning/reflection (tools disabled)
  - `exec`: Execution (tools enabled)
- Structured JSON output via `--output-schema`
- Automatic timeout and retry handling

## Data Flow

### Execution Trace

Every run produces a JSONL trace at `runs/autonomous/<run_id>/trace.jsonl`:

```json
{"type": "observation", "observation": {...}}
{"type": "step", "step_index": 0, "plan": {...}, "action": {...}, "result": {...}, "reflection": {...}}
{"type": "memory_write", "kind": "procedure", "key": "...", "record_id": 123}
{"type": "stop", "reason": "goal_achieved", "success": true, "steps": 5}
```

### State Management

```python
class AgentState:
    task: str                    # Original user task
    observations: List[Observation]  # History (auto-compacted)
    rolling_summary: str         # LLM-generated summary of dropped observations
    current_plan: Optional[Plan] # Active plan (plan_first mode)
    current_step_idx: int        # Progress within plan

    def state_fingerprint(self) -> str:
        # Hash of recent observations for change detection
```

## Safety Mechanisms

### 1. Stop Conditions
- Step limit, time limit, cost budget
- Loop and stuck detection
- Kill switch (file or env var)

### 2. Pre/Post Conditions
- Steps can specify preconditions (checked before execution)
- Steps can specify postconditions (checked after execution)
- Failed conditions trigger recovery or replan

### 3. Recovery Attempts
On failure, the agent attempts:
1. Close modal dialogs (`web_close_modal`)
2. Search for target elements (`web_find_elements`)
3. Scroll to reveal content (`web_scroll`)
4. Resnapshot UI (`web_gui_snapshot`, `desktop_som_snapshot`)

### 4. Approval Gates
Dangerous tools (delete, move outside workspace) require human approval via `human_ask`.

### 5. Memory Isolation
- `user_info` storage disabled by default
- Filesystem roots configurable (though currently bypassed)

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEX_BIN` | `codex` | Path to Codex CLI |
| `CODEX_EXE_PATH` | (unset) | Full path to codex executable |
| `CODEX_CLI_PATH` | (unset) | Alias for codex executable path |
| `CODEX_MODEL` | (default) | Override LLM model |
| `CODEX_MODEL_FAST` | (unset) | Fast/default Codex model |
| `CODEX_MODEL_REASON` | (unset) | Higher-reasoning Codex model |
| `CODEX_REASONING_EFFORT_FAST` | `low` | Reasoning effort for fast tasks |
| `CODEX_REASONING_EFFORT_REASON` | `high` | Reasoning effort for hard tasks |
| `CODEX_TIMEOUT_SECONDS` | `120` | LLM call timeout |
| `AGENT_MEMORY_EMBED_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `AGENT_MEMORY_EMBED_BACKEND` | auto | `hash` for fallback |
| `AGENT_MEMORY_FAISS_DISABLE` | `0` | Disable FAISS acceleration |
| `AGENT_KILL_SWITCH` | `0` | Set to `1` to abort |
| `AGENT_KILL_FILE` | none | Path to kill switch file |
| `LLM_COST_PER_1K_TOKENS_USD` | none | Enable cost tracking |

### RunnerConfig

```python
@dataclass
class RunnerConfig:
    max_steps: int = 30
    timeout_seconds: int = 600
    cost_budget_usd: Optional[float] = None
    loop_repeat_threshold: int = 3
    loop_window: int = 8
    no_state_change_threshold: int = 3
    tool_max_retries: int = 2
    tool_retry_backoff_seconds: float = 0.8
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 1.2
```

### AgentConfig

```python
@dataclass
class AgentConfig:
    unsafe_mode: bool = False           # Bypass some safety checks
    enable_web_gui: bool = False        # Enable browser automation
    enable_desktop: bool = False        # Enable desktop automation
    allow_user_info_storage: bool = False  # Allow storing user data
    memory_db_path: Optional[Path] = None  # Custom memory DB location
    pre_mortem_enabled: bool = False    # Enable pre-execution analysis
    allow_human_ask: bool = False       # Enable human-in-the-loop
```

## Extending the Agent

### Adding a New Tool

1. Create tool function with signature:
```python
def my_tool(ctx: RunContext, args: MyToolArgs) -> ToolResult:
    # Implementation
    return ToolResult(success=True, output={...})
```

2. Define args model:
```python
class MyToolArgs(BaseModel):
    param1: str
    param2: int = 10
```

3. Register in `build_default_tool_registry()`:
```python
registry.register(
    ToolSpec(
        name="my_tool",
        description="Does something useful",
        dangerous=False,
    ),
    my_tool,
    MyToolArgs,
)
```

### Adding a New Integration

1. Create module in `agent/integrations/`
2. Add credential handling in `agent/memory/credentials.py`
3. Create procedural memory schema in `agent/memory/procedures/`
4. Add tools that wrap the integration

## Future Improvements

- [ ] Re-enable filesystem safety with proper configuration
- [ ] Add rate limiting for web requests
- [ ] Implement context variables for structured logging
- [ ] Add async tool execution
- [ ] Multi-agent coordination via `delegate_task`
- [ ] Visual grounding improvements (SoM, A11y tree)
- [ ] Checkpoint/resume for long-running tasks
