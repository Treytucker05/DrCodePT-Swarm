# Phase Checklists & Task Breakdown
**Last Updated:** November 12, 2025

---

## PHASE 2: Data Extraction (NOW - This Week)

### Task 2.1: Finalize Blackboard Course Extraction ✅ ~90%
- [x] Add Selenium scroll loop to `get_courses()`
- [x] Add Selenium scroll loop to `get_due_dates()`
- [ ] Run `extract_course_urls.py` (Codex task - IN PROGRESS)
- [ ] Hardcode 5 course URLs in handler or config
- [ ] Test course extraction → Confirm all 5 courses surface
- [ ] Document the 5 course URLs in `COURSE_URLS.txt`

**Blocker:** Anatomy & PT Exam Skills not showing (filter issue)  
**Solution:** Extract URLs directly, bypass filter

**Owner:** Codex (extract_course_urls.py) + Trey (test)

---

### Task 2.2: Extract All Due Dates
- [ ] Test `get_due_dates()` against all 5 courses with scroll fix
- [ ] Count total due dates per course:
  - Legal & Ethics: target 14
  - Lifespan Dev: target 2
  - Clinical Pathology: target 22
  - Anatomy: target 6
  - PT Exam Skills: target 4
- [ ] Total target: 48 due dates
- [ ] Document results in `TEST_RESULTS_DUE_DATES.txt`
- [ ] Fix any timeout/extraction errors

**Owner:** Trey (run test) + Codex (debug if needed)

---

### Task 2.3: File Downloads (Low Priority - Phase 4)
- [ ] Implement `download_file()` in blackboard_handler.py
- [ ] Test file download from 1 course
- [ ] Document file storage location
- [ ] Add to future roadmap

**Owner:** Codex (implement later)

---

## PHASE 3: Integration & Orchestration (Next Week)

### Task 3.1: MCP Server → Claude Connection
- [ ] Verify fastmcp-server is running and accessible via ngrok
- [ ] Re-add fastmcp-server URL to ChatGPT MCP settings (cache-bust)
- [ ] Confirm all 13 tools appear in ChatGPT tool list
- [ ] Log each tool name + description

**Owner:** Trey (ChatGPT setup) + Codex (verify tools)

---

### Task 3.2: Test Each Tool Individually
- [ ] Test ingest_file: Upload course material, verify stored
- [ ] Test search_materials: Search for term, get results
- [ ] Test generate_flashcards: Create 3 cards from sample text
- [ ] Test addCardToDeck: Push cards to Anki, verify in app
- [ ] Test listAnkiDecks: List all decks, confirm "DrCodePT" exists
- [ ] Test getCardsFromDeck: Retrieve cards from deck
- [ ] Document results + screenshots

**Owner:** Trey (test) + Codex (fix if errors)

---

### Task 3.3: End-to-End Workflow Test
**Scenario:** Ask Claude: "Extract Legal & Ethics due dates and create 5 flashcards"

Steps:
- [ ] Claude calls blackboard-agent → extract due dates from Legal & Ethics
- [ ] Claude calls ingest_file → load course materials
- [ ] Claude calls generate_flashcards → create cards (PERRIO v6.4)
- [ ] Claude calls addCardToDeck → push to Anki
- [ ] Verify cards appear in Anki within 5 minutes
- [ ] Check logs for full request/response chain
- [ ] Document any errors

**Owner:** Trey (run test) + Codex (debug)

---

### Task 3.4: Error Handling & Logging
- [ ] Add logging to all API calls (request, response, timing)
- [ ] Handle AnkiConnect offline (retry logic)
- [ ] Handle Blackboard 403 (expired session)
- [ ] Handle network timeout (exponential backoff)
- [ ] Document all error codes + recovery steps

**Owner:** Codex (implement) + Trey (test scenarios)

---

### Task 3.5: Documentation
- [ ] Write "How to Run Full Workflow" guide
- [ ] Create error reference manual
- [ ] Document all 13 tools + examples
- [ ] Create troubleshooting guide

