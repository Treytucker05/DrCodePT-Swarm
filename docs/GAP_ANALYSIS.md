# Gap Analysis: DrCodePT-Swarm

## Executive Summary

This document catalogs all gaps between the current implementation and the target production-grade autonomous agent architecture.

## Gap Categories

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| LLM Integration | 2 | 1 | 0 | 0 |
| Orchestration | 1 | 2 | 1 | 0 |
| Tools | 0 | 2 | 2 | 1 |
| Skills | 1 | 1 | 1 | 0 |
| Memory | 0 | 2 | 1 | 0 |
| Safety | 2 | 2 | 1 | 0 |
| Robustness | 0 | 2 | 2 | 0 |
| Evals | 1 | 1 | 0 | 0 |
| **Total** | **7** | **13** | **8** | **1** |

---

## Critical Gaps

### GAP-001: Codex CLI Authentication Dependency
**Severity:** Critical
**Location:** `agent/llm/codex_cli_client.py`, `agent/llm/router.py`

**Problem:**
The agent fails completely when Codex CLI is not authenticated. There's no graceful fallback.

**Current Behavior:**
```python
# In codex_cli_client.py
result = subprocess.run([self.codex_bin, "chat", ...])
# If not authenticated, raises exception with "not authenticated"
```

**Impact:**
Agent unusable for users without Codex auth.

**Fix:**
Implement provider-agnostic LLM client with OpenRouter as primary fallback.

---

### GAP-002: No OpenRouter Direct HTTP Client
**Severity:** Critical
**Location:** `agent/llm/openrouter_client.py`

**Problem:**
OpenRouterClient exists but isn't properly integrated as a fallback. It's only used when explicitly selected.

**Current Behavior:**
```python
# In router.py - OpenRouter only used for specific task types
if task_type == TaskType.SUMMARIZE:
    return OpenRouterClient()
```

**Impact:**
Cannot fail over to cheap models when Codex unavailable.

**Fix:**
Make OpenRouter the default with Codex as optional enhancement.

---

### GAP-003: Brittle Keyword-Based Routing
**Severity:** Critical
**Location:** `agent/cli.py:_needs_learning_agent()`, `agent/llm/router.py`

**Problem:**
Mode selection uses keyword matching, not LLM understanding.

**Current Behavior:**
```python
def _needs_learning_agent(text: str) -> bool:
    learning_keywords = ["calendar", "outlook", "gmail", ...]
    return any(kw in lower for kw in learning_keywords)
```

**Impact:**
- "schedule a meeting" doesn't route to calendar
- "check my appointments" doesn't route to calendar
- Semantically equivalent requests handled differently

**Fix:**
Implement LLM-based intelligent orchestrator.

---

### GAP-004: Incomplete Calendar Skill
**Severity:** Critical
**Location:** `agent/tools/calendar.py`, `agent/integrations/google_apis.py`

**Problem:**
Calendar integration exists but is incomplete and doesn't handle OAuth properly.

**Current Behavior:**
- OAuth flow requires manual browser intervention
- Tokens stored in plaintext JSON
- No automatic refresh
- Error handling incomplete

**Impact:**
"Check my calendar" fails for most users.

**Fix:**
Implement first-class calendar skill with proper OAuth, token refresh, and error handling.

---

### GAP-005: Secrets in Logs
**Severity:** Critical
**Location:** Various (logs, traces, prompts)

**Problem:**
API keys and tokens can leak into:
- Log files
- JSONL traces
- LLM prompts
- Error messages

**Current Behavior:**
```python
# In various files
logger.info(f"Using API key: {api_key}")  # BAD
print(f"Token: {token}")  # BAD
```

**Impact:**
Security vulnerability - credential exposure.

**Fix:**
Implement SecretStore with DPAPI encryption and log redaction.

---

### GAP-006: No Kill Switch
**Severity:** Critical
**Location:** N/A (not implemented)

**Problem:**
No way to emergency stop the agent mid-execution.

**Impact:**
Runaway agent cannot be stopped without killing process.

**Fix:**
Implement file-based kill switch checked before each action.

---

### GAP-007: No Eval Harness
**Severity:** Critical
**Location:** N/A (not implemented)

**Problem:**
No automated way to test agent capabilities or catch regressions.

**Current State:**
- `test_integration.py` exists but is minimal
- No scenario-based testing
- No golden trace comparison
- No CI integration

**Impact:**
Cannot verify agent works correctly after changes.

**Fix:**
Implement eval framework with 10+ scenarios.

---

## High Priority Gaps

### GAP-008: No Approval Gates
**Severity:** High
**Location:** `agent/supervisor/hardening.py` (incomplete)

**Problem:**
Destructive actions execute without user confirmation.

**Current Behavior:**
- File deletion happens automatically
- Shell commands run without approval
- API calls that modify data execute immediately

