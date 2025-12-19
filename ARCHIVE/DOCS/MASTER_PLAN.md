# ðŸš€ DrCodePT-Swarm: MASTER PLAN
**Last Updated**: November 12, 2025  
**Owner**: Trey Tucker  
**Status**: System Design Phase â†’ Component Specifications

---

## ðŸ“‹ PROJECT VISION

You are building a **personal AI operating system**â€”a general-purpose agent that manages your entire digital workflow while learning your preferences and keeping you organized.

**Core Problems Solving:**
- Claude/ChatGPT token limits force knowledge loss between chats
- Scattered files across multiple systems (Blackboard, local folders, cloud)
- Manual work running your study system (should be automated)
- Corrupted PDFs + image-heavy documents need intelligent indexing
- "Censored" AI responses (Ollama + Dolphin as unfiltered option)

**End State:**
You ask your agent to do something (move files, research a topic, generate study cards), it figures out the workflow across all systems, executes it with observability, learns what you need, and keeps everything organized in a searchable knowledge base.

---

## ðŸ—ï¸ SYSTEM COMPONENTS

### **1. DESKTOP AGENT**
**What it does:** Executes tasks on your computer with logic and observability (move files, create files, manage mail/to-do/GroupMe/Blackboard, etc.)

**How it works:**
- Claude/ChatGPT receives natural language instruction
- Agent breaks down task into steps
- Executes file operations, API calls, web interactions
- Reports back what it did (observability)

**Tech Stack:**
- Claude/ChatGPT as orchestrator
- Desktop Commander or similar for file/system access
- API clients for mail, to-do, GroupMe, Blackboard

**Current Status:** â³ Not started (but pieces exist: Blackboard handler, etc.)

**Next Steps:**
- Define which operations the agent can perform
- Create abstraction layer for file ops, API calls, web scraping

---

### **2. WEB SCRAPER**
**What it does:** Extract text, videos, and information from webpages â†’ feeds into RAG

**How it works:**
- Agent receives URL or search query
- Scrapes webpage (text extraction, video identification)
- Extracts structured data (links, media, metadata)
- Sends to RAG indexer

**Tech Stack:**
- BeautifulSoup, Selenium, or Firecrawl for scraping
- ffmpeg for video handling
- JSON/markdown for structured output

**Current Status:** â³ Not started

**Next Steps:**
- Specify which types of content to scrape (PDFs, videos, text, images)
- Define scraper output format for RAG

---

### **3. RAG SYSTEM (Knowledge Base)**
**What it does:** Local searchable knowledge base for your files (personal training materials, PT course content, web-scraped info). "Brain" that learns your preferences.

**How it works:**
- Documents indexed (PDFs, transcripts, web content, markdown)
- When you ask a question, agent searches RAG first
- RAG injects relevant context into LLM prompt
- Avoids token limit issues + gives you control over what's searched

**Tech Stack:**
- Vector database (Chroma, Weaviate, Pinecone, or similar)
- Embedding model (local or API-based)
- Indexer to process new documents

**Current Status:** â³ Not started

**Special Challenge:** PDFs with corrupted words + images
- Solution: Multi-stage indexing
  - OCR for text extraction (with corruption handling)
  - Vision model to extract + describe images
  - Dual indexing: text index + image descriptions
  - When searching, query both indices

**Next Steps:**
- Choose vector DB + embedding model
- Design indexing pipeline for corrupted PDFs + images
- Specify metadata (source, date, class, etc.)

---

### **4. CONTENT PIPELINE (Blackboard â†’ Organized)**
**What it does:** Automate: Blackboard download â†’ organize by module â†’ convert videos to MP4 â†’ generate transcripts â†’ index everything

**How it works:**
1. Agent pulls files from Blackboard
2. Organizes into `PTSchool/` folder by class/module
3. Videos â†’ convert to MP4 (if needed)
4. MP4 â†’ transcription (via speech-to-text tool)
5. Transcripts â†’ indexed and searchable

**Tech Stack:**
- Blackboard handler (Selenium-based, see CURRENT PROGRESS)
- ffmpeg for video conversion
- Whisper or similar for transcription
- RAG indexer for transcripts

**Current Status:** âœ… Partially done (see BLACKBOARD PROGRESS below)

**Next Steps:**
- Implement download_file() in blackboard_handler.py
- Add video conversion automation
- Add transcription automation
- Wire into RAG indexer

---

### **5. STUDY SOP PIPELINE**
**What it does:** Automate your StudySOP â†’ generate flashcards â†’ send to Anki â†’ keep organized

**How it works:**
1. Agent runs your PERRIO Protocol (Gather-Prime-Encode-Retrieve-Reinforce-Close)
2. Extracts key information from materials
3. Generates Anki cards with proper formatting
4. Sends to Anki via AnkiConnect
5. Keeps deck organized (deduped, tagged, reviewed)

**Tech Stack:**
- Your PERRIO Protocol as the logic framework
- Claude/ChatGPT to generate cards
- AnkiConnect to send cards to Anki
- Anki credentials: <YOUR_ANKI_EMAIL>

**Current Status:** âœ… Mostly done (ChatGPT + Anki integration working)

