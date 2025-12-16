# ðŸŽ¯ EXECUTION_PLAN.md

**Last Updated:** November 13, 2025  
**Phase:** 3 - Tool Use API Integration  
**Timeline:** This week (Nov 13-19)

---

## ðŸ”´ IMMEDIATE ACTIONS (DO TODAY)

### 1. Choose Architecture (DECISION POINT)

| Option | Description | Complexity | Best For |
|--------|-------------|-----------|----------|
| **A** | Claude full Tool Use orchestration | HIGH | Complete automation â­ |
| **B** | Guided workflows + coordination | MEDIUM | Balanced control |
| **C** | Hybrid with user preferences | HIGH | Learning system |
| **D** | Progressive refinement | MEDIUM | Iterative approach |

**Recommendation:** Start with **Option A** (full Tool Use orchestration)

---

### 2. Build Tool Use Wrapper

**Location:** `PROGRAMS/tool-use-wrapper/` (NEW)

**Components:**
- `tool_definitions.json` - Tool schemas
- `handler_router.py` - Route Claude calls to FastMCP
- `error_handler.py` - Error handling
- `logger.py` - Logging

**Time:** 2-3 hours

---

### 3. Build CLI Interface

**Location:** `Codex\ Tasks/drcodept-cli\.py`

**Commands:**
```bash
python drcodept-cli.py extract --course LEGAL001
python drcodept-cli.py generate-cards --all-due-soon
python drcodept-cli.py status
python drcodept-cli.py sync-anki
```

**Time:** 3-4 hours


---

## ðŸŸ¡ THIS WEEK (Nov 13-19)

### Phase 3.1: Tool Use API Implementation

**Milestone 1: Tool Definitions Ready**
- [ ] Document all 10+ handlers as Tool Use compatible
- [ ] Create tool_definitions.json
- [ ] Define input/output schemas for each tool

**Milestone 2: Router Working**
- [ ] Create handler_router.py
- [ ] Test routing from Claude â†’ FastMCP â†’ actual handlers
- [ ] Implement error handling with retry logic

**Milestone 3: CLI Interface Ready**
- [ ] Build drcodept-cli.py with 5+ commands
- [ ] Test each command end-to-end
- [ ] Integrate with Anki auto-add feature

---

### Phase 3.2: End-to-End Testing

**Test Scenario 1: Extract & Generate**
```
User: "Extract this week's due dates and generate cards"
Claude: [uses extract tool] â†’ [uses generate_cards tool]
Result: New Anki deck ready
```

**Test Scenario 2: Multi-Course Workflow**
```
User: "Prepare all pathology assignments due next week"
Claude: [extracts pathology] â†’ [retrieves materials] â†’ [generates deck]
Result: Focused study deck
```

---

## ðŸŸ¢ NEXT WEEK (Nov 20-26)

### Phase 3.3: Refinement & Optimization

- [ ] Dashboard fully integrated
- [ ] Performance benchmarks documented
- [ ] User guide completed

### Phase 3.4: Production Ready

- [ ] AutoGen features (auto-schedule, auto-review)
- [ ] Cloud sync ready
- [ ] Full documentation complete

---

## âœ¨ Success Criteria for Phase 3

By end of Phase 3, you can:

1. âœ… Say to Claude: "Extract this week's assignments"
2. âœ… Claude automatically uses Blackboard extraction tool
3. âœ… Claude generates appropriate study cards
4. âœ… Cards appear in Anki automatically
5. âœ… Dashboard shows progress and status
6. âœ… System handles errors gracefully

---

## ðŸ”— Files to Create/Modify

| File | Status | Priority |
|------|--------|----------|
| `PROGRAMS/tool-use-wrapper/` | NEW | ðŸ”´ HIGH |
| `Codex\ Tasks/drcodept-cli\.py` | UPDATE | ðŸ”´ HIGH |
| `MASTER_PLAN.md` | UPDATE | ðŸŸ¡ MED |
| Dashboard `api-server.js` | COMPLETE | ðŸŸ¡ MED |

---

**Next Step:** Choose architecture (A/B/C/D) and confirm

