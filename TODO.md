# DrCodePT-Swarm TODO List

## High Priority

### 1. Implement Smart Orchestrator Router
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

## Medium Priority

### 4. Phase 2: Self-Monitoring Execution
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
