# Agent Rebuild Plan - ReAct + Reflexion + Memory Architecture

**Status:** Historical/Archive. Do not update as a source of truth. See `AGENT_BEHAVIOR.md` and `conductor/tracks.md`.



Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
## Why Rebuild?
- Current playbook system is too rigid (can't adapt to new situations)
- Chat mode gets stuck in planning without executing
- Swarm mode broken (tool-use conflicts with "DO NOT execute" wrapper)
- Agent can't learn from failures or adapt when things go wrong
- Weeks of work, nothing reliably working

## Target Architecture (Based on 2023-2025 Research)

### Core Loop (ReAct + Reflexion):
1. PERCEPTION: User request + web search for solution approaches
2. PLANNING: Create dynamic plan (DAG of steps, not pre-written playbook)
3. ACTION: Execute using autonomously chosen tools
4. OBSERVATION: Capture results
5. REFLECTION: Analyze what worked/failed, why
6. MEMORY: Store learnings for future tasks
7. REPLAN: If failed, adjust approach and retry

### Key Components:
- **ReAct Loop**: Interleave reasoning with actions (arxiv.org/abs/2210.03629)
- **Reflexion**: Self-correction through analyzing failures (arxiv.org/abs/2303.11366)
- **Dual Memory**: Short-term scratchpad + long-term retrieval store
- **Dynamic Tool Selection**: Agent chooses tools based on situation
- **No Playbooks**: Agent web searches solutions and adapts

## What We're Keeping:
- ✅ Existing tools (Desktop Commander, web_search, Google APIs, etc.)
- ✅ Memory infrastructure (SQLite, embeddings)
- ✅ Codex CLI integration
- ✅ Credential storage
- ✅ Issue tracking

## What We're Changing:
- ❌ Remove playbook dependency for core tasks
- ❌ Remove "DO NOT execute" wrapper from execution modes
- ❌ Remove rigid mode routing (chat/playbook/swarm separation)
- ✅ Add reflection loop after each action
- ✅ Add learning from failures
- ✅ Add dynamic plan generation

## Implementation Phases:

### Phase 1: Core ReAct Loop (1-2 days)
Goal: Get ONE task working end-to-end with reflection

Steps:
1. Create new `agent/autonomous/react_loop.py`
2. Implement: perception → plan → act → observe → reflect
3. Test with simple task: "Set up Google Calendar OAuth"
4. Agent should:
   - Search web for solution
   - Create plan dynamically
   - Choose tools (Desktop Commander vs browser)
   - Execute and observe results
   - Reflect on failures
   - Retry with different approach if needed

Success criteria: ONE task completes autonomously with self-correction

### Phase 2: Memory Integration (2-3 days)
Goal: Agent learns from experience

Steps:
1. Store successful action sequences in memory
2. Store failure patterns and solutions
3. Retrieve similar past experiences before planning
4. Use past learnings to improve future attempts

Success criteria: Agent gets faster/smarter on repeated task types

### Phase 3: Scale & Polish (1 week)
Goal: Handle diverse tasks reliably

Steps:
1. Test on multiple task types (calendar, email, code, research)
2. Refine reflection prompts based on observed failure modes
3. Add confidence scoring to plans
4. Implement graceful degradation

Success criteria: Agent handles 80% of reasonable requests autonomously

## Timeline:
- Start: December 28, 2025
- Phase 1 target: December 30, 2025
- Phase 2 target: January 2, 2026
- Phase 3 target: January 9, 2026

## Success Metrics:
- Agent completes tasks without human intervention (except 2FA/passwords)
- Agent learns from failures and doesn't repeat mistakes
- Agent adapts approach when initial plan fails
- 80% task success rate within 3 attempts

## Rollback Plan:
If rebuild fails, current codebase preserved in:
- Git commit before rebuild starts
- All current files remain (just add new ones)
- Can revert by removing new react_loop.py and restoring old routing

## Notes:
- Keep existing playbooks as optional shortcuts (not requirements)
- Maintain backward compatibility where possible
- Document learnings as we go
