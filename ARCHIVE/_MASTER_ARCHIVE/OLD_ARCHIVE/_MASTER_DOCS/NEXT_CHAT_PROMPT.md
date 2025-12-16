# NEXT CHAT PROMPT - Copy & Paste This

**Use this to start your next conversation with Claude:**

---

## CONTEXT: DrCodePT-Swarm Phase 2 Finalization

We just completed the master plan and architecture review for my AI study automation system. Here's the state:

**Project:** Automate PT school study workflow. Extract Blackboard materials → Generate Anki flashcards via Claude → Track progress.

**Architecture (2 core programs + 1 dashboard):**
1. **fastmcp-server** (MCP orchestrator) — ✅ Working, 13 tools built, connected to ChatGPT via ngrok
2. **blackboard-agent** (Blackboard extraction) — 🔄 90% done, Selenium scroll fix applied to load all courses + due dates
3. **dashboard-api** (Agent control panel) — ⏳ Not started

**Current Blocker:** Anatomy & PT Exam Skills courses not appearing in Blackboard course list (likely filter). Solution: Extract 5 course URLs directly via script.

**Master Docs Created:**
- `_MASTER_DOCS/DRCODEPT_MASTER_PLAN.md` — Full architecture + vision
- `_MASTER_DOCS/PHASE_CHECKLISTS.md` — Task breakdown per phase
- `_MASTER_DOCS/QUICK_REFERENCE.md` — Commands + troubleshooting
- `ACTIVE_ROADMAP.md` — Updated weekly priorities

**Phase 2 Status (THIS WEEK):**
- [x] Selenium scroll fix applied to get_courses() and get_due_dates()
- [x] Master plan + architecture locked
- [ ] Extract 5 course URLs via `extract_course_urls.py` ← NEXT (Codex task)
- [ ] Test due-date extraction → Confirm ~48 total ← AFTER URLs

**Phase 3 Gate (NEXT WEEK):**
- Re-connect fastmcp-server to ChatGPT (re-add URL to MCP settings)
- Test all 13 tools individually
- Run full workflow: Claude extracts Legal & Ethics → generates flashcards → pushes to Anki
- Verify end-to-end

**Credentials on File:**
- Blackboard: frtucker / OmmarAnnie1!
- Anki: treytucker05@yahoo.com / Turtle1!
- ngrok: configured (see fastmcp-server console)

---

## IMMEDIATE NEXT STEPS (TODAY)

1. **Codex:** Create `PROGRAMS/blackboard-agent/extract_course_urls.py`
   - Login, navigate to Courses, extract all 5 course outline URLs
   - Save to `COURSE_URLS.txt`
   - Expected: 5 URLs like `https://utmb.blackboard.com/ultra/courses/_XXXXX/outline`

2. **Trey (me):** After URLs extracted, test due-date extraction
   - Run: `python test_all_due_dates.py` (or similar)
   - Target: ~48 total (Legal 14, Lifespan 2, Pathology 22, Anatomy 6, Exam Skills 4)

3. **Both:** Update docs (mark Phase 2 tasks as done)

---

## WHAT I NEED FROM YOU

**Option A:** Continue with the blocker
- Help Codex build `extract_course_urls.py` script
- Debug if URLs don't extract
- Help test the due-date extraction

**Option B:** Jump ahead to Phase 3
- Start testing fastmcp-server connection to ChatGPT
- Run tool tests individually
- Prep for full workflow test

**Option C:** Build dashboard backend
- Start designing dashboard API endpoints
- Begin Node.js API code

**My preference:** Option A (finish Phase 2 blocker TODAY), then Phase 3 next week.

---

## FILES TO REFERENCE

**Master Docs (read these first):**
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\_MASTER_DOCS\DRCODEPT_MASTER_PLAN.md`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\_MASTER_DOCS\PHASE_CHECKLISTS.md`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\ACTIVE_ROADMAP.md`

**Program Folders:**
- `PROGRAMS/fastmcp-server/` — MCP server (running)
- `PROGRAMS/blackboard-agent/` — Selenium extraction (needs extract_course_urls.py)
- `PROGRAMS/dashboard-api/` — Dashboard (not started)

**Key File to Create:**
- `PROGRAMS/blackboard-agent/COURSE_URLS.txt` ← Will be created by extract_course_urls.py

---

**Status:** Phase 2 (Finalizing) → Phase 3 (Integration) next week  
**Timeline:** 5 phase project, ~4 weeks to production  
**Owner:** Trey (me) + Claude (Codex as implementation agent)

Let's finish this blocker and move Phase 2 to complete. 🚀
