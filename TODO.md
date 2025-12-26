# DrCodePT-Swarm TODO List

## High Priority - STRATEGIC THINKING PARTNER FOCUS 🎯

### 1. Fix Collaborative Over-Questioning **⚡ DO THIS NOW**
**Status:** Audit complete, ready to implement  
**Added:** 2025-12-26  
**Time:** 30 minutes  
**Description:** Implement 4 fixes from Codex audit to stop unnecessary questions

**Issues identified:**
1. Question prompt forces 2-3 questions even when request is clear
2. ready_to_plan flag is ignored
3. Fallback questions trigger for clear requests
4. Swarm routing too broad (triggers on "research")

**Implementation:**
- Apply all 4 fixes from audit report
- Test with: "Search for Google OAuth docs and extract steps"
- Should execute immediately without questions

**Why First:** Blocks all other collaborative work until fixed

---

### 2. Build Multi-Agent Strategic Thinking System **CORE GOAL**
**Status:** New architecture needed  
**Added:** 2025-12-26  
**Description:** Transform agent from task executor to strategic thinking partner

**Core capabilities needed:**
- **Socratic Questioning Mode:** Helps clarify fuzzy goals through probing questions
- **Multi-Agent Research:** Spawns specialist agents (Research/Analysis/Critic/Synthesis)
- **Assumption Challenge Mode:** Detects contradictions, gaps in logic, unrealistic plans
- **Gap Analysis:** Identifies missing pieces in your systems/thinking
- **Synthesis Mode:** Combines findings into actionable recommendations

**Example workflow:**
```
You: "I want to improve my study system"
Agent: Socratic mode → "What outcome are you optimizing for?"
You: "Long-term retention"
Agent: Gap analysis → "Your SOP focuses on encoding. Where's retrieval practice?"
Agent: Research mode → Spawns 3 agents to find retrieval methods
Agent: Synthesis → "Here are 5 approaches. I recommend spaced repetition because..."
Agent: Challenge mode → "You said you'd study 2hr/day. Where does that time come from?"
```

**Phases:**
- Phase 1: Socratic questioning workflow
- Phase 2: Multi-agent research spawning
- Phase 3: Critical analysis/assumption detector
- Phase 4: Systems mapping and gap analysis

---

### 3. OpenRouter Uncensored API Integration
**Status:** New  
**Added:** 2025-12-26  
**Time:** 2-3 hours  
**Description:** Add fallback to uncensored model when primary LLM refuses

**Use cases:**
- Medical questions triggering safety filters
- Security/hacking research for legitimate purposes
- Edge case queries that get blocked

**Implementation:**
- Add OpenRouter client to agent/llm/
- Try primary model first (OpenAI/Anthropic)
- Auto-fallback to venice/uncensored:free on refusal
- Add OPENROUTER_API_KEY to .env

**Priority:** After collaborative fixes working

---

### 4. Implement Smart Orchestrator Router
**Status:** Ready to implement  
**Description:** Replace manual mode selection with intelligent auto-routing
- Add `smart_orchestrator()` function to `agent/treys_agent.py`
- Remove "Reply with execute/team/auto/swarm" confirmation prompts
- Auto-route based on task complexity
- Preserve swarm capability for complex analysis tasks

**Expected Outcomes:**
- Simple queries execute immediately
- Ambiguous tasks trigger collaborative planning
- Complex analysis auto-suggests swarm mode
- Smooth autonomous operation

---

### 2. Integrate OpenRouter Uncensored Model
**Status:** New  
**Added:** 2025-12-26  
**Description:** Add uncensored AI model for queries that other models refuse
- Set up OpenRouter API integration
- Add model selection logic (censored vs uncensored)
- Create fallback system (try primary model, fallback to uncensored if refused)
- Add configuration for OpenRouter API key
- Test with edge case queries

**Use Cases:**
- Medical questions that trigger safety filters
- Legal/ethical gray area queries
- Technical questions about security/hacking for legitimate purposes
- Creative writing with mature themes

**Files to modify:**
- `agent/llm/` (add OpenRouter client)
- `.env` (add OPENROUTER_API_KEY)
- `agent/treys_agent.py` (add model selection logic)

---

### 3. Documentation and File Structure Cleanup
**Status:** New  
**Added:** 2025-12-26  
**Description:** Update all README files and organize file structure