**Next Steps:**
- Integrate with RAG (only generate cards from your materials)
- Automate the entire PERRIO workflow
- Add scheduling logic (when to study what)

---

### **6. MULTI-AI ROUTER**
**What it does:** Route different tasks to different AIs based on what works best

**How it works:**
- Fact-checking, research, analysis â†’ Claude or ChatGPT
- "Unfiltered" responses, censorship bypass â†’ Ollama + Dolphin
- Long-form generation â†’ whichever has context left
- Specialized tasks â†’ task-specific model

**Tech Stack:**
- Claude API
- OpenAI ChatGPT API
- Ollama + Dolphin (local, no rate limits)
- Router logic to pick which AI based on task type

**Current Status:** â³ Not started

**Next Steps:**
- Define task types + which AI handles each
- Create router logic
- Test all three AIs in parallel

---

### **7. DASHBOARD** (Later)
**What it does:** Visual interface to see system status, manually control tasks, view RAG contents

**Current Status:** â³ Not started

**Next Steps:** Build after other components are solid

---

## ðŸ”— INTEGRATION MAP

```
User Query
    â†“
Agent (Claude/ChatGPT)
    â†“
[Decision Tree: What type of task?]
    â”œâ†’ File/System Task â†’ Desktop Agent â†’ File Ops
    â”œâ†’ Research Task â†’ Web Scraper â†’ RAG Indexer
    â”œâ†’ Question About Materials â†’ RAG Search â†’ Context Injection â†’ Multi-AI Router
    â”œâ†’ Study Task â†’ PERRIO Protocol â†’ Card Generator â†’ Anki
    â””â†’ Needs Unfiltered Response â†’ Ollama + Dolphin
    â†“
RAG (stores + searches everything)
    â†“
Output to User + Log to Master Plan
```

---

## ðŸ“Š CURRENT PROGRESS

### **BLACKBOARD EXTRACTION** âœ… Significant Progress

**What's Done:**

Core code enhancements:
- `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:153`
  - `get_courses()`: Added scroll preload, broader discovery, click-through fallback, debug prints
- `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:622`
  - `get_due_dates()`: Full BFS expansion of nested toggles, "show more/expand" clicks, async content reads, final page-text scan

Helper scripts (for testing/verification):
- `PROGRAMS/blackboard-agent/tmp_list_courses.py`: Quick course list after login
- `PROGRAMS/blackboard-agent/extract_course_urls.py`: Auto-collect outline URLs from Courses view
- `PROGRAMS/blackboard-agent/interactive_track_courses.py`: Manual course tracking (you click, it records URLs to COURSE_URLS.txt)
- `PROGRAMS/blackboard-agent/extract_due_dates_from_list.py`: Visit saved URLs, extract due dates (raw + normalized)
- `PROGRAMS/blackboard-agent/test_end_to_end.py`: Non-interactive E2E harness (login â†’ courses â†’ due dates)

Documentation:
- `BLACKBOARD_SCRAPER_STATUS.md`: Concise status of fixes, outputs, next steps
- `BLACKBOARD_FILE_DOWNLOAD_AUDIT.md`: Audit + update on scroll/BFS enhancements + remaining work

Outputs captured:
- `PROGRAMS/blackboard-agent/COURSE_URLS.txt`: 5 course outline URLs (captured interactively)
- `PROGRAMS/blackboard-agent/COURSE_DUE_DATES.txt`: Raw per-course due dates (post-BFS expansion)
- `PROGRAMS/blackboard-agent/COURSE_DUE_DATES_NORMALIZED.txt`: Deduped/normalized due dates
- `TEST_RESULTS_SCROLL_FIX.txt`: Course counts + initial due-date totals after scroll fix

**Results:**
- âœ… 48 due dates extracted from all 5 courses (Legal 14, Lifespan 2, Pathology 22, Anatomy 6, Exam Skills 4)
- âœ… Course discovery working with fallback logic
- âœ… Nested toggle expansion working (BFS)
- âœ… Robust extraction pipeline established

**What's Left (Next Steps for Blackboard):**

1. **Implement Downloads** (CRITICAL)
   - Add `download_file()` / `download_course_materials()` in `blackboard_handler.py`
   - Configure Chrome download prefs + wait-for-completion logic
   - Expose `blackboard_download_files` tool in `claude_handler.py`

2. **Course Discovery Robustness**
   - Add "All Courses/All Terms" filter toggle in `get_courses()`

3. **Due Dates Completeness**
   - Add targeted DOM parsing for assignment/quiz rows outside folder toggles
   - Extend `get_due_dates()` in handler

4. **Security**
   - Remove hard-coded credential fallbacks in handler
   - Rely only on env vars

---

### **OTHER COMPONENTS**

- **Web Scraper**: â³ Not started
- **RAG System**: â³ Not started (need to design indexing for corrupted PDFs + images)
- **Desktop Agent**: â³ Not started (framework exists, needs expansion)
- **Study SOP Pipeline**: âœ… ChatGPT + Anki integration working (needs RAG integration)
- **Multi-AI Router**: â³ Not started
- **Dashboard**: â³ Not started

