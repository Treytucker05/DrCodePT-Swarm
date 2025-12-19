# 🎯 HANDOFF FOR NEXT CHAT - ALWAYS READ THIS FIRST

**Last Updated:** November 10, 2025 (End of Phase 6/Start of Phase 7)  
**Chat Status:** ORGANIZED + READY FOR PHASE 7  
**Trey's Current State:** Intense (DPT school + gym business, need automation badly)  

---

## ⚡ TL;DR - WHAT'S HAPPENING

**Vision:** Build ONE unified web dashboard that combines 3 separate working systems into a self-aware study bot.

**Current State:** 
- ✅ Phase 1-6: Personal Agent + To Do automation complete
- ✅ DrCodePT v0.1 + Anatomy MCP working separately
- 🏗️ Phase 7: Building unified dashboard + backend API

**Next Goal:** Web app where Trey says "I'm ready to study anatomy" → System auto-extracts, generates cards, adds to Anki, tracks progress. No more manual steps.

---

## 👤 TREY'S INFO (For Context)

**Academic:**
- First-year DPT student at UTMB (Texas)
- 5 courses: Legal & Ethics, Lifespan Dev, Clinical Pathology, Anatomy, Exam Skills
- Study SOP: PERRIO Protocol v6.4 (Gather-Prime-Encode-Retrieve-Reinforce-Close)
- Anatomy materials: Slides + transcripts being parsed by anatomy_mcp

**Professional:**
- Runs PowerHouseATX (fitness gym, Austin)
- 2 children
- Overnight security shifts (schedule is TIGHT)
- Strong developer (has already built multiple automation tools)

