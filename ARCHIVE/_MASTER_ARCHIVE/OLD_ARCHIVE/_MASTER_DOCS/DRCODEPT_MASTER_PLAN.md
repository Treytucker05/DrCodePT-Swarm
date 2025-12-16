# DrCodePT-Swarm: Master Plan & Architecture
**Last Updated:** November 12, 2025  
**Current Phase:** 2 (Finalizing) → 3 (Integration)  
**Owner:** Trey Tucker (PowerHouseATX)

---

## PROJECT VISION

**Mission:** Automate the entire PT school study workflow. Extract course materials from Blackboard → Generate study flashcards using PERRIO protocol → Push to Anki → Track progress via Agent dashboard.

**End State:** Claude acts as your AI study assistant. You ask Claude: "Create flashcards for Anatomy exam next week." Claude:
1. Extracts materials from Blackboard
2. Generates cards following PERRIO v6.4 protocol
3. Pushes to Anki
4. Reports progress via dashboard

**Key Constraint:** You're running DPT courses + gym business + overnight security + two kids. System must be hands-off once started.

---

## CURRENT ARCHITECTURE (2 Core Programs + 1 Dashboard)

### Program 1: fastmcp-server (Study Orchestrator) ✅
**Status:** Working  
**Location:** `PROGRAMS/fastmcp-server/`

**What it does:**
- Runs MCP (Model Context Protocol) server on localhost:8000
- Exposes via ngrok tunnel for Claude/ChatGPT access
- Hosts 13 tools Claude can call

**Tools (13 total):**
- **Study tools (5):** ingest_file, search_materials, export_to_txt, create_anki_template, generate_flashcards
- **Deck tools (8):** listAnkiDecks, getCardsFromDeck, addCardToDeck, updateCard, moveCard, deleteCard, mergeDeck, cleanupDeck

**Internals:**
- Uses AnkiBridge to communicate with local Anki (127.0.0.1:8765)
- Implements PERRIO Protocol v6.4 in generate_flashcards logic
- Stores study materials in SQLite/JSON for search + retrieval

**Credentials:**
- Anki: treytucker05@yahoo.com / Turtle1! (encrypted on disk)

---

### Program 2: blackboard-agent (Data Extractor) ⚠️
**Status:** Phase 2 (finalizing - Selenium scroll fix in place)  
**Location:** `PROGRAMS/blackboard-agent/`

**What it does:**
- Logs into UTMB Blackboard (Selenium automation)
- Extracts all 5 enrolled courses
- Pulls modules and content from each course
- Extracts all due dates from expandable folders
- (Future) Downloads files from course materials

**Handlers:**
- `blackboard_handler.py` — Main Selenium orchestrator
- `claude_handler.py` — Integration with Claude tools

**Credentials:**
- Username: frtucker
- Password: OmmarAnnie1! (env var)
- Base URL: https://utmb.blackboard.com

**Current Blockers:**
- Anatomy & PT Exam Skills not appearing in courses list (likely filter issue)
  - **Solution:** Hardcode 5 course URLs after `extract_course_urls.py` runs
- Scroll fix applied to load all folders (both `get_courses()` and `get_due_dates()`)

**Target:** Extract all 48 due dates (Legal 14, Lifespan 2, Pathology 22, Anatomy 6, Exam Skills 4)

---

### Program 3: dashboard-api (Agent Control Panel) ⏳
**Status:** In Development  
**Location:** `PROGRAMS/dashboard-api/`

**What it does:**
- Web dashboard showing Agent system status
- NOT for deck management — for monitoring & control
- Real-time status of:
  - Blackboard extraction (courses found, due dates pulled, last run time)
  - Anki sync (cards pushed, decks updated, last sync time)
  - MCP server health (tools available, ngrok tunnel status)
  - Study progress (cards reviewed today, upcoming due items, schedule)

**Frontend:** React/Next.js  
**Backend:** Node.js HTTP API  
**Data Source:** Queries fastmcp-server + local Anki via AnkiConnect

**Purpose:** Single control point for your AI study system. At a glance: "What's my study status?"

---

## PHASES & TIMELINE

### Phase 2: Data Extraction (NOW - This Week)
**Objective:** Reliably extract all course data from Blackboard

