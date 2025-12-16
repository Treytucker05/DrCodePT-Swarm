# GAMEPLAN - DrCodePT-Swarm Master Strategy

**Last Updated:** November 11, 2025  
**Owner:** Trey  
**Status:** In Execution

---

## 🎯 Mission

Build an AI-powered automation system for UTMB DPT coursework that:
- Scrapes Blackboard for course data & due dates
- Generates flashcards automatically using Claude + PERRIO Protocol
- Creates Anki decks with proper organization
- Provides web dashboard for course management
- Integrates with ChatGPT for natural language study assistance

---

## 🏗️ Architecture (Phase 2C)

```
User Request (ChatGPT)
    ↓
FastMCP Server (Python)
    ↓
Dashboard/API (Node.js)
    ↓
Anki Integration
    ↓
Study Files (C:\PT School)
```

**Components:**
- **Blackboard Agent** (core/agent/) - Scrapes UTMB portal for courses, modules, announcements, due dates
- **Card Generator** (core/drcodept_v0.1/) - Converts study material to Anki flashcards using PERRIO Protocol v6.4
- **FastMCP Server** (tools/anatomy_mcp/) - Bridges ChatGPT to card creation & storage
- **Dashboard & API** (unified_control_center/mcp-server-unified/) - Web UI for course/deck/card management
- **Study Materials** (core/textbooks/) - Extracted textbooks, notes, diagrams

---

## 📊 Current Phase: Phase 2C - ChatGPT Bridge

**Goal:** Connect ChatGPT to the entire system via FastMCP  
**Status:** In Progress

### Completed:
✅ Blackboard automation (48 due dates extracted)  
✅ Card generation engine working  
✅ FastMCP server operational  
✅ API server built with all endpoints  
✅ Dashboard scaffolded  
✅ Anki credentials stored and ready  

### In Progress:
⏳ Smoke test Dashboard & API  
⏳ Folder reorganization (PROGRAMS, IN_DEVELOPMENT, DOCS)  
⏳ Path updates after reorganization  

### Next:
⏳ ChatGPT integration (point to FastMCP)  
⏳ Full workflow testing  
⏳ Scale to all 5 PT courses  

---

## 🎓 Five PT Courses Being Automated

1. **Legal & Ethics** (14 due dates extracted)
2. **Lifespan Development** (2 due dates extracted)
3. **Clinical Pathology** (22 due dates extracted)
4. **Human Anatomy** (6 due dates extracted)
5. **PT Examination Skills** (4 due dates extracted)

**Total Due Dates:** 48 extracted from Blackboard

---

## 🔄 Study Workflow (Vision)

1. **User asks ChatGPT:** "Generate flashcards for Anatomy Chapter 5"
2. **ChatGPT calls FastMCP:** Sends study material + format request
3. **Card Generator processes:** Uses PERRIO Protocol v6.4 to create cards
4. **FastMCP stores:** Saves cards to C:\PT School\<Course>\<Deck>\
5. **Dashboard shows:** Cards appear in UI immediately
6. **User imports:** One-click import to Anki
7. **Anki syncs:** Cards available across devices

---

## 📁 Folder Organization Strategy

**After reorganization:**

```
PROGRAMS/              ← All working code
├── blackboard-agent/
├── card-generator/
├── fastmcp-server/
└── study-materials/

IN_DEVELOPMENT/        ← What Codex is building
└── dashboard-api/

DOCS/                  ← Technical reference
└── phase_2c/

ARCHIVE/               ← Old systems (ignore)
```

**Benefit:** Clear separation of concerns. PROGRAMS = what we keep alive. IN_DEVELOPMENT = what we're building. DOCS = reference only.

---

## 🚀 Success Criteria (Phase 2C Complete)

- [ ] Dashboard & API running at localhost:3000 & :7400
- [ ] FastMCP server running at localhost:8000
- [ ] Can create course/deck/card via dashboard
- [ ] Cards saved to C:\PT School\<Course>\<Deck>\deck.json
- [ ] ChatGPT can call FastMCP addCardToDeck tool
- [ ] Import to Anki works end-to-end
- [ ] At least one full test flow: ChatGPT → FastMCP → Dashboard → Anki
- [ ] Folder reorganization complete with no broken paths

---

## 📅 Timeline

- **Phase 1-2B:** Blackboard automation + Card generation (DONE)
- **Phase 2C (NOW):** ChatGPT bridge + Dashboard (In Progress)
- **Phase 3:** Scale to all 5 courses + Advanced features
- **Phase 4:** Mobile app + Cloud sync

---

## 🔑 Key Technologies

- **Python:** Blackboard scraping, card generation, FastMCP
- **Node.js:** Dashboard API
- **Claude API:** Card generation & ChatGPT bridge
- **Anki:** Study platform
- **FastMCP:** LLM integration protocol

---

## ⚠️ Constraints & Notes

- Must not break existing Blackboard scraper
- Anki must remain the source of truth
- ChatGPT integration via FastMCP (no direct API)
- Study files always saved to C:\PT School\
- PERRIO Protocol v6.4 is the card generation framework
- Idempotency required (no duplicate cards)

---

## 📞 Contact / Owner

**Trey Tucker** (@treytucker05 Anki)  
**Status:** Actively developing  
**Last Action:** Paused Codex to reorganize folders