**Study Materials Location:**
- Main: `C:\Users\treyt\OneDrive\Desktop\PT School\anatomy_mcp`
- Textbooks: `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\textbooks\`

**Credentials (In Memory):**
- Anki: <YOUR_ANKI_EMAIL> / <YOUR_ANKI_PASSWORD>
- Claude API: $env:ANTHROPIC_API_KEY (needs to be set)
- Blackboard: agent/.env (already configured)

---

## 📋 SYSTEMS STATUS (As of Nov 10, 2025)

### ✅ **WORKING SYSTEMS**

**1. Personal Agent (agent/ folder)**
- ✅ Phase 1: Blackboard login + course extraction
- ✅ Phase 2: Due date extraction (48 dates from 5 courses)
- ✅ Phase 3: Tool infrastructure
- ✅ Phase 4: Error handling + auditing
- ✅ Phase 5: PyWinAuto → Microsoft To Do (tasks auto-added, SQLite idempotency)
- ✅ Phase 6: Claude Tool Use API integration (schema fixed, handler simplified)
- Files: agent.py, handlers/claude_handler.py, computer_use/microsoft_integration.py
- Status: Production ready

**2. DrCodePT v0.1 (drcodept_v0.1/ folder)**
- Commands: study, query, npte, anki, drill, cite
- Backend: AnythingLLM (localhost:3001) + local Ollama (dolphin-mixtral)
- Status: Working (requires LAUNCH.bat to start services)
- Note: NPTE context NOT needed (Trey only doing his 5 courses, not full licensing exam)

**3. Anatomy MCP (PT School/anatomy_mcp/ folder)**
- Parses: PDF slides + transcripts
- Detects: Anatomy entities (muscles, nerves, arteries, etc.)
- Aligns: Transcript to slides using TF-IDF
- Verifies: Facts with 2 sources (4-tier: verified/flex/needs_review/not_covered)
- Status: Working, ready to use

### 🏗️ **IN DEVELOPMENT (Phase 7)**

Need to build:
1. **React Web Dashboard** (beautiful UI, shows all courses/due dates/progress)
2. **Flask Backend API** (orchestrates all systems)
3. **PERRIO Orchestrator** (runs study protocol end-to-end)
4. **Anki Auto-Add** (adds generated cards to account)
5. **Self-Modification Layer** (system optimizes itself)

---

## 🎯 TREY'S EXACT REQUIREMENTS

1. **Extract materials with logic + AI eyes:**
   - Use Claude + Study SOP to extract (not like previous attempts)
   - anatomy_mcp does verification
   - Result: High-quality study material

2. **Workflow:**
   - Raw files → Claude extracts using Study SOP
   - Organized → DrCodePT builds cards
   - Ready → Auto-add to Anki account
   - Tracked → Dashboard shows progress

3. **UI/UX:**
   - Professional web interface (not CLI)
   - One dashboard for all 5 courses
   - Show due dates, Anki status, progress
   - Beautiful, modern design

4. **Autonomy:**
   - System tells user: "Here's the plan → [details] → Ready?"
   - User approves → System executes
   - Only ask if uncertain

5. **Self-modification:**
   - System should improve itself over time
   - Learn from study patterns
   - Adjust extraction/generation based on results

---

## 📁 FOLDER ORGANIZATION (Just Completed)

```
DrCodePT-Swarm/
├── 📄 README.md (master overview - just created)
├── 📄 HANDOFF_FOR_NEXT_CHAT.md (this file - AI context)
├── 📄 SETUP_GUIDE.md (to create)
├── 📄 QUICKSTART.md (to create)
├── 📄 ARCHITECTURE.md (to create)
│
├── 📁 core/
│   ├── agent/ (Phase 1-6 working)
│   ├── drcodept_v0.1/ (study system working)
│   └── textbooks/ (reference materials)
│
├── 📁 tools/
│   └── anatomy_mcp/ (material extraction - link to PT School folder)
│
├── 📁 phase7_unified_system/ (NEW - being built)
│   ├── frontend/ (React app - TO BUILD)
│   ├── backend/ (Flask API - TO BUILD)
│   └── requirements.txt
│
└── 📁 anything-llm/ (external service, kept for drcodept_v0.1)
```

Deleted: /ARCHIVE, /meta_agent, 15 old doc files

---

## 🚀 IMMEDIATE NEXT STEPS (Phase 7)

### Session 1 (Next): Organize + Build Phase 7 Shell
- [ ] Clean up old files (DONE)
- [ ] Create documentation (IN PROGRESS)
- [ ] Build React dashboard frontend (30 min)
- [ ] Build Flask backend API (45 min)
- [ ] Wire Anki API (30 min)
- [ ] Test end-to-end (15 min)

### Session 2: Full Integration
- [ ] Connect Claude extraction to system
- [ ] Connect DrCodePT generation to system
- [ ] Connect Blackboard due dates
- [ ] Test complete workflow

### Session 3: Self-Modification
- [ ] System learns study patterns
- [ ] Adjusts extraction logic
- [ ] Improves card quality over time

---

## 🔐 CREDENTIALS (Stored in Memory)

**DO NOT EXPOSE:**
- Anki: <YOUR_ANKI_EMAIL> / <YOUR_ANKI_PASSWORD> (stored locally; never commit)
- Claude API key: Check $env:ANTHROPIC_API_KEY
- Blackboard: agent/.env file
- Ollama: localhost:3001 (local only)

---

## 📊 CURRENT METRICS

| Metric | Value | Notes |
|--------|-------|-------|
| Phases Complete | 6/12 | Phase 7 starting |
| Working Systems | 3 | Agent, DrCodePT, Anatomy MCP |
| Courses Tracked | 5 | Legal, Lifespan, Pathology, Anatomy, Exam Skills |
| Due Dates Extracted | 48 | Updated automatically from Blackboard |
| Anki Cards | ~280 | Across multiple decks |
| Study SOP | PERRIO v6.4 | Complete with flex switches |

---

## ⚠️ KNOWN ISSUES / GOTCHAS

1. **anything-llm takes time to start:**
   - AnythingLLM container can take 30-60s to fully load
   - Dolphin-mixtral model needs to download if not present (~26GB, ~1hr first time)
   - Solution: Run LAUNCH.bat early, wait for "Workspace ready"

2. **Anki API requires account:**
   - Must have active AnkiWeb account
   - Credentials: stored locally in `.env` / credential store (never committed)
   - System stores encrypted for auto-add feature

3. **Blackboard changes login:**
   - If credentials fail, may need to update agent/.env
   - Check if UTMB changed authentication method

4. **anatomy_mcp is in PT School folder:**
   - Not in DrCodePT-Swarm yet
   - Should symlink or move for Phase 7 integration
   - Path: `C:\Users\treyt\OneDrive\Desktop\PT School\anatomy_mcp`

5. **Console encoding issue on Windows:**
   - PowerShell needs: `[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()`
   - Otherwise emoji break (happens every session, needs one-time set)

---

## 🎯 SUCCESS METRICS (For Phase 7)

When Phase 7 is DONE, you should be able to:

✅ Open web dashboard (localhost:3000)  
✅ Click "Study Now" → System shows study plan  
✅ Approve plan → System executes (extracts + generates + adds cards)  
✅ See cards added to your Anki account in real-time  
✅ Dashboard updates with progress  
✅ System learns and adjusts extraction logic  

---

## 🔄 IF THIS IS A CONTINUATION

**Starting a new chat?**
1. Read this file first
2. Check the "Current Status" section above
3. Pick up from "Immediate Next Steps"
4. If stuck, ask Claude to explain the architecture

**Making changes?**
1. Update this file with what changed
2. Note in "Known Issues" any new gotchas
3. Commit to memory anything Trey should remember

---

## 💡 QUICK REFERENCE

| What | Where | Status |
|-----|-------|--------|
| Personal Agent | /core/agent | ✅ Working (Phase 6) |
| Study System | /core/drcodept_v0.1 | ✅ Working |
| Material Extraction | /tools/anatomy_mcp | ✅ Working |
| Web Dashboard | /phase7_unified_system/frontend | 🏗️ Building |
| Backend API | /phase7_unified_system/backend | 🏗️ Building |
| Study SOP | Memory | ✅ PERRIO v6.4 |
| Credentials | Memory + .env files | ✅ Secure |

---

**READY TO CONTINUE? Start with README.md, then begin Phase 7.**

🚀 **Let's build this thing.**