**Tasks:**
- [ ] Consolidate redundant README files (README.md, README_NEW_FEATURES.md, START_HERE.md)
- [ ] Update main README.md with current features and architecture
- [ ] Clean up CONTINUITY files (merge CONTINUITY.md and CONTINUITY-PowerHouseATX.md?)
- [ ] Organize documentation by category:
  - Setup guides → `docs/setup/`
  - Architecture docs → `docs/architecture/`
  - Usage examples → `docs/usage/`
  - Troubleshooting → `docs/troubleshooting/`
- [ ] Delete outdated/duplicate files
- [ ] Update file structure documentation
- [ ] Create clear hierarchy and navigation

**Current Issues:**
- Too many top-level files (14 markdown files in root)
- Unclear which file to start with
- Overlapping content across files
- No clear navigation structure

---

## Medium Priority - Automation & Productivity

### 5. Google Calendar + Tasks + Memory MCP Integration
**Status:** Designed, not yet critical  
**Added:** 2025-12-26  
**Description:** Productivity automation for PT school + gym management
- Google Calendar MCP - schedule management
- Google Tasks MCP - task tracking
- Memory MCP - persistent context

**Why Deprioritized:** 
- Strategic thinking system more valuable
- Calendar/tasks are nice-to-have, not core mission
- Can add later once thinking partner works

**Keep in backlog for:**
- Study schedule automation (integrate with Study SOP)
- Client workout tracking for gym
- PT assignment deadline tracking

**Implementation Plan:**
- See `PHASE1_CALENDAR_TASKS_MEMORY.md` when ready

---

### 6. Expand MCP Tool Coverage
**Status:** Planned  
**Description:** Add pause-on-uncertainty during execution
- Monitor confidence scores during MCP tool execution
- Pause and ask user when confidence drops below threshold
- Learn from user corrections

---

### 5. Improve Collaborative Planning Prompts
**Status:** In progress  
**Recent fixes:**
- ✅ Removed CONTINUITY.md questions
- ✅ Added filesystem tool guidance
- ✅ Reduced unnecessary plan steps

**Remaining:**
- Fine-tune question quality
- Improve confidence scoring
- Better plan step descriptions

---

### 6. Expand MCP Tool Coverage
**Status:** Partial  
**Completed:**
- ✅ Filesystem MCP (list, read, move, create)
- ✅ Obsidian notes
- ✅ Playwright browser automation
- ✅ Desktop wrapper

**Remaining:**
- [ ] Google Drive integration (read/write/organize)
- [ ] Gmail integration (read/send/organize)
- [ ] Calendar integration (read/create events)
- [ ] Slack/Discord integration

---

## Low Priority

### 7. Blackboard Integration
**Status:** On hold  
**Description:** Connect to UTMB Blackboard for automated assignment tracking
- Phase 3: Extract due dates (COMPLETED ✅)
- Phase 4: Auto-generate study materials
- Phase 5: Sync with Anki

---

### 8. Anki Integration Enhancement
**Status:** Partial  
**Description:** Improve automated flashcard generation
- Better card quality scoring
- Spaced repetition optimization
- Multi-deck support

---

### 9. Error Recovery and Learning
**Status:** Planned  
**Description:** Agent learns from failures
- Track common errors
- Build error recovery playbooks
- Self-improvement feedback loop

---

## Completed ✅

### Smart Playbook Matching
- ✅ Fixed false matches (generic words no longer trigger wrong playbooks)
- ✅ Domain-specific token requirements
- ✅ Proper scoring thresholds

### Auto-Execute Simple Queries
- ✅ Read-only filesystem queries execute without confirmation
- ✅ Safety preserved for destructive operations

### MCP Filesystem Integration
- ✅ Fixed path resolution issues
- ✅ Working list/read/move operations
- ✅ Shortcut resolution

### Collaborative Planning Mode
- ✅ Ask questions before execution
- ✅ Direct MCP tool execution (fast path)
- ✅ Fallback to execute mode when needed

---

## Notes

**Architecture Decision Log:**
- 2025-12-26: Chose hybrid architecture (single orchestrator + dynamic multi-agent spawning)
- Reasoning: Best balance of autonomous operation, collaborative planning, and swarm capabilities

**Current Priorities:**
1. Smart orchestrator (remove friction)
2. OpenRouter integration (expand capabilities)
3. Documentation cleanup (improve onboarding)