---

## ðŸŽ¯ NEXT IMMEDIATE STEPS

**Phase 1: Finish Blackboard (You're 80% Done)**
1. Implement `download_file()` + `download_course_materials()` 
2. Test end-to-end: Login â†’ Get Courses â†’ Get Due Dates â†’ **Download Files**
3. Wire into Desktop Agent so you can say: "Agent, get all my Pathology materials from Blackboard"

**Phase 2: Design RAG System**
1. Choose vector DB + embedding model
2. Design indexing strategy for corrupted PDFs + images
3. Create indexer tool to add documents to RAG

**Phase 3: Wire RAG + Study SOP**
1. Connect RAG search to PERRIO protocol
2. Generate cards only from your indexed materials
3. Auto-send to Anki

**Phase 4: Multi-AI Router**
1. Define task â†’ AI routing logic
2. Implement fallback (if Claude out of tokens â†’ ChatGPT or Ollama)

---

## ðŸ“ NOTES & DECISIONS

- **Master Plan Location**: This file stays at `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\MASTER_PLAN.md`
- **Update Rule**: Each chat, Claude updates this file with progress + next steps. No work gets lost.
- **Single Source of Truth**: This file is THE reference. No scattered docs.
- **Token Overflow Fix**: New chats read this file first â†’ know exactly where you left off

---

## ðŸ”„ HOW TO USE THIS FILE

1. **New Chat Starts**: "Hey Claude, read my Master Plan and tell me where we are"
2. **Claude Reads File**: Understands project, status, what's done/what's left
3. **Continue Work**: "Next, let's implement Blackboard downloads" or "Let's design the RAG system"
4. **Claude Edits File**: Updates CURRENT PROGRESS + NEXT IMMEDIATE STEPS
5. **Close Chat**: Master Plan reflects where you left off
6. **Next Chat**: Repeat step 1

---

**Last Updated By**: Claude (November 12, 2025)  
**Next Update**: After Phase 1 Blackboard work completes
 
---


## FILE ORGANIZATION - What's Active, What's Archived

**November 13, 2025 Cleanup**: All scattered .md files have been consolidated into organized structure.

### ACTIVE FILES (Keep in Root)

Only **2 files** should exist in root:
- **MASTER_PLAN.md** -- System architecture, vision, progress tracking
- **CODEX.md** -- Operational instructions, tool references, credentials

### ACTIVE DIRECTORIES

| Directory | Purpose | Status |
|-----------|---------|--------|
| **ARCHITECTURE/** | 6 core system specs | KEEP |
| **SPECIFICATIONS/** | 3 implementation specs | KEEP |
| **PROGRAMS/** | Working code components | KEEP |
| **Codex Tasks/** | Coordination hub | KEEP |
| **IN_DEVELOPMENT/** | Active projects | KEEP |
| **_ARCHIVE/** | Pre-cleanup reference | KEEP for reference |

### ARCHIVED (OLD_ARCHIVE folder)

**10 Root-Level .md Files Moved:**
- ACTIVE_ROADMAP.md, CODEX_V2.md, MASTER_PLAN_OPTION_B_UPDATE.md
- BLACKBOARD_SCRAPER_STATUS.md, BLACKBOARD_AGENT_TEST_REPORT.md, and 5 others

**4 Old Directories Moved:**
- _MASTER_DOCS/, DOCS/, HALF_A_FINDINGS/, IMPLEMENTATION/

See **FILE_MANIFEST.md** for complete inventory (what's active, what's archived, and why).

---
## ðŸ“š DETAILED SPECIFICATIONS (Added Nov 13)

- ARCHITECTURE/1_BLACKBOARD_DOWNLOAD_SPEC.md â€” Download discovery, Chrome prefs, completion detection, integration points
- ARCHITECTURE/2_RAG_SYSTEM_SPEC.md â€” Architecture, data model, retrieval flow, decisions
- SPECIFICATIONS/PDF_INDEXING_STRATEGY.md â€” OCR fallback, captions, normalization, chunking
- SPECIFICATIONS/VECTOR_DB_COMPARISON.md â€” Decision matrix; recommendation: Chroma
- ARCHITECTURE/3_CONTENT_PIPELINE_SPEC.md â€” Endâ€‘toâ€‘end from downloads to RAG
- SPECIFICATIONS/TRANSCRIPTION_PIPELINE.md â€” fasterâ€‘whisper workflow and outputs

## âœ… DECISIONS MADE (Architecture Phase)
- Vector DB: Chroma (localâ€‘first); adapter path to Weaviate/Milvus later
- Embedding Model: BAAI/bge-small-en-v1.5 (local); alt `e5-base-v2`
- OCR: Tesseract via PyMuPDF renders @ 300â€“400 DPI
- Image Captions: BLIP locally; optional Claude Vision when online
- Video/Audio: ffmpeg + faster-whisper with SRT + TXT outputs

## ðŸ“Œ STATUS UPDATES (Nov 13)
- RAG System: Design complete; implementation pending
- Content Pipeline: Design complete; implementation pending
- Blackboard Downloads: Spec complete; ready to implement

