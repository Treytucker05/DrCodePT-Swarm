# Acceptance Tests for Agent Refactoring

These tests validate that the refactored agent works correctly at each stage.

---

## Module 0 - Baseline Tests

### Test 0.1: Agent Menu Launches
```bash
python -m agent.main --menu
```
**Expected**: Menu displays with options 1-9, R, S, 0

### Test 0.2: Self-Check Passes
From menu, select option [9] Self-Check System
**Expected**: All checks show checkmarks (or known failures documented)

### Test 0.3: Git Status Clean
```bash
git status
```
**Expected**: Clean working tree (or only new docs files)

### Test 0.4: Logs Directory Exists
```bash
ls logs/ || mkdir logs/
```
**Expected**: Directory exists and is gitignored

---

## Module 1 - Unified Registry Tests

### Test 1.1: Registry Loads Local Tools
```python
from agent.autonomous.tools.registry import ToolRegistry
reg = ToolRegistry()
tools = [t.name for t in reg.list_tools()]
assert "file_read" in tools or len(tools) > 0
print(f"Loaded {len(tools)} tools")
```

### Test 1.2: Registry Loads MCP Tools (if configured)
```python
from agent.mcp.registry import load_registry
mcp_servers = load_registry()
print(f"Loaded {len(mcp_servers)} MCP servers")
```

### Test 1.3: Tool Execution Works
```python
from agent.autonomous.tools.registry import ToolRegistry
from agent.autonomous.config import RunContext
from pathlib import Path

reg = ToolRegistry()
ctx = RunContext(
    run_id="test",
    run_dir=Path("./test_run"),
    workspace_dir=Path("./test_run"),
    profile=None,
    usage=None,
)

# Test a safe tool
result = reg.call("finish", {"summary": "test complete"}, ctx)
print(f"Result: {result}")
```

---

## Module 2 - Model Router Tests

### Test 2.1: Router Returns Valid Backend
```python
from agent.llm.router import ModelRouter
router = ModelRouter()

# Should route planning to cheap model
backend = router.route_for_task("plan next step")
assert backend in ["openrouter", "local", "default"]

# Should route coding to Codex
backend = router.route_for_task("fix bug in repository")
assert backend in ["codex", "claude", "default"]
```

### Test 2.2: LLM Call Works Through Router
```python
from agent.llm.router import ModelRouter
router = ModelRouter()
llm = router.get_llm_for_task("plan next step")
# Should return a valid LLMClient
assert hasattr(llm, "complete_json")
```

---

## Module 3 - ReAct Loop Tests

### Test 3.1: Single Step Execution
```python
from agent.autonomous.react_loop import react_step

result = react_step(
    task="Create a file named test.txt",
    observations=[],
    memories=[],
)
assert result is not None
assert hasattr(result, "action")
print(f"Action: {result.action}")
```

### Test 3.2: Observation -> Action Flow
```python
from agent.autonomous.react_loop import react_step
from agent.autonomous.models import Observation

obs = Observation(
    source="user",
    raw="file created successfully",
    salient_facts=["file exists"],
)

result = react_step(
    task="Create test.txt and verify it exists",
    observations=[obs],
    memories=[],
)
# Should recognize progress
assert result is not None
```

### Test 3.3: Finish Detection
```python
from agent.autonomous.react_loop import react_step
from agent.autonomous.models import Observation

obs = Observation(
    source="tool",
    raw="task completed",
    salient_facts=["goal achieved"],
)

result = react_step(
    task="Simple task",
    observations=[obs],
    memories=[],
)
# Should output finish action when goal met
# (May need multiple steps - this tests the flow)
```

---

## Module 4 - Codex Tool Tests

### Test 4.1: Codex Tool Registered
```python
from agent.tools.unified_registry import UnifiedRegistry
reg = UnifiedRegistry()
assert reg.has_tool("codex") or reg.has_tool("codex_cli")
```

### Test 4.2: Codex Tool Executes
```python
from agent.tools.codex_tool import CodexTool

tool = CodexTool()
result = tool.execute({"task": "list python files in current directory"})
print(f"Success: {result.success}")
print(f"Output: {result.output}")
```

### Test 4.3: Codex Results Flow to Agent
```python
# Full integration test
from agent.autonomous.runner import AgentRunner
# ... setup runner with codex tool enabled
# result = runner.run("find all TODO comments in the codebase")
# assert "TODO" in str(result) or result.success
```

---

## Module 5 - Cleanup Tests

### Test 5.1: Clean Imports
```bash
python -c "from agent.autonomous.runner import AgentRunner; print('OK')"
python -c "from agent.autonomous.react_loop import react_step; print('OK')"
python -c "from agent.tools.unified_registry import UnifiedRegistry; print('OK')"
```
**Expected**: No import errors

### Test 5.2: No Circular Dependencies
```bash
python -c "
import sys
sys.setrecursionlimit(100)
from agent.autonomous.runner import AgentRunner
print('No circular deps')
"
```

### Test 5.3: Archive Directory Structure
```
archive/
  modes/           # Archived mode system
  supervisor/      # Archived supervisor (if moved)
  playbooks/       # Archived playbook system
```

---

## End-to-End Tests

### E2E Test 1: Simple File Task
```python
from agent.autonomous.runner import AgentRunner
from agent.autonomous.config import RunnerConfig, AgentConfig, PlannerConfig
from agent.llm.router import ModelRouter

runner = AgentRunner(
    cfg=RunnerConfig(max_steps=10),
    agent_cfg=AgentConfig(),
    planner_cfg=PlannerConfig(mode="react"),
    llm=ModelRouter().get_llm_for_task("plan"),
)

result = runner.run("Create a file named hello.txt with 'Hello World' in it")
assert result.success
```

### E2E Test 2: Web Search Task
```python
# Requires web tools configured
result = runner.run("Search the web for 'Python best practices 2024'")
# Should not error, may require human_ask if stuck
```

### E2E Test 3: Code Analysis Task
```python
result = runner.run("Count the number of Python files in the agent/ directory")
assert result.success
# Check logs for actual count
```

---

## Performance Benchmarks

### Benchmark 1: Step Latency
- Target: < 5s per planning step with OpenRouter
- Target: < 30s per Codex tool call

### Benchmark 2: Token Usage
- Track estimated_tokens per run
- Compare before/after refactor

### Benchmark 3: Success Rate
- Track success/failure ratio
- Target: >= current success rate

---

## Regression Checklist

Before each module merge:

- [ ] All Module 0 tests pass
- [ ] All previous module tests pass
- [ ] No new import errors
- [ ] Git diff reviewed
- [ ] Rollback tested (git stash, run old code, git stash pop)