**Tasks:**
1. ✅ Implement Selenium scroll loop in `get_courses()` and `get_due_dates()`
2. 🔄 Extract 5 course URLs via `extract_course_urls.py` (Codex task)
3. 🔄 Test due-date extraction against hardcoded URLs → Confirm ~48 total
4. ⏳ Implement file downloads from Blackboard (low priority)

**Success Criteria:**
- All 5 courses surface in course list
- All ~48 due dates extracted (breakdown: Legal 14, Lifespan 2, Pathology 22, Anatomy 6, Exam Skills 4)
- Zero timeout errors in Selenium

**Deliverable:** `COURSE_URLS.txt` with 5 hardcoded URLs; due-date extraction test passing

---

### Phase 3: Integration & Orchestration (Next Week)
**Objective:** Wire all systems together; Claude controls the flow

**Tasks:**
1. ⏳ Refresh ChatGPT MCP connection (re-add server URL, bypass cache)
2. ⏳ Validate all 13 tools work via ChatGPT (test each tool individually)
3. ⏳ End-to-end test: Ask Claude to extract Legal & Ethics due dates → Generate flashcards → Push to Anki
4. ⏳ Add smoke tests + logging for Anki operations
5. ⏳ Document error handling (AnkiConnect offline, Blackboard 403, etc.)

**Success Criteria:**
- Claude can call all 13 tools without errors
- Flashcards created via Claude appear in Anki within 5 minutes
- Logs show full request/response chain
- One full workflow completes: Extract → Generate → Push → Verify

**Deliverable:** Integration test report; end-to-end workflow video; error handling docs

---

### Phase 4: Dashboard & Monitoring (Week After Next)
**Objective:** Build Agent control panel; full system visibility

**Tasks:**
1. Build Node.js API endpoints for:
   - Blackboard extraction status
   - Anki sync status
   - MCP server health
   - Study progress metrics
2. Build React dashboard frontend
3. Add real-time notifications (Slack/email when extractions fail)
4. Add scheduling (auto-extract due dates every morning)

**Success Criteria:**
- Dashboard loads and shows current system status
- Metrics update in real-time
- One failed extraction triggers a notification

**Deliverable:** Working dashboard at `http://localhost:3000`

---

### Phase 5: Polish & Production Ready
**Objective:** Make it bulletproof and automatic

**Tasks:**
1. Add retry logic to all Selenium operations
2. Implement database for extracted materials (SQLite → PostgreSQL)
3. Add CI/CD pipeline (GitHub Actions → auto-test extraction daily)
4. Write comprehensive error handling docs
5. Package as Docker container (optional: AWS Lambda for scheduled runs)

**Success Criteria:**
- System runs 7 days without manual intervention
- Any error is logged + recoverable
- Dashboard shows 99.5% uptime

**Deliverable:** Production-ready system; deployment guide

---

## STUDY METHODOLOGY: PERRIO Protocol v6.4

All flashcard generation follows PERRIO (Gather-Prime-Encode-Retrieve-Reinforce-Close):

1. **Gather:** Extract raw materials from Blackboard
2. **Prime:** Identify key concepts
3. **Encode:** Create flashcards with clinical relevance
4. **Retrieve:** Card pushed to Anki
5. **Reinforce:** You review cards using spaced repetition
6. **Close:** Deck consolidated before next extraction

Implementation in `fastmcp-server/tools/generate_flashcards.py`

---

## HOW IT ALL CONNECTS

```
┌─────────────────────────────────────────────────────────────┐
│                    YOU                                      │
│          (Ask Claude for study help)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        v                         v
   ChatGPT                   Your Browser
   (Claude 4.5)              (Manual checks)
        │                         │
        └────────────┬────────────┘
                     │
                     v
        ┌────────────────────────┐
        │  fastmcp-server        │
        │  (MCP + 13 tools)      │
        │  ngrok tunnel          │
        └────────┬───────────────┘
                 │
        ┌────────┴────────┬──────────────┐
        │                 │              │
        v                 v              v
  blackboard-agent   AnkiBridge    dashboard-api
  (Selenium)         (HTTP)         (Node.js)
        │                 │              │
        v                 v              v
   Blackboard        Anki Desktop    React Dashboard
   (UTMB portal)      (127.0.0.1:     (http://localhost:
                      8765)            3000)

FLOW: You → Claude → Tools → Extract/Generate/Push → Anki
                                                        ↓
                                                  Review & Study
```

