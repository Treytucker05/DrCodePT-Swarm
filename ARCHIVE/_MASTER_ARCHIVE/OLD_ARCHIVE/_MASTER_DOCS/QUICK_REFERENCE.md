# Quick Reference: System Status & Commands
**Last Updated:** November 12, 2025  
**Current Phase:** 2 (Finalizing) → 3 (Integration)

---

## CURRENT STATUS AT A GLANCE

| Component | Status | Next Step |
|-----------|--------|-----------|
| fastmcp-server | ✅ Working | Re-add to ChatGPT (Phase 3) |
| blackboard-agent | 🔄 90% (scroll fix applied) | Extract course URLs (NOW) |
| AnkiBridge | ✅ Working | Test via ChatGPT (Phase 3) |
| dashboard-api | ⏳ Not started | Build after Phase 3 |

**Critical Blocker:** Anatomy & PT Exam Skills not in course list  
**Current Solution:** Extract 5 course URLs via `extract_course_urls.py` (Codex running)

---

## QUICK COMMANDS

### Start fastmcp-server
```bash
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server
python server.py
```
Expected output: `Server running on http://localhost:8000 + ngrok tunnel URL`

### Test Blackboard Extraction
```bash
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\blackboard-agent
python tmp_list_courses.py
```
Expected output: 5 courses found (Legal, Lifespan, Pathology, Anatomy, Exam Skills)

### Extract Course URLs (TODO - Codex)
```bash
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\blackboard-agent
python extract_course_urls.py
```
Creates: `COURSE_URLS.txt` with 5 URLs

### Test Due Dates Extraction
```bash
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\blackboard-agent
python -c "
from handlers.blackboard_handler import BlackboardHandler
handler = BlackboardHandler()
handler.login()
courses = handler.get_courses()
total = 0
for course in courses:
    dates = handler.get_due_dates(course['url'])
    total += len(dates)
    print(f'{course[\"code\"]}: {len(dates)} due dates')
print(f'TOTAL: {total}')
handler.close()
"
```
Expected output: Total ~48 due dates

### Test Full Workflow (After Phase 3 setup)
In ChatGPT with MCP connected:
```
Extract due dates from Legal & Ethics and create 5 flashcards.
```
Expected: Cards appear in Anki within 5 minutes

---

## CREDENTIALS & CONFIG

**Blackboard Login:**
- URL: https://utmb.blackboard.com
- Username: <YOUR_BLACKBOARD_USERNAME>
- Password: <YOUR_BLACKBOARD_PASSWORD> (stored in .env)

**Anki:**
- Local: 127.0.0.1:8765 (AnkiConnect)
- Email: <YOUR_ANKI_EMAIL>
- Password: <YOUR_ANKI_PASSWORD> (stored locally)

**ngrok:**
- Token: (stored in .env)
- Tunnel URL: See fastmcp-server console output

**.env Location:**
`PROGRAMS/blackboard-agent/.env` and `PROGRAMS/fastmcp-server/.env`

---

## PHASE 2 TASKS (THIS WEEK)

### NOW: Extract 5 Course URLs
**Task:** Codex runs `extract_course_urls.py`  
**Output:** `COURSE_URLS.txt` in blackboard-agent folder  
**File should contain:**
```
https://utmb.blackboard.com/ultra/courses/_XXXXX/outline
https://utmb.blackboard.com/ultra/courses/_YYYY/outline
https://utmb.blackboard.com/ultra/courses/_ZZZZ/outline
https://utmb.blackboard.com/ultra/courses/_AAAA/outline
https://utmb.blackboard.com/ultra/courses/_BBBB/outline
```

### AFTER URLs: Test Due Dates
**Task:** Run the due-dates test command above  
**Target:** ~48 total (Legal 14, Lifespan 2, Pathology 22, Anatomy 6, Exam Skills 4)  
**Success:** All targets met

### FINAL: Document in Phase 2 Summary
- [ ] Update `ACTIVE_ROADMAP.md` with completion
- [ ] Document any issues + workarounds
- [ ] Note timing (how long extraction takes)

