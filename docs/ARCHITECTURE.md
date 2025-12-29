# DrCodePT-Swarm Architecture

## Overview

DrCodePT-Swarm is a production-grade autonomous AI agent framework for Windows 11. The agent follows a unified execution model:

```
Observe → Decide → Act → Verify → Learn/Store → Repeat
```

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENTRY POINTS                              │
│  CLI (agent/cli.py) │ API │ Tests                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED AGENT                                 │
│  agent/core/unified_agent.py                                     │
│  - Single entry point for all tasks                             │
│  - Coordinates orchestrator, tools, memory, safety              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 INTELLIGENT ORCHESTRATOR                         │
│  agent/core/intelligent_orchestrator.py                          │
│  - LLM-based strategy selection (not keyword matching)          │
│  - Returns structured JSON: {needs_tools, risk_level, skill...} │
│  - Validates output against schema                              │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────────┐    ┌───────────────┐
│   PLANNING    │    │   TOOL REGISTRY   │    │    SKILLS     │
│               │    │                   │    │               │
│ - ReAct loop  │    │ - Schema-valid    │    │ - Calendar    │
│ - Plan-first  │    │ - Pre/post conds  │    │ - Browser     │
│ - Reflection  │    │ - Retries         │    │ - Filesystem  │
└───────────────┘    └───────────────────┘    └───────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION MONITOR                             │
│  - Precondition checks before tool execution                    │
│  - Postcondition verification after execution                   │
│  - Retry with exponential backoff                               │
│  - Fallback strategies on failure                               │
│  - Stuck-loop detection (ThrashGuard)                           │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────────┐    ┌───────────────┐
│    MEMORY     │    │     SECURITY      │    │   TRACING     │
│               │    │                   │    │               │
│ - Embeddings  │    │ - Kill switch     │    │ - JSONL logs  │
│ - Semantic    │    │ - Approvals       │    │ - Structured  │
│ - Recency     │    │ - Allowlists      │    │ - Artifacts   │
│ - Persistence │    │ - Secret redact   │    │               │
└───────────────┘    └───────────────────┘    └───────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM ADAPTERS                                  │
│  agent/adapters/                                                 │
│  - OpenRouterAdapter (required, primary)                        │
│  - OpenAIAdapter (optional)                                     │
│  - CodexCLIAdapter (optional, for code tasks)                   │
│  - Graceful failover between providers                          │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Unified Agent (`agent/core/unified_agent.py`)
The single entry point for all task execution. Responsibilities:
- Accept user input (text, file, or structured task)
- Coordinate with orchestrator for strategy
- Execute via appropriate runner/skill
- Manage memory and learning
- Ensure safety constraints
- Produce execution traces

### 2. Intelligent Orchestrator (`agent/core/intelligent_orchestrator.py`)
LLM-based strategy selection replacing brittle keyword matching.

**Input:** User request + context
**Output:** Structured JSON strategy:
```json
{
  "needs_tools": true,
  "needs_web": false,
  "needs_deep_planning": false,
  "risk_level": "low",
  "complexity": "simple",
  "preferred_skill": "calendar",
  "clarification_questions": [],
  "reasoning": "User wants to check calendar events"
}
```

### 3. LLM Adapters (`agent/adapters/`)
Provider-agnostic LLM client with pluggable backends:

| Adapter | Use Case | Auth |
|---------|----------|------|
| OpenRouterAdapter | Primary, cheap inference | API key |
| OpenAIAdapter | High-quality when needed | API key |
| CodexCLIAdapter | Code generation tasks | OAuth |

**Error Handling:**
- Auth errors → try next provider
- Rate limits → exponential backoff
- Transient errors → retry with backoff
- Fatal errors → surface to user

### 4. Tool Registry (`agent/tools/registry.py`)
Schema-validated tool execution with safety.

