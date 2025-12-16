# Active Roadmap - Updated November 12, 2025

**Current Phase:** 2 (Finalizing) → 3 (Integration)  
**Previous Phase 2 Status:** Blackboard extraction 90% complete (Selenium scroll fix applied)

---

## COMPLETED IN PHASE 2

✅ Blackboard login working  
✅ Course extraction working (scroll loop added)  
✅ Module extraction working  
✅ Due date extraction working (scroll loop added)  
✅ Selenium framework stable (no timeout issues)  
✅ AnkiBridge working (cards pushing to Anki)  
✅ FastMCP server running + ngrok tunnel stable  
✅ All 13 tools registered + accessible via HTTP

---

## IMMEDIATE PRIORITIES (NEXT 48 HOURS)

### Priority 1: Extract 5 Course URLs (BLOCKING)
**Owner:** Codex  
**Task:** Create `extract_course_urls.py` script
- Login to Blackboard
- Navigate to Courses page
- Extract outline URL for each of 5 courses
- Save to `COURSE_URLS.txt`

**Blocker:** Anatomy & PT Exam Skills not showing in course list (likely filter)  
**Workaround:** Direct URL extraction bypasses filter issue

**Timeline:** 2 hours (Codex) + 30 min (Trey validation)  
**Gate to Phase 3:** Must have 5 confirmed URLs

---

### Priority 2: Validate All 48 Due Dates
**Owner:** Trey (run test)  
**Task:** Test `get_due_dates()` against hardcoded URLs
- Run extraction against all 5 courses
- Count per course:
  - Legal & Ethics: 14
  - Lifespan Dev: 2
  - Clinical Pathology: 22
  - Anatomy: 6
  - PT Exam Skills: 4
  - Total: 48

**Timeline:** 30 min (test run)  
**Gate to Phase 3:** Must confirm ≥95% of expected counts

---

### Priority 3: Document Phase 2 Completion
**Owner:** Trey  
**Task:** Update files
- [ ] `ACTIVE_ROADMAP.md` → Phase 2 complete
- [ ] `PHASE_CHECKLISTS.md` → Mark Phase 2 tasks done
- [ ] `QUICK_REFERENCE.md` → Current status snapshot

**Timeline:** 15 min

---

## PHASE 3 ROADMAP (NEXT WEEK)

### 3.1: Re-connect MCP to ChatGPT
- Remove old server URL from ChatGPT MCP settings
- Add new ngrok tunnel URL
- Verify all 13 tools appear
- Screenshot tool list

**Timeline:** 30 min  
**Owner:** Trey

---

### 3.2: Test All 13 Tools Individually
- ingest_file → push material to fastmcp-server
- search_materials → query indexed content
- generate_flashcards → create PERRIO-based cards
- create_anki_template → verify template format
- export_to_txt → export materials
- listAnkiDecks → list all decks
- getCardsFromDeck → retrieve cards
- addCardToDeck → push cards to Anki ← KEY TEST
- updateCard → modify card content
- moveCard → move card between decks
- deleteCard → remove card
- mergeDeck → combine two decks
- cleanupDeck → remove duplicates

**Timeline:** 2-3 hours (all tests)  
**Owner:** Trey (run) + Codex (fix if needed)

---

### 3.3: End-to-End Integration Test
**Scenario:** Ask Claude to "Extract Legal & Ethics due dates and create 5 flashcards"

**Expected Flow:**
1. Claude calls blackboard-agent → extract_course_urls
2. Claude calls get_due_dates → pull dates from Legal & Ethics
3. Claude calls ingest_file → load course materials
4. Claude calls generate_flashcards → create 5 cards (PERRIO v6.4)
5. Claude calls addCardToDeck → push to Anki
6. Verify 5 cards appear in Anki within 5 minutes

**Timeline:** 1 hour (test + verification)  
**Owner:** Trey

---

### 3.4: Error Handling & Logging
- Add structured logging to all API calls
- Handle AnkiConnect offline
- Handle Blackboard session timeout
- Add retry logic (exponential backoff)
- Document all error codes