**Fix:**
Implement ApprovalGate for destructive actions.

---

### GAP-009: Missing Pre/Postconditions
**Severity:** High
**Location:** `agent/tools/` (partial in `agent/autonomous/hybrid_executor.py`)

**Problem:**
Tools execute without verifying preconditions or validating results.

**Current Behavior:**
```python
# Just execute and hope
result = tool.execute(args)
return result
```

**Partial Implementation:**
`hybrid_executor.py` now has `_check_precondition()` and `_verify_postcondition()` but only for UI actions.

**Fix:**
Add pre/postconditions to all tools.

---

### GAP-010: Tool Schema Validation Incomplete
**Severity:** High
**Location:** `agent/tools/registry.py`, `agent/autonomous/tools/builtins.py`

**Problem:**
Tool inputs aren't consistently validated against schemas.

**Current Behavior:**
- Some tools have Pydantic args classes
- Others accept raw dicts
- Validation happens inconsistently

**Fix:**
Enforce Pydantic validation for all tool inputs.

---

### GAP-011: Memory Persistence Issues
**Severity:** High
**Location:** `agent/memory/memory_manager.py`, `agent/autonomous/memory/sqlite_store.py`

**Problem:**
Memory doesn't reliably persist or is lost between runs.

**Issues:**
- Multiple memory systems (JSON file vs SQLite)
- Embeddings may not persist
- No migration between formats

**Fix:**
Consolidate to single SQLite store with guaranteed persistence.

---

### GAP-012: Reflection Not Stored
**Severity:** High
**Location:** `agent/autonomous/reflection.py`, `agent/autonomous/memory/reflexion.py`

**Problem:**
Reflection happens but lessons aren't stored for future use.

**Current Behavior:**
```python
# Reflection generates output but doesn't persist
reflection = reflector.reflect(...)
# reflection.lesson exists but isn't saved to memory
```

**Fix:**
Store reflection lessons in memory for retrieval.

---

### GAP-013: Domain Allowlists Not Enforced
**Severity:** High
**Location:** `agent/security/` (partial)

**Problem:**
No allowlist enforcement for browser navigation or API calls.

**Impact:**
Agent could navigate to malicious sites or call unauthorized APIs.

**Fix:**
Implement and enforce domain/URL allowlists.

---

### GAP-014: Tool Allowlists Not Enforced
**Severity:** High
**Location:** `agent/autonomous/tools/registry.py`

**Problem:**
Tool registry has allowlist concept but not consistently enforced.

**Current Behavior:**
```python
# In registry.py
if tool.name not in self.allowed_tools:
    # Log warning but may still execute
```

**Fix:**
Block execution of non-allowed tools.

---

### GAP-015: Stuck Loop Detection Partial
**Severity:** High
**Location:** `agent/autonomous/guards.py`, `agent/autonomous/hybrid_executor.py`

**Problem:**
ThrashGuard exists but integration is incomplete.

**Current State:**
- `guards.py` has ThrashGuard
- `hybrid_executor.py` now integrates it (recent fix)
- `runner.py` has separate loop detection
- Not unified

**Fix:**
Ensure ThrashGuard is used consistently in all execution paths.

---

### GAP-016: No Health Checks for UI Automation
**Severity:** High
**Location:** `agent/autonomous/windows_ui.py`, `agent/autonomous/vision_executor.py`

**Problem:**
Agent doesn't check if UI automation dependencies are available before starting.

**Impact:**
Confusing failures when pyautogui or uiautomation not installed.

**Fix:**
Add startup health checks, declare capabilities.

---

### GAP-017: UI Automation Fallback Chain Incomplete
**Severity:** High
**Location:** `agent/autonomous/hybrid_executor.py`

**Problem:**
Vision fallback exists but popup/modal handling is incomplete.

**Issues:**
- No systematic popup detection
- No modal dismissal
- Exploration policy is basic (scroll only)

**Fix:**
Improve exploration policy with popup handling.

---

### GAP-018: Missing Eval Scenarios
**Severity:** High
**Location:** N/A

**Problem:**
No scenario-based tests exist.

**Needed Scenarios:**
1. Check calendar (authenticated)
2. Check calendar (need OAuth)
3. Create file and verify
4. Web search and summarize
5. Multi-step task with plan
6. Error recovery
7. Stuck loop recovery
8. Kill switch test
9. Approval gate test
10. Memory retrieval test

**Fix:**
Create eval framework with these scenarios.

---

## Medium Priority Gaps

### GAP-019: Multiple Entry Points
**Severity:** Medium
**Location:** `agent/cli.py`, `agent/__main__.py`, `agent/treys_agent.py`, `agent/unified_cli.py`

**Problem:**
Multiple CLI entry points cause confusion.