**Tool Result Envelope:**
```python
@dataclass
class ToolResult:
    ok: bool
    data: Any
    error: Optional[str]
    retryable: bool
    changed_state: bool
```

**Execution Flow:**
1. Validate input against Pydantic schema
2. Check preconditions
3. Execute with timeout
4. Verify postconditions
5. Return standardized result

### 5. Skills System (`agent/skills/`)
First-class API integrations (not UI-driven workarounds).

**Calendar Skill Interface:**
```python
class CalendarSkill:
    def auth_status() -> AuthStatus
    def begin_oauth() -> OAuthFlow
    def list_events(time_range: str) -> List[Event]
    def next_event() -> Optional[Event]
    def create_event(event: EventCreate) -> Event
```

### 6. Memory System (`agent/memory/`)
Persistent memory with semantic retrieval.

**Memory Types:**
- `experience`: Past task executions and outcomes
- `procedure`: Learned procedures and skills
- `knowledge`: Facts and domain knowledge
- `user_info`: User preferences and context

**Retrieval Strategy:**
1. Semantic similarity (embedding-based)
2. Recency weighting
3. Importance scoring
4. Diversity sampling

### 7. Security (`agent/security/`)
Defense-in-depth approach.

**Components:**
- `KillSwitch`: Emergency stop for all execution
- `ApprovalGate`: Human approval for destructive actions
- `Allowlist`: Permitted domains, apps, tools
- `SecretStore`: Secure credential storage (DPAPI)
- `Redactor`: Remove secrets from logs/traces

### 8. Execution Monitor
Robust execution with failure recovery.

**Features:**
- Precondition checks (e.g., file exists before read)
- Postcondition verification (e.g., file was created)
- Timeout enforcement per tool
- Retry with exponential backoff
- Fallback strategies (e.g., vision → UI automation)
- Stuck-loop detection (ThrashGuard)

### 9. Tracing (`agent/tracing/`)
Structured observability for debugging and evals.

**Output Format:** JSONL with:
- Timestamp, run_id, step_number
- Action, input, output
- Duration, memory_used
- Success/failure and error details

## Execution Modes

### Simple Tasks
```
User Input → Orchestrator → Single Tool → Result
```

### Complex Tasks
```
User Input → Orchestrator → Planner → [Tool₁, Tool₂, ...] → Verify → Result
```

### Learning Tasks
```
User Input → Orchestrator → Research → Plan → Execute → Reflect → Store Lesson
```

## Data Flow

```
User Request
    │
    ▼
┌─────────────┐
│ Orchestrator│ ←── Memory (past experiences)
└─────────────┘
    │
    ▼ Strategy JSON
┌─────────────┐
│   Planner   │ ←── LLM (ReAct or Plan-First)
└─────────────┘
    │
    ▼ Action Plan
┌─────────────┐
│   Executor  │ ←── Tools, Skills
└─────────────┘
    │
    ▼ Results
┌─────────────┐
│  Reflector  │ ←── LLM (analyze outcome)
└─────────────┘
    │
    ▼ Lessons
┌─────────────┐
│   Memory    │ ──► Persistence
└─────────────┘
```

## Configuration

### Environment Variables
```bash
# Required
OPENROUTER_API_KEY=sk-or-...

# Optional
OPENAI_API_KEY=sk-...
CODEX_EXE_PATH=/path/to/codex
CODEX_CLI_PATH=/path/to/codex
CODEX_BIN=codex
CODEX_MODEL=gpt-5.1-codex-mini
CODEX_MODEL_FAST=gpt-5.1-codex-mini
CODEX_MODEL_REASON=gpt-5.2-codex
CODEX_REASONING_EFFORT_FAST=low
CODEX_REASONING_EFFORT_REASON=high

# Safety
AGENT_APPROVAL_REQUIRED=true
AGENT_KILL_SWITCH_FILE=/path/to/killswitch
AGENT_ALLOWED_DOMAINS=github.com,google.com
```

