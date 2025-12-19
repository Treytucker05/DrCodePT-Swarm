# 🚀 START HERE - DrCodePT-Swarm Phase 2C

**Last Updated:** November 11, 2025  
**Current Phase:** 2C - ChatGPT Bridge (In Progress)  
**Status:** Ready for Smoke Test

---

## 📖 What is This System?

An AI-powered automation system for UTMB DPT coursework that:
- ✅ Scrapes Blackboard for courses & due dates (48 extracted)
- ✅ Generates Anki flashcards automatically using Claude
- ✅ Runs a FastMCP server for ChatGPT integration
- ⏳ Provides a web dashboard for course/deck/card management (Smoke testing now)

---

## 🎯 What's Currently Running?

**4 Working Systems (PROGRAMS/):**
1. **blackboard-agent** - Scrapes UTMB portal (working)
2. **card-generator** - Creates flashcards via PERRIO Protocol v6.4 (working)
3. **fastmcp-server** - Bridges to ChatGPT at localhost:8000 (running now)
4. **study-materials** - Organized textbooks & notes (ready)

**1 System Being Tested (IN_DEVELOPMENT/):**
- **dashboard-api** - Web UI + REST API (smoke test in progress)

---

## 📁 New Folder Structure (November 11, 2025)

```
DrCodePT-Swarm/
├── PROGRAMS/ ........................ ✅ All production code
│   ├── blackboard-agent/
│   ├── card-generator/
│   ├── fastmcp-server/
│   └── study-materials/
│
├── IN_DEVELOPMENT/ ................. ⏳ Codex's current project
│   └── dashboard-api/
│       ├── api-server.js ........... 11 REST endpoints
│       ├── dashboard/ .............. Web UI (HTML/JS/CSS)
│       └── package.json ............ npm dependencies
│
├── DOCS/ ........................... 📚 Technical reference
│   └── phase_2c/ ................... Phase 2C implementation guide
│
└── _ARCHIVE/ ....................... 📦 Legacy systems (ignore)
```

---

## 🚀 Quick Start (First Time?)

**Prerequisites:**
- Python 3.8+
- Node.js 14+
- Anki desktop app
- FastMCP library installed

**Step 1: Verify FastMCP is running**
```powershell
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server
python server.py
# Should see: Server running on http://localhost:8000
```

**Step 2: Verify API is running**
```powershell
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\IN_DEVELOPMENT\dashboard-api
npm run start:api
# Should see: Server running on port 7400
```

**Step 3: Open Dashboard**
```
file:///C:/Users/treyt/OneDrive/Desktop/DrCodePT-Swarm/IN_DEVELOPMENT/dashboard-api/dashboard/index.html
```

**Step 4: Test end-to-end**
- Create a course (e.g., "Anatomy")
- Create a deck (e.g., "Chapter 5")
- Add a card (title + content)
- Verify it saves to C:\PT School\Anatomy\Chapter 5\deck.json

---

## 📋 Current State (Smoke Test Phase)

**What works:**
- ✅ FastMCP server operational
- ✅ Blackboard scraper extracting 48 due dates
- ✅ Card generator creating flashcards
- ✅ API has all 11 endpoints built
- ✅ Dashboard UI scaffolded and ready

**What we're testing right now:**
- ⏳ API starts without errors
- ⏳ Dashboard loads in browser
- ⏳ Full workflow: Course → Deck → Card → Saved to disk
- ⏳ FastMCP integration working
- ⏳ Data persists correctly

**Success = all 9 checklist items in CODEX_INSTRUCTIONS.md pass**

---

## 🔗 Key Files & Where to Find Them

**To understand the whole system:**
1. Read: `GAMEPLAN.md` (master strategy)
2. Read: `STATUS.md` (current state & next steps)
3. Deep dive: `DOCS/phase_2c/README_PHASE_2C.md`

**To see what Codex is doing:**
- Read: `CODEX_INSTRUCTIONS.md` (Codex's task)
- Check: `IN_DEVELOPMENT/dashboard-api/` (the code)

**To run the systems:**
- FastMCP: `PROGRAMS/fastmcp-server/server.py`
- API: `IN_DEVELOPMENT/dashboard-api/api-server.js`
- Dashboard: `IN_DEVELOPMENT/dashboard-api/dashboard/index.html`

**For technical details:**
- See: `DOCS/phase_2c/PHASE_2C_CODE_REFERENCE.md`

---

## 💾 Data Storage

All study data goes to: `C:\PT School\`

Structure:
```
C:\PT School\
├── Anatomy\
│   ├── _decks-index.json
│   └── Chapter-5-Muscles\
│       └── deck.json (Anki-importable)
├── Legal & Ethics\
├── Lifespan Development\
├── Clinical Pathology\
└── PT Examination Skills\
```

---

## 🔐 Credentials & Config

**Anki Access:**
- Email: `<YOUR_ANKI_EMAIL>`
- Password: `<YOUR_ANKI_PASSWORD>` (stored locally)

**API Configuration:**
- FastMCP URL: `http://localhost:8000`
- API Port: `7400`
- Check: `IN_DEVELOPMENT/dashboard-api/.env.example`

---

## 📊 Phase 2C Goals

Phase 2C is complete when:
- [ ] API server starts cleanly
- [ ] Dashboard loads in browser
- [ ] Can create course/deck/card via UI
- [ ] Cards save to disk correctly
- [ ] FastMCP integration verified
- [ ] All 9 smoke test checklist items pass ✅
- [ ] Documentation updated for Phase 3

---

## ⏳ What's Next After Smoke Test?

After this smoke test passes:
1. **ChatGPT Integration** - Point ChatGPT to FastMCP server
2. **Full Workflow Test** - Create card in ChatGPT → See it in dashboard
3. **Anki Import** - Export to Anki and verify cards appear
4. **Scale to 5 Courses** - Repeat across all PT courses
5. **Phase 3** - Production deployment & optimization

---

## 🆘 Troubleshooting

**FastMCP won't start?**
```powershell
pip install fastmcp
# Then try again
```

**Dashboard won't load?**
- Check: Is API running on port 7400?
- Check: Browser console for errors (F12)
- Check: File path is correct (no backslashes in URL)

**Card not saving?**
- Check: `C:\PT School\` directory exists
- Check: Write permissions on C:\PT School\
- Check: API logs for errors

**Port already in use?**
```powershell
# Kill existing process
Get-Process node | Stop-Process
Get-Process python | Stop-Process
# Then restart
```

---

## 📞 Quick Reference

| Need | Location |
|------|----------|
| Master plan | `GAMEPLAN.md` |
| Current status | `STATUS.md` |
| Codex's task | `CODEX_INSTRUCTIONS.md` |
| System overview | `DOCS/phase_2c/README_PHASE_2C.md` |
| Deep technical dive | `DOCS/phase_2c/PHASE_2C_CODE_REFERENCE.md` |
| Verification checklist | `DOCS/phase_2c/PHASE_2C_VERIFICATION.md` |

---

## ✅ Success Indicators

You'll know everything is working when:

1. **API responds:**
   ```
   GET http://localhost:7400/api/health
   Returns: { status: "ok", timestamp: "..." }
   ```

2. **Dashboard loads** in browser without errors

3. **Can create course/deck/card** via web UI

4. **Files exist** after saving:
   ```
   C:\PT School\Anatomy\Chapter-5-Muscles\deck.json
   ```

5. **JSON is valid** (can open in text editor and parse)

6. **FastMCP shows "connected"** in dashboard sync status

---

**You're ready to go! Start with the "Quick Start" section above.** 🚀

Next chat: Check smoke test results and proceed to ChatGPT integration.