**Timeline:** 4-5 hours  
**Owner:** Codex

---

### 3.5: Documentation
- "How to Run Full Workflow" guide
- Error reference manual
- Tool documentation with examples
- Troubleshooting guide

**Timeline:** 3 hours  
**Owner:** Trey (coordinate)

---

## PHASE 4 ROADMAP (WEEK AFTER NEXT)

### 4.1: Dashboard Backend (Node.js)
- Create API endpoints (status, extraction, Anki, progress)
- Add real-time WebSocket updates
- Implement scheduling (6 AM extractions, 6 PM generation)

**Timeline:** 8-10 hours  
**Owner:** Codex

---

### 4.2: Dashboard Frontend (React)
- System status component
- Extraction status with live updates
- Anki deck visualization
- Study progress metrics

**Timeline:** 6-8 hours  
**Owner:** Codex

---

### 4.3: Notifications
- Slack alerts (extraction failure, low decks)
- Email digest (daily summary)
- Notification preferences UI

**Timeline:** 3-4 hours  
**Owner:** Codex

---

## KEY BLOCKERS & WORKAROUNDS

| Blocker | Status | Workaround | Timeline |
|---------|--------|-----------|----------|
| Anatomy & PT Exam not in course list | 🔄 Active | Extract URLs directly | 2 hours |
| ChatGPT MCP tool cache issue | ⏳ Phase 3 | Re-add server URL | 30 min |
| Blackboard session timeout | ⏳ Phase 3 | Add re-login logic | 1-2 hours |

---

## SUCCESS GATES FOR PHASE ADVANCEMENT

**Phase 2 → 3:**
- ✅ All 5 courses extracted
- ✅ All ~48 due dates confirmed
- ✅ 5 course URLs locked in
- ✅ Zero timeout errors in last 10 runs

**Phase 3 → 4:**
- ✅ All 13 tools tested individually
- ✅ Full workflow succeeds end-to-end
- ✅ Claude can orchestrate entire process
- ✅ Cards appear in Anki within 5 min consistently

**Phase 4 → 5:**
- ✅ Dashboard deployed + real-time updates
- ✅ Scheduled extraction runs automatically
- ✅ System runs 7 days without intervention
- ✅ Notifications working

---

## TEAM ASSIGNMENTS

**Codex (AI Agent):**
- Build extract_course_urls.py
- Implement all backend code
- Debug integration issues
- Write documentation drafts

**Trey (You):**
- Run all tests
- Validate results
- Make go/no-go decisions
- Integrate feedback

---

## TIMELINE SUMMARY

- **This week (by Nov 15):** Phase 2 COMPLETE (URLs extracted, due dates confirmed)
- **Next week (by Nov 22):** Phase 3 COMPLETE (full integration tested)
- **Week after (by Nov 29):** Phase 4 COMPLETE (dashboard deployed)
- **By Dec 13:** Phase 5 COMPLETE (production ready)

---

## RESOURCES & DOCUMENTATION

**Master Documents:**
- `DRCODEPT_MASTER_PLAN.md` — Full architecture
- `PHASE_CHECKLISTS.md` — Detailed task breakdown
- `QUICK_REFERENCE.md` — Commands & status

**Program Locations:**
- fastmcp-server: `PROGRAMS/fastmcp-server/`
- blackboard-agent: `PROGRAMS/blackboard-agent/`
- dashboard-api: `PROGRAMS/dashboard-api/`

**Credentials:**
- `.env` files (keep secret, never commit)
- Blackboard: frtucker / OmmarAnnie1!
- Anki: treytucker05@yahoo.com / Turtle1!

---

## NEXT IMMEDIATE ACTION

**TODAY:**
1. Codex: Run `extract_course_urls.py` → Generate `COURSE_URLS.txt`
2. Trey: Test due-date extraction with URLs → Confirm ~48 total
3. Both: Update documentation, mark Phase 2 complete

**START:** Phase 3 next week

---

**Last Updated:** November 12, 2025  
**Owner:** Trey Tucker  
**Review Cadence:** Weekly (Sundays 6 PM)
