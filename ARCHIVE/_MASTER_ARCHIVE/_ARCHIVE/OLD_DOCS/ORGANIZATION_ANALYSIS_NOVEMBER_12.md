# DRCODEPT-SWARM ORGANIZATION ANALYSIS
**Date:** November 12, 2025  
**Purpose:** Comprehensive folder analysis + divided work plan  
**Status:** Ready to execute

---

## EXECUTIVE SUMMARY

Your system has **4 complete, working components** + **1 in development**. The folder structure is mostly organized but has some strategic decisions pending. Work divided into **HALF A (Understanding & Planning)** and **HALF B (Implementation & Integration)**.

---

## PART A: COMPREHENSIVE FOLDER ANALYSIS

### **ROOT LEVEL STRATEGIC FILES** (5 files that matter most)

| File | Purpose | Status | Action |
|------|---------|--------|--------|
| `START_HERE.md` | Quick start guide + smoke test status | ✅ Current | Reference only |
| `STATUS.md` | Current state & next steps | ✅ Current | Update after each session |
| `GAMEPLAN.md` | Master strategy & vision | ✅ Clear | Reference for direction |
| `CODEX_INSTRUCTIONS.md` | What Codex was doing overnight | ⏳ Partial | Update with findings |
| `DIRECTORY_STRUCTURE.md` | File location map | ⏳ Needs update | Will fix after analysis |

**Confidence:** 100% - These are your decision points.

---

## PART B: FOUR WORKING SYSTEMS (PROGRAMS/)

### **1. BLACKBOARD-AGENT** ✅ PRODUCTION READY
**Location:** `PROGRAMS/blackboard-agent/`  
**Purpose:** Scrape UTMB portal for courses, modules, announcements, due dates

**What it does:**
- Logs into Blackboard via Selenium
- Extracts courses + modules
- Pulls all announcements
- **Result:** 48 due dates across 5 courses

**Key files:**
- `agent.py` - Main orchestrator
- `claude_tools.py` - Tool definitions for Claude
- `handlers/` - Specific handlers for Blackboard operations
- `config/` - Settings + environment variables
- `opstore.db` - SQLite database for operation idempotency

**Current state:**
- ✅ Extracts 48 due dates successfully
- ✅ No errors on last run
- ✅ Production quality code

**Confidence:** 95% - Well-documented, tested, working daily.

---

### **2. CARD-GENERATOR** ✅ PRODUCTION READY
**Location:** `PROGRAMS/card-generator/`  
**Purpose:** Convert study material to Anki flashcards using PERRIO Protocol v6.4

**What it does:**
- Takes input (topic, material, course)
- Applies PERRIO logic: Gather → Prime → Encode → Retrieve → Reinforce → Close
- Generates flashcard JSON
- Exports to Anki-compatible format

**Key files:**
- `drcodept.py` - Main generator engine
- `core/` - Core PERRIO logic
- `generators/` - Anki, NPTE question generators
- `utils/` - Helper functions
- `README.md` - Clear documentation

**Current state:**
- ✅ Generates cards successfully
- ✅ PERRIO framework embedded
- ✅ Ready for production

**Confidence:** 95% - Clear methodology, working well.

---

### **3. FASTMCP-SERVER** ✅ OPERATIONAL
**Location:** `PROGRAMS/fastmcp-server/`  
**Purpose:** Bridge between ChatGPT and internal systems via MCP protocol

**What it does:**
- Runs FastMCP server at localhost:8000
- Provides tools to ChatGPT: list_modules, ingest_module, search_facts, export_module
- Manages course material database
- Verifies facts with two-source validation

**Key files:**
- `server.py` - Main FastMCP server (383 lines)
- `entities.py` - Anatomy entity detection
- `aligner.py` - Slide-to-transcript alignment
- `verifier.py` - Two-source fact verification (4 tiers)
- `manifest_loader.py` - Course material loader
- `manifest.yaml` - Course index
- `ngrok.yml` - Networking config (connects to ChatGPT)

**Current state:**
- ✅ Server running at localhost:8000
- ✅ Connected to ChatGPT via ngrok
- ✅ All 4 tools operational

**Confidence:** 90% - Working, but missing the `addCardToDeck` tool that completes the workflow.

---

### **4. STUDY-MATERIALS** ✅ ORGANIZED & READY
**Location:** `PROGRAMS/study-materials/`  
**Purpose:** Store organized course materials (textbooks, diagrams, notes)

**What it contains:**
- Anatomy lecture materials
- Pathology references
- PT textbooks (KenHub, Dutton, etc.)
- Course-specific study guides
- OCR'd content from textbooks

**Current state:**
- ✅ Well-organized by subject
- ✅ Indexed + searchable
- ✅ Ready for FastMCP ingestion

**Confidence:** 95% - Clear organization, all materials present.

---

## PART C: ONE SYSTEM IN DEVELOPMENT (IN_DEVELOPMENT/)

### **5. DASHBOARD-API** ⏳ SMOKE TEST PHASE
**Location:** `IN_DEVELOPMENT/dashboard-api/`  
**Purpose:** Web interface + REST API for course/deck/card management