---

## PHASE 3 TASKS (NEXT WEEK)

### 3.1: Connect FastMCP to ChatGPT
1. Open ChatGPT Settings → Connected Apps → MCP Servers
2. Add new server:
   - Name: StudyMCP
   - URL: (ngrok tunnel from fastmcp-server console)
3. Refresh → Verify all 13 tools appear
4. Document tool list screenshot

### 3.2: Test Each Tool
For each of the 13 tools, ask Claude:
```
"Test the [TOOL_NAME] tool. Show me the result."
```
Examples:
- "Test ingest_file: Upload this text [sample]"
- "Test generate_flashcards: Create 3 cards from this [text]"
- "Test addCardToDeck: Create a card and push it to Anki"

### 3.3: Run Full Workflow
```
Claude: "Extract due dates from Legal & Ethics and create 5 flashcards."
```
Then check:
- [ ] Claude's response shows extraction happened
- [ ] Open Anki → Verify 5 cards in DrCodePT deck
- [ ] Check logs for full request/response chain

---

## FILE LOCATIONS

**Master Docs:**
```
C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\_MASTER_DOCS\
  ├─ DRCODEPT_MASTER_PLAN.md (full architecture + vision)
  ├─ PHASE_CHECKLISTS.md (detailed task breakdown)
  └─ QUICK_REFERENCE.md (this file)
```

**Programs:**
```
C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\
  ├─ fastmcp-server\ (MCP orchestrator)
  ├─ blackboard-agent\ (Blackboard extraction)
  └─ dashboard-api\ (Control panel - in dev)
```

**Results & Logs:**
```
C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\
  ├─ COURSE_URLS.txt (5 hardcoded URLs - to be created)
  ├─ TEST_RESULTS_*.txt (test output)
  └─ _ARCHIVE\OLD_DOCS\ (27 older docs, keep for reference)
```

---

## TROUBLESHOOTING

### "Anatomy and PT Exam Skills don't appear in course list"
**Cause:** Blackboard filters to "Current/Favorites" only  
**Solution:** Hardcode URLs via `extract_course_urls.py`

### "Selenium timeout when scrolling"
**Cause:** Page takes >1 sec to load more content  
**Solution:** Increase sleep time in scroll loop from 1s to 2s

### "AnkiConnect connection refused"
**Cause:** Anki not running or AnkiConnect add-on not installed  
**Solution:**
1. Open Anki desktop
2. Tools → Add-ons → Install add-on → Paste: 2055492159 (AnkiConnect)
3. Restart Anki

### "ChatGPT doesn't see MCP tools"
**Cause:** Cache or URL mismatch  
**Solution:**
1. Remove server URL from ChatGPT MCP settings
2. Re-add the exact ngrok tunnel URL
3. Refresh ChatGPT page (Cmd+R)
4. Wait 30 seconds

### "FastMCP server won't start"
**Cause:** Port 8000 already in use or dependency missing  
**Solution:**
```bash
# Check what's using port 8000
netstat -ano | findstr :8000
# Kill the process or use different port in server config
```

---

## KEY CONTACTS & RESOURCES

**Code Owner:** Codex (for implementation)  
**Testing Owner:** Trey (for verification)  
**Documentation:** Both (collaborative)

**External Resources:**
- UTMB Blackboard: https://utmb.blackboard.com
- Anki: https://apps.ankiweb.net/
- ngrok: https://ngrok.com
- MCP Spec: https://modelcontextprotocol.io/

**Credentials Stored:** `.env` files (keep private, never commit to git)

---

## NEXT IMMEDIATE STEPS

1. **TODAY:** Codex extracts 5 course URLs → `COURSE_URLS.txt`
2. **TODAY:** Trey tests due-date extraction → Confirm ~48 total
3. **TOMORROW:** Document any issues; Phase 2 = COMPLETE
4. **NEXT WEEK:** Phase 3 begins (ChatGPT integration)

---

**Last Updated:** November 12, 2025  
**Next Review:** After Phase 2 completion