**Fix:**
Consolidate to single entry point with subcommands.

---

### GAP-020: Inconsistent Error Handling
**Severity:** Medium
**Location:** Various

**Problem:**
Error handling is inconsistent:
- Some functions return (success, error)
- Others raise exceptions
- Others return None
- Error types not standardized

**Fix:**
Standardize on Result pattern or exceptions.

---

### GAP-021: Legacy Mode Code
**Severity:** Medium
**Location:** `agent/modes/`, `agent/_legacy/`

**Problem:**
Multiple execution modes add complexity without clear benefit.

**Modes:**
- autonomous, swarm, collaborative, execute, learn, research, mail_supervised, mail_collab, mail_intelligent, maintenance, grade, resume

**Fix:**
Consolidate to unified agent with capabilities, not modes.

---

### GAP-022: Timeout Handling Inconsistent
**Severity:** Medium
**Location:** Various

**Problem:**
Timeouts are handled inconsistently:
- Some tools have hardcoded timeouts
- Others respect config
- Some have no timeout

**Fix:**
Implement consistent timeout handling via ExecutionMonitor.

---

### GAP-023: Semantic Retrieval Not Used
**Severity:** Medium
**Location:** `agent/autonomous/memory/sqlite_store.py`

**Problem:**
Embedding-based retrieval exists but isn't consistently used.

**Current Behavior:**
- Store has `search()` method
- Not always called before planning
- Relevance not weighted properly

**Fix:**
Integrate memory retrieval into planning prompts.

---

### GAP-024: Checkpoint Resume Fragile
**Severity:** Medium
**Location:** `agent/autonomous/checkpointing.py`

**Problem:**
Checkpoint/resume exists but is fragile.

**Issues:**
- State may be incomplete
- Tools may have changed
- Context may be stale

**Fix:**
Add validation on resume, warn about stale state.

---

### GAP-025: Log Redaction Incomplete
**Severity:** Medium
**Location:** `agent/agent_logging/redaction.py`

**Problem:**
Redaction exists but isn't applied everywhere.

**Fix:**
Apply redaction to all log outputs.

---

### GAP-026: Tool Result Envelope Not Standardized
**Severity:** Medium
**Location:** `agent/tools/types.py`, `agent/tools/base.py`

**Problem:**
Tool results have different shapes:
- Some return ToolResult
- Others return (bool, str)
- Others return dicts

**Fix:**
Standardize on ToolResult envelope everywhere.

---

## Low Priority Gaps

### GAP-027: Documentation Sparse
**Severity:** Low
**Location:** `docs/`

**Problem:**
Limited documentation for:
- Tool development
- Skill development
- Memory system
- Security model

**Fix:**
Add TOOLS.md, SKILLS.md, THREAT_MODEL.md.

---

## Implementation Priority

### Phase 1 (Critical - Do First)
1. GAP-001: LLM Client refactor
2. GAP-002: OpenRouter integration
3. GAP-003: Intelligent orchestrator

### Phase 2 (Critical - Enable Core Features)
4. GAP-004: Calendar skill
5. GAP-005: Secret handling
6. GAP-006: Kill switch

### Phase 3 (High - Tools & Execution)
7. GAP-009: Pre/postconditions
8. GAP-010: Schema validation
9. GAP-008: Approval gates

### Phase 4 (High - Memory & Learning)
10. GAP-011: Memory persistence
11. GAP-012: Reflection storage
12. GAP-023: Semantic retrieval

### Phase 5 (High - Safety)
13. GAP-013: Domain allowlists
14. GAP-014: Tool allowlists
15. GAP-025: Log redaction

### Phase 6 (High - Robustness)
16. GAP-015: ThrashGuard unification
17. GAP-016: Health checks
18. GAP-017: Exploration policy

### Phase 7 (Critical - Verification)
19. GAP-007: Eval harness
20. GAP-018: Eval scenarios

### Phase 8 (Medium - Cleanup)
21. GAP-019: Entry point consolidation
22. GAP-020: Error handling
23. GAP-021: Legacy mode removal
24. GAP-026: Tool result standardization

---

## Acceptance Criteria Mapping

| Criteria | Gaps to Resolve |
|----------|-----------------|
| "Check my calendar" works | GAP-001, GAP-002, GAP-003, GAP-004, GAP-005 |
| OpenRouter fallback | GAP-001, GAP-002 |
| Unified agent entry | GAP-003, GAP-019, GAP-021 |
| Schema-validated tools | GAP-009, GAP-010, GAP-026 |
| Persistent memory | GAP-011 |
| Reflection stores lessons | GAP-012 |
| Evals run | GAP-007, GAP-018 |
| Secrets not logged | GAP-005, GAP-025 |
| Approvals for destructive | GAP-008 |
| Kill switch works | GAP-006 |