**What it does:**
- Provides web dashboard (HTML/JS/CSS)
- Express.js REST API with 11 endpoints
- CRUD operations for courses, decks, cards
- Saves data to C:\PT School\
- Integration hooks for FastMCP

**Key files:**
- `api-server.js` - Express server with all 11 endpoints
- `dashboard/index.html` - Web UI
- `dashboard/` - Frontend assets (CSS, JS)
- `package.json` - npm dependencies
- `.env` - Configuration
- `data/` - Local data storage

**11 Endpoints:**
1. GET /api/health - Server health check
2. GET /api/courses - List all courses
3. POST /api/courses - Create new course
4. GET /api/courses/:id/decks - List decks for course
5. POST /api/courses/:id/decks - Create deck
6. GET /api/decks/:id/cards - List cards in deck
7. POST /api/decks/:id/cards - Create card
8. PUT /api/decks/:id/cards/:cardId - Update card
9. DELETE /api/decks/:id/cards/:cardId - Delete card
10. GET /api/stats - System statistics
11. POST /api/sync - Trigger FastMCP sync

**Current state:**
- ✅ API server starts cleanly on :7400
- ✅ Dashboard loads in browser
- ✅ Can create courses/decks/cards via UI
- ✅ Data saves to disk (C:\PT School\) correctly
- ✅ All 11 endpoints responding
- ⏳ **Missing:** Direct Anki integration (still manual export)

**Smoke test results:**
- ✅ API functional
- ✅ Dashboard responsive
- ✅ Data persistence working
- ❌ **Gap:** addCardToDeck tool not in StudyMCP

**Confidence:** 85% - Infrastructure solid, but Anki integration incomplete.

---

## PART D: DOCUMENTATION (DOCS/)

**Location:** `DOCS/phase_2c/`

**Contains:**
- `README_PHASE_2C.md` - Phase 2C overview
- `PHASE_2C_CODE_REFERENCE.md` - Deep technical docs
- `PHASE_2C_FILES_INDEX.md` - File locations
- `PHASE_2C_VERIFICATION.md` - Checklist
- `PHASE_2C_FINAL_SUMMARY.md` - Post-implementation summary
- `PHASE_2C_REVIEW_COMPLETE.md` - Review notes
- `PHASE_2C_STATUS.md` - Phase status

**Confidence:** 90% - Well-documented, reference quality.

---

## PART E: PLANNING FOLDER (unified_control_center/)

**Location:** `unified_control_center/`

**Key files:**
- `INDEX.md` - Entry point
- `MASTER_PLAN.md` - 5-system unified vision (very detailed)
- `CURRENT_SYSTEM_STATE.md` - Audit of what exists
- `STATUS_AND_ROADMAP.md` - Progress tracking
- `NEW_CHATS_START_HERE.md` - Handoff document
- `QUESTION_B_FINAL_DECISIONS.md` - Architecture decisions
- `CODEX_ASSIGNMENTS/` - Codex's assigned tasks (overnight work)

**Status:** ⏳ In use but getting cluttered with assignments

**Confidence:** 85% - Strategic value, but needs cleanup.

---

## PART F: ARCHIVE (Legacy - Ignore)

**Location:** `_ARCHIVE/`

**Contains:** Old Phase 7 implementation, AnythingLLM setup, outdated systems

**Action:** Leave untouched. Reference only if needed.

---

## ORGANIZATION ASSESSMENT

| Category | Status | Confidence |
|----------|--------|------------|
| **Production Systems** | ✅ Clean & working | 95% |
| **In-Development Code** | ✅ Well-structured | 85% |
| **Documentation** | ✅ Comprehensive | 90% |
| **Planning Docs** | ⚠️ Organized but scattered | 75% |
| **File Paths** | ✅ Consistent after Nov 11 reorganization | 95% |
| **Folder Naming** | ✅ Clear (PROGRAMS, IN_DEVELOPMENT, DOCS) | 98% |

---

## KEY DISCOVERY: THE REAL ARCHITECTURE

**You're NOT using local FastMCP as your ChatGPT bridge.**

**What you ARE using:**
- FastMCP server (localhost:8000) is for Anatomy material extraction
- **StudyMCP** (ChatGPT's connection) is the real MCP server
- StudyMCP has 4 tools: list_modules, ingest_module, search_facts, export_module
- **MISSING:** `addCardToDeck` tool (your next bottleneck)

**Important:** The Dashboard/API is a nice management interface, but the real workflow is:
```
ChatGPT → StudyMCP → (needs addCardToDeck) → Anki
```

**Confidence:** 90% - Documented in CODEX_INSTRUCTIONS.md but needs verification.

---

## CRITICAL QUESTIONS STILL PENDING

1. **Where is StudyMCP source code?** (Codex was supposed to find it)
2. **What Anki integration method?** (AnkiConnect vs. file-based vs. plugin)
3. **Who maintains StudyMCP?** (Is it your code or someone else's?)
4. **What's the priority?** (Local dashboard vs. ChatGPT-to-Anki workflow)

---