**Owner:** Trey (coordinate) + Codex (draft)

---

## PHASE 4: Dashboard & Monitoring (Week After Next)

### Task 4.1: Backend API (Node.js)
- [ ] Create endpoints:
  - GET /api/status → Blackboard + Anki + MCP status
  - GET /api/extraction/latest → Last extraction metadata
  - GET /api/anki/decks → List all decks + card counts
  - GET /api/progress → Study progress metrics
  - POST /api/extraction/trigger → Start extraction now
- [ ] Add error handling + logging
- [ ] Document API spec

**Owner:** Codex

---

### Task 4.2: Frontend Dashboard (React)
- [ ] Build components:
  - SystemStatus (MCP, Blackboard, Anki)
  - ExtractionStatus (courses, due dates, last run)
  - AnkiStatus (decks, card counts, sync time)
  - StudyProgress (cards today, due items, schedule)
- [ ] Add real-time updates (WebSocket or polling)
- [ ] Add refresh buttons

**Owner:** Codex

---

### Task 4.3: Notifications
- [ ] Implement Slack notifications (extraction failure, low decks)
- [ ] Implement email notifications (daily digest)
- [ ] Add notification preferences UI

**Owner:** Codex (implement) + Trey (test)

---

### Task 4.4: Scheduling
- [ ] Add cron job: Extract due dates every morning at 6 AM
- [ ] Add cron job: Generate flashcards every evening at 6 PM
- [ ] Test scheduling; verify runs on time

**Owner:** Codex

---

## PHASE 5: Production Ready (3+ Weeks)

### Task 5.1: Reliability
- [ ] Add retry logic to all Selenium operations
- [ ] Add retry logic to all Anki operations
- [ ] Implement circuit breaker pattern (fail gracefully)
- [ ] Test 7-day continuous run without manual intervention

**Owner:** Codex + Trey

---

### Task 5.2: Database
- [ ] Migrate extracted materials from JSON to PostgreSQL
- [ ] Add indexing for search performance
- [ ] Add backup strategy

**Owner:** Codex

---

### Task 5.3: CI/CD
- [ ] Set up GitHub Actions workflow
- [ ] Auto-run extraction tests daily
- [ ] Auto-run integration tests weekly
- [ ] Slack alerts on test failure

**Owner:** Codex

---

### Task 5.4: Deployment
- [ ] Package as Docker container
- [ ] Write deployment guide
- [ ] Test on fresh machine (not your dev laptop)
- [ ] Optional: Deploy to AWS Lambda (serverless extraction)

**Owner:** Codex + Trey (testing)

---

## DAILY STANDUP QUESTIONS

Each day, answer these 3 questions:

1. **What did we complete?**
   - One completed task = one line answer

2. **What's blocking us?**
   - Specific error, missing info, unclear requirement

3. **What's next?**
   - Top priority task for tomorrow

---

## SUCCESS CRITERIA BY PHASE

**Phase 2 → Phase 3 Gate:**
- ✅ All 5 courses extracting reliably
- ✅ All ~48 due dates present (breakdown verified)
- ✅ Zero timeout errors in last 10 test runs
- ✅ 5 course URLs documented

**Phase 3 → Phase 4 Gate:**
- ✅ Claude can execute full workflow (extract → generate → push) end-to-end
- ✅ Cards appear in Anki within 5 minutes consistently
- ✅ All 13 tools tested individually
- ✅ Error handling implemented for top 5 failure scenarios

**Phase 4 → Phase 5 Gate:**
- ✅ Dashboard deployed and showing real-time status
- ✅ Notifications working (Slack + email)
- ✅ System runs 7 days without intervention
- ✅ One scheduled extraction completes successfully

**Phase 5 → Production Gate:**
- ✅ 99.5% uptime (measured over 30 days)
- ✅ All errors logged + recoverable
- ✅ Docker container builds and runs on fresh machine
- ✅ You can hand off to automation (zero manual involvement)

---

**Last Update:** November 12, 2025  
**Next Review:** After Phase 2 completion