---

## FILES & LOCATIONS

**Core Programs:**
- `PROGRAMS/fastmcp-server/` — MCP orchestrator
- `PROGRAMS/blackboard-agent/` — Blackboard extraction
- `PROGRAMS/dashboard-api/` — Control panel (in dev)

**Critical Configs:**
- `.env` — API keys, credentials (Blackboard login, ngrok token)
- `PROGRAMS/blackboard-agent/COURSE_URLS.txt` — 5 hardcoded course URLs (to be created)

**Credentials (Encrypted):**
- Anki: treytucker05@yahoo.com / Turtle1!
- Blackboard: frtucker / OmmarAnnie1!

**Documentation:**
- `_MASTER_DOCS/DRCODEPT_MASTER_PLAN.md` ← You are here
- `_MASTER_DOCS/PHASE_CHECKLISTS.md` — Task breakdowns per phase
- `ACTIVE_ROADMAP.md` — Next 3 priorities (updated weekly)
- `QUICK_REFERENCE_GUIDE.md` — Commands to start/test systems

---

## HOW TO START SYSTEMS

**Start fastmcp-server:**
```bash
cd PROGRAMS/fastmcp-server
python server.py
# Runs on localhost:8000
# ngrok tunnel: see console output
```

**Start blackboard extraction:**
```bash
cd PROGRAMS/blackboard-agent
python extract_course_urls.py  # Get the 5 URLs
python -c "from handlers.blackboard_handler import BlackboardHandler; ..."  # Test extraction
```

**Start dashboard:**
```bash
cd PROGRAMS/dashboard-api
npm install && npm start
# Runs on http://localhost:3000
```

**Test full flow:**
```bash
# In ChatGPT, add fastmcp-server via MCP configuration
# Ask Claude: "Extract due dates from Legal & Ethics and create 3 flashcards"
# Check Anki — cards should appear within 5 minutes
```

---

## SUCCESS METRICS

**Phase 2:** ✅ All 5 courses extracted, ~48 due dates confirmed  
**Phase 3:** ✅ Claude can extract + generate + push to Anki end-to-end  
**Phase 4:** ✅ Dashboard shows real-time status  
**Phase 5:** ✅ System runs autonomously for 7+ days  

**Final Success:** You stop manually organizing study materials. Claude does it.

---

## KNOWN ISSUES & WORKAROUNDS

| Issue | Status | Workaround |
|-------|--------|-----------|
| Anatomy & PT Exam Skills missing from course list | 🔄 In progress | Hardcode URLs via extract_course_urls.py |
| ChatGPT MCP tool cache issue | ⏳ Phase 3 | Re-add server URL to ChatGPT |
| Blackboard session timeout after 30 min | ⏳ Phase 2/3 | Implement re-login logic in blackboard_handler.py |
| AnkiConnect down → cards fail to push | ⏳ Phase 5 | Add retry logic + queue system |

---

## CONTACTS & RESOURCES

**Your Resources:**
- UTMB Blackboard: https://utmb.blackboard.com
- Anki Desktop: https://apps.ankiweb.net/
- ngrok: https://ngrok.com (account: PowerHouseATX)
- MCP Docs: https://modelcontextprotocol.io/

**Credentials File:**
- Store all sensitive data in `.env` (Blackboard login, ngrok token, Anki email)
- Never commit to git

---

## REVISION HISTORY

| Date | Phase | Change |
|------|-------|--------|
| Nov 12, 2025 | 2→3 | Clarified architecture (2 programs, not 4); added dashboard scope; locked in PERRIO v6.4 |
| Nov 12, 2025 | 2 | Added Selenium scroll fix to get_courses() and get_due_dates() |
| Nov 11, 2025 | 2 | Blackboard agent extraction tested; scroll issue identified |
| Nov 10, 2025 | 3 | FastMCP server + AnkiBridge working end-to-end |

---

**Next Action:** Run `extract_course_urls.py` to lock in 5 course URLs. Report the URLs here.