### Profiles
- `fast`: Quick execution, minimal verification
- `deep`: Thorough planning, full verification
- `audit`: Maximum logging, no side effects

## File Structure

```
agent/
├── core/
│   ├── unified_agent.py      # Main entry point
│   ├── intelligent_orchestrator.py
│   ├── policy.py             # Execution policies
│   └── state.py              # Agent state
├── adapters/
│   ├── llm_client.py         # Base + factory
│   ├── openrouter.py
│   ├── openai.py
│   └── codex_cli.py
├── tools/
│   ├── registry.py           # Tool registry
│   ├── schemas/              # Pydantic schemas
│   └── implementations/      # Tool implementations
├── skills/
│   ├── base.py               # Skill interface
│   ├── calendar.py           # Google Calendar
│   ├── browser.py            # Browser automation
│   └── filesystem.py         # File operations
├── memory/
│   ├── store.py              # Memory interface
│   ├── sqlite_store.py       # SQLite + embeddings
│   ├── retrieval.py          # Semantic retrieval
│   └── persistence.py        # Disk persistence
├── tracing/
│   ├── tracer.py             # JSONL tracer
│   ├── structured_log.py     # Structured logging
│   └── artifacts.py          # Artifact capture
├── security/
│   ├── kill_switch.py
│   ├── approvals.py
│   ├── allowlists.py
│   ├── secret_store.py
│   └── redactor.py
└── autonomous/               # Legacy (to be migrated)
    ├── runner.py
    ├── planning/
    └── ...

evals/
├── scenarios/                # Test scenarios
├── runner.py                 # Eval runner
└── golden/                   # Expected outputs

docs/
├── ARCHITECTURE.md           # This file
├── THREAT_MODEL.md           # Security analysis
├── TOOLS.md                  # Tool reference
└── SKILLS.md                 # Skill reference
```

## Migration Path

### Phase 1: LLM Adapters
- Create provider-agnostic client
- Add OpenRouter as primary
- Keep Codex CLI as optional

### Phase 2: Unified Agent
- Implement intelligent orchestrator
- Create unified entry point
- Deprecate keyword-based routing

### Phase 3: Tools & Execution
- Add schema validation
- Add pre/postconditions
- Standardize result envelopes

### Phase 4: Skills
- Implement calendar skill
- Add proper OAuth flow
- Store credentials securely

### Phase 5: Memory & Reflection
- Ensure persistence
- Add semantic retrieval
- Implement reflection loop

### Phase 6: Safety
- Add kill switch
- Implement approvals
- Add secret redaction

### Phase 7: Robustness
- Add health checks
- Improve stuck-loop detection
- Add exploration policies

### Phase 8: Evals
- Create scenario suite
- Add CI smoke test
- Document eval process

## Non-Functional Requirements

### Performance
- Tool execution timeout: 30s default, configurable
- LLM call timeout: 60s
- Memory retrieval: <100ms for top-k

### Reliability
- Retry transient failures 3x with backoff
- Checkpoint every 5 steps
- Resume from last checkpoint on restart

### Security
- No secrets in logs
- Approval for destructive actions
- Sandboxed file access
- Domain allowlists

### Observability
- Structured JSONL traces
- Step-by-step logging
- Memory/CPU monitoring
- Error classification

## Appendix: Current State Analysis

### What Works
- ReAct loop execution
- Basic tool execution
- Memory with embeddings
- Checkpoint/resume
- UI automation (hybrid)

### What's Broken/Missing
- LLM auth routing (Codex-dependent)
- Keyword-based mode selection
- Incomplete calendar skill
- No approval gates
- Weak secret handling
- No eval harness
- Architecture bloat (many modes)

### Key Gaps to Address
1. Provider-agnostic LLM client
2. LLM-based orchestration
3. Schema-validated tools
4. First-class calendar skill
5. Persistent memory
6. Reflection + learning
7. Safety controls
8. Eval framework
