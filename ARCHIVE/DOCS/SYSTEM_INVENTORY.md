# ðŸ“¦ SYSTEM_INVENTORY.md

**Last Updated:** November 13, 2025  
**Status:** Phase 2 Complete, Phase 3 Ready

---

## âœ… PRODUCTION CODE (PROGRAMS/)

### 1. blackboard-agent âœ… WORKING
**Purpose:** Scrapes UTMB Blackboard for course data and due dates  
**Status:** All handlers verified working
- `get_courses()` - All 5 courses loaded
- `get_modules()` - Course modules extracted
- `get_announcements()` - Announcements retrieved
- `get_due_dates()` - 48 dates extracted successfully

**Key Tech:** Selenium, SQLite idempotency, PyWinAuto

---

### 2. drcodept-rag ✅ WORKING
**Purpose:** RAG client for querying textbooks via AnythingLLM (RAG-only)  
**Status:** CLI ready (query, cite, upload)
- Queries with citations and page references
- Uploads documents into workspace
- Card creation handled by FastMCP server tools
- CLI: python PROGRAMS/drcodept-rag/drcodept.py

---

### 3. fastmcp-server âœ… RUNNING
**Purpose:** FastMCP bridge for Claude/ChatGPT integration  
**Location:** localhost:8000  
**Handlers Connected:**
- Blackboard handler (all methods)
- Study generation handler
- Anki integration handler

---

### 4. study-materials âœ… ORGANIZED
**Purpose:** Repository for study materials  
**Contents:**
- OCR-processed textbooks
- Course notes and summaries
- Diagram collections (~200+ KenHub charts)
- Reference materials indexed for RAG

---

## ðŸ—ï¸ IN DEVELOPMENT

### dashboard-api â³ SMOKE TEST
**Status:** Testing in progress  
**Components:**
- Express backend with 11 REST endpoints
- SQLite database for metadata
- HTML/CSS/JS frontend

---

## ðŸ“š ARCHITECTURE / SPECIFICATIONS

**ARCHITECTURE/ folder:**
- Blackboard extraction spec
- RAG system spec
- Content pipeline spec
- Integration map

**SPECIFICATIONS/ folder:**
- PDF indexing strategy
- Transcription pipeline
- Vector DB comparison

---

## ðŸ”Œ INTEGRATION MAP

```
User (Natural Language)
    â†“
Claude (Tool Use API)
    â†“
FastMCP Server (localhost:8000)
    â†“
Handlers (Blackboard, Study Gen, Anki)
    â†“
Execution (SQLite, Anki DB, File System)
    â†“
Results â†’ User / Dashboard
```

---

## ðŸ“Š DATA EXTRACTED (Phase 2)

- **Due Dates:** 48 (indexed in SQLite)
- **Courses:** 5 (Legal, Lifespan, Pathology, Anatomy, Exam Skills)
- **Modules:** 50+
- **Study Materials:** 200+ diagrams, OCR'd textbooks

---

## ðŸš€ Phase 3 Readiness

| Component | Ready? | Notes |
|-----------|--------|-------|
| Data Extraction | âœ… YES | All handlers working |
| Study Generation | âœ… YES | PERRIO tested |
| MCP Bridge | âœ… YES | Server running |
| Tool Orchestration | â³ NO | Architecture TBD |
| Dashboard | â³ PARTIAL | Smoke testing |

---

See **EXECUTION_PLAN.md** for Phase 3 implementation steps.

