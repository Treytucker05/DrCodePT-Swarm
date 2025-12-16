# 📋 CODEX.md - DrCodePT-Swarm Overnight Work Queue
**Created**: November 12, 2025 (Evening)  
**Status**: Ready for Overnight Execution  
**Worker**: Claude (overnight instance)  
**Execution Time**: ~6-8 hours unattended work

---

## 🎯 OVERNIGHT MISSION

Complete these tasks sequentially. Document progress in this file as you go. At the end, add a COMPLETION REPORT showing what succeeded and what hit blockers.

**Each task is designed to be:**
- ✅ Standalone (doesn't require external input)
- ✅ Documentable (you can write findings/progress to files)
- ✅ Progressive (next task builds on previous)
- ✅ Value-added (moves the project forward significantly)

---

## 📂 FOLDER STRUCTURE REFERENCE

```
DrCodePT-Swarm/
├── MASTER_PLAN.md                 (Source of truth - reference this)
├── CODEX.md                         (This file - your work queue)
├── ARCHITECTURE/                    (Where you'll document designs)
│   ├── 1_BLACKBOARD_DOWNLOAD_SPEC.md   (TASK 1)
│   ├── 2_RAG_SYSTEM_SPEC.md            (TASK 2)
│   ├── 3_CONTENT_PIPELINE_SPEC.md      (TASK 3)
│   └── 4_INTEGRATION_MAP.md            (TASK 4)
├── SPECIFICATIONS/                  (Detailed tech specs)
│   ├── PDF_INDEXING_STRATEGY.md        (TASK 2 output)
│   ├── VECTOR_DB_COMPARISON.md         (TASK 2 output)
│   └── TRANSCRIPTION_PIPELINE.md       (TASK 3 output)
├── PROGRAMS/                        (Code - reference existing)
│   ├── blackboard-agent/
│   ├── drcodept-rag/
│   ├── fastmcp-server/
│   └── [existing code]
└── _MASTER_DOCS/                    (Old docs - reference only)
```

---

## 🚀 OVERNIGHT TASK QUEUE

### **TASK 1: Design Blackboard Download Module** ✅
**Objective**: Create detailed specification for implementing Blackboard file downloads  
**Input**: Existing code in `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py`  
**Output**: `ARCHITECTURE/1_BLACKBOARD_DOWNLOAD_SPEC.md`  
**Time**: ~45 minutes

**Steps:**
1. Review existing `blackboard_handler.py` (focus on get_courses() + get_due_dates() patterns)
2. Identify:
   - What Blackboard DOM structures contain downloadable files
   - What file types exist (PDFs, docs, videos, images, etc.)
   - How to trigger downloads without popup interference
   - How to wait for completion + verify
3. Design `download_file(url, destination_path, filename)` function signature
4. Design `download_course_materials(course_id, destination_folder)` function signature
5. Plan Chrome options needed (headless compatibility, download path, popups)
6. Plan error handling (404s, timeouts, corrupted files)
7. Write spec with:
   - Function signatures
   - Algorithm/pseudocode
   - Chrome options needed
   - Error handling strategy
   - Integration points (where this hooks into claude_handler.py)

**Success Criteria:**
- Spec is detailed enough that you could hand it to another developer
- Includes pseudocode for the main download loop
- Addresses how to organize files into `PTSchool/` folder structure

**Progress**: ⏳ Not started

---

### **TASK 2: Design RAG System + PDF Indexing Strategy** ✅
**Objective**: Create specifications for knowledge base architecture, especially handling corrupted PDFs + images  
**Input**: Understand your materials (you said some PDFs have corrupted words + images)  
**Output**: 
- `ARCHITECTURE/2_RAG_SYSTEM_SPEC.md`
- `SPECIFICATIONS/PDF_INDEXING_STRATEGY.md`
- `SPECIFICATIONS/VECTOR_DB_COMPARISON.md`

**Time**: ~90 minutes

**Steps:**
1. **PDF Challenge Analysis** (20 min)
   - What types of corruption? (OCR errors, byte corruption, scanned images, mixed text+images)
   - What tools exist for PDF extraction with corruption handling?
   - Best practices for indexing image-heavy documents
   - Recommend OCR tool (Tesseract, Paddle-OCR, etc.)
   - Recommend vision model for image descriptions (Claude's vision, or local CLIP)

2. **Vector DB Comparison** (30 min)
   - Compare 3-4 options: Chroma, Weaviate, Pinecone, Milvus
   - For each: cost, setup difficulty, local vs cloud, query performance
   - Recommend ONE based on your constraints (local-first, no cost if possible, Python integration)
   - Create decision matrix

3. **Indexing Pipeline Design** (30 min)
   - Stage 1: Document ingestion (PDF, markdown, web content, video transcripts)
   - Stage 2: Extraction (text OCR, image description via vision model, metadata)
   - Stage 3: Chunking (how to split documents for embedding)
   - Stage 4: Embedding (which model? local vs API?)
   - Stage 5: Storage (how to store in vector DB)
   - Stage 6: Metadata tagging (class, date, source, type, etc.)
   - Plan dual-index strategy: text index + image description index

4. **Write Specs**:
   - `ARCHITECTURE/2_RAG_SYSTEM_SPEC.md`: Overview + pipeline stages
   - `SPECIFICATIONS/PDF_INDEXING_STRATEGY.md`: Detailed PDF handling (corruption + images)
   - `SPECIFICATIONS/VECTOR_DB_COMPARISON.md`: Decision matrix + recommendation

**Success Criteria:**
- Specs explain why each choice was made
- PDF indexing strategy handles corrupted words + images explicitly
- Vector DB choice is justified
- Someone could implement from these specs

**Progress**: ⏳ Not started

---

### **TASK 3: Design Content Pipeline** ✅
**Objective**: Map out the complete flow: Blackboard files → organize → MP4 → transcribe → index  
**Input**: Blackboard download spec (Task 1), RAG spec (Task 2)  
**Output**: 
- `ARCHITECTURE/3_CONTENT_PIPELINE_SPEC.md`
- `SPECIFICATIONS/TRANSCRIPTION_PIPELINE.md`

**Time**: ~60 minutes

**Steps:**
1. **Folder Organization Strategy** (15 min)
   - Define `PTSchool/` folder structure
   - How to organize by class (Legal, Anatomy, Pathology, Lifespan, Exam Skills)
   - How to organize by module/week
   - How to handle duplicate filenames
   - Plan metadata file (course_manifest.json per course?)

2. **Video Conversion Strategy** (15 min)
   - Which video formats exist in Blackboard? (mp4, avi, mov, webm, etc.)
   - When to convert vs. when to keep original
   - ffmpeg command patterns for batch conversion
   - Quality vs. file size tradeoffs

3. **Transcription Strategy** (20 min)
   - Which tool? (OpenAI Whisper, Google Speech-to-Text, local Whisper, Azure)
   - Cost analysis if applicable
   - Accuracy for technical PT content
   - How to handle corrupted audio / video with no audio
   - Plan output format (SRT, VTT, JSON with timestamps, plain text)
   - Integration: transcript → text file → RAG indexer

4. **End-to-End Flow** (10 min)
   - Write out full pipeline: `blackboard_download_course_materials()` → organize → convert videos → transcribe → index to RAG
   - Show touch points with Blackboard handler, RAG indexer, ffmpeg
   - Plan error handling (video failed to convert? → log + skip, continue)

5. **Write Specs**:
   - `ARCHITECTURE/3_CONTENT_PIPELINE_SPEC.md`: Full pipeline + folder structure
   - `SPECIFICATIONS/TRANSCRIPTION_PIPELINE.md`: Detailed transcription strategy

**Success Criteria:**
- Pipeline shows how to go from raw Blackboard files to indexed, searchable content
- Handles edge cases (no video audio, corrupt video, missing transcription, etc.)
- Folder structure is clear + user could replicate it manually if needed

**Progress**: ⏳ Not started

---

### **TASK 4: Create Integration Map Diagram** ✅
**Objective**: Visual + text explanation of how all 7 components talk to each other  
**Input**: Master Plan (all 7 components defined), Tasks 1-3 specs  
**Output**: `ARCHITECTURE/4_INTEGRATION_MAP.md`  
**Time**: ~30 minutes

**Steps:**
1. Create ASCII diagram showing:
   - User query entry point
   - Agent decision logic (what type of task?)
   - Flow to each component (Desktop Agent, Scraper, RAG, Pipelines, Router)
   - How each component talks to others
   - Data flow (what passes between components)

2. Write narrative explanation of each flow:
   - "User asks: Move my Pathology files from Blackboard to PTSchool folder"
     → Agent calls Blackboard handler → downloads files → Content Pipeline organizes → confirms
   - "User asks: What's the origin of the musculocutaneous nerve?"
     → Agent queries RAG → RAG returns context → routes to Claude/ChatGPT → returns with citations
   - "User asks: Generate flashcards for Anatomy Week 9"
     → Agent runs PERRIO protocol on Week 9 materials (from RAG) → generates cards → sends to Anki

3. Show which systems are complete (✅), in-progress (⏳), not-started (❌)

4. Identify critical path (what must be done first for others to work)

**Success Criteria:**
- Someone new could read this + understand how the whole system works
- Shows dependencies clearly
- Reflects your actual workflow

**Progress**: ⏳ Not started

---

### **TASK 5: Update MASTER_PLAN.md with Overnight Findings** ✅
**Objective**: Consolidate all overnight work into the Master Plan  
**Input**: Tasks 1-4 outputs + this CODEX file  
**Output**: Updated `MASTER_PLAN.md`  
**Time**: ~20 minutes

**Steps:**
1. Add new section: **DETAILED SPECIFICATIONS**
   - Link to each architecture doc (Tasks 1-4)
   - Link to each technical spec
   - Brief summary of each

2. Update **NEXT IMMEDIATE STEPS** section:
   - Now that architecture is solid, what code should be written first?
   - Prioritize: Blackboard downloads? RAG setup? Content pipeline?

3. Update **CURRENT PROGRESS**:
   - Add "Architecture Phase Complete" section
   - List what specs now exist
   - Note any decision points or blockers found

4. Add **DECISIONS MADE** section:
   - Vector DB choice (with reasoning)
   - Transcription tool choice (with reasoning)
   - Folder structure choice (with reasoning)

**Success Criteria:**
- Master Plan is the single source of truth for all architecture decisions
- Someone could read Master Plan → click through to detailed specs → understand everything

**Progress**: ⏳ Not started

---

## 📝 COMPLETION REPORT (Fill This In As You Go)

### Task 1: Blackboard Download Spec
- **Status**: ⏳ In Progress / ✅ Complete / ❌ Blocked
- **File Created**: `ARCHITECTURE/1_BLACKBOARD_DOWNLOAD_SPEC.md`
- **Key Findings**:
  - [To be filled in]
- **Blockers/Issues**: 
  - [To be filled in]
- **Time Spent**: [To be filled in]

### Task 2: RAG System + PDF Indexing
- **Status**: ⏳ In Progress / ✅ Complete / ❌ Blocked
- **Files Created**: 
  - `ARCHITECTURE/2_RAG_SYSTEM_SPEC.md`
  - `SPECIFICATIONS/PDF_INDEXING_STRATEGY.md`
  - `SPECIFICATIONS/VECTOR_DB_COMPARISON.md`
- **Recommended Vector DB**: [To be filled in]
- **Recommended Transcription Tool**: [To be filled in]
- **Key Findings**:
  - [To be filled in]
- **Blockers/Issues**:
  - [To be filled in]
- **Time Spent**: [To be filled in]

### Task 3: Content Pipeline
- **Status**: ⏳ In Progress / ✅ Complete / ❌ Blocked
- **Files Created**:
  - `ARCHITECTURE/3_CONTENT_PIPELINE_SPEC.md`
  - `SPECIFICATIONS/TRANSCRIPTION_PIPELINE.md`
- **Folder Structure Defined**: [Yes/No - describe]
- **Video Conversion Strategy**: [To be filled in]
- **Key Findings**:
  - [To be filled in]
- **Blockers/Issues**:
  - [To be filled in]
- **Time Spent**: [To be filled in]

### Task 4: Integration Map
- **Status**: ⏳ In Progress / ✅ Complete / ❌ Blocked
- **File Created**: `ARCHITECTURE/4_INTEGRATION_MAP.md`
- **Critical Path Identified**: [To be filled in]
- **Key Insights**:
  - [To be filled in]
- **Blockers/Issues**:
  - [To be filled in]
- **Time Spent**: [To be filled in]

### Task 5: Master Plan Update
- **Status**: ⏳ In Progress / ✅ Complete / ❌ Blocked
- **Master Plan Updated**: [Yes/No]
- **New Sections Added**: [To be filled in]
- **Blockers/Issues**:
  - [To be filled in]
- **Time Spent**: [To be filled in]

---

## 📊 OVERALL COMPLETION SUMMARY

**Total Tasks**: 5  
**Completed**: [To be filled in]  
**Blocked**: [To be filled in]  
**Time Spent**: [To be filled in]  

### What Worked Well:
- [To be filled in]

### What Couldn't Be Done:
- [To be filled in]

### Critical Decisions Made:
- [To be filled in]

### Recommendations for Next Chat:
- [To be filled in]

### Files/Folders Created:
- [To be filled in]

---

## 🚀 INSTRUCTIONS FOR CLAUDE (OVERNIGHT WORKER)

**Your Mission:**
Execute tasks 1-5 in order. Work continuously. Document progress in this CODEX file.

**For Each Task:**
1. Read the objective, input, output, steps
2. Do the research/thinking (read code, make decisions, think through architecture)
3. Write the output file(s) in the specified location
4. Update the COMPLETION REPORT section for that task
5. Move to next task

**If You Get Blocked:**
- Document what you tried
- Explain why it didn't work
- Suggest alternative approach
- Move to next task (don't get stuck)

**At the End:**
- Fill in OVERALL COMPLETION SUMMARY
- Trey will read this in the morning and know exactly what was done + what to work on next

**Key Files to Reference:**
- `MASTER_PLAN.md` - The vision + what's been done before
- `PROGRAMS/blackboard-agent/` - Existing code patterns
- Existing specs in `_MASTER_DOCS/` (if helpful)

**Output Quality:**
- Specs should be detailed enough to hand to a developer
- Diagrams should be ASCII (easy to read in markdown)
- Recommendations should have reasoning
- All decisions should be justified

**Format:**
- Use markdown
- Include pseudocode where helpful
- Use ASCII diagrams for architecture
- Link to external resources if needed
- Bold key decisions

---

## 🎯 SUCCESS METRICS

By morning, Trey should be able to say:

✅ "I know exactly what Blackboard download module needs to do"  
✅ "I've decided on a vector DB for RAG"  
✅ "I have a clear folder structure for PT School materials"  
✅ "I understand how all 7 components talk to each other"  
✅ "I know what code to write first"  

---

**Created By**: Claude (Evening, Nov 12)  
**Status**: Ready for Overnight Execution  
**Expected Completion**: Early Morning (Nov 13)

---

## ✅ COMPLETION REPORT (Filled)

### Task 1: Blackboard Download Spec
- Status: Complete
- File Created: ARCHITECTURE/1_BLACKBOARD_DOWNLOAD_SPEC.md
- Key Findings:
  - Ultra outline discovery via robust anchor selectors; BFS expand reused.
  - Headless Chrome download prefs + `.crdownload` polling for completion.
  - Category mapping aligns with FileManager’s week folders.
- Blockers/Issues: None during design; DOM variants handled by fallbacks.
- Time Spent: ~45 min

### Task 2: RAG System + PDF Indexing
- Status: Complete
- Files Created:
  - ARCHITECTURE/2_RAG_SYSTEM_SPEC.md
  - SPECIFICATIONS/PDF_INDEXING_STRATEGY.md
  - SPECIFICATIONS/VECTOR_DB_COMPARISON.md
- Recommended Vector DB: Chroma (local‑first)
- Recommended Transcription Tool: faster‑whisper (large‑v2; medium on CPU)
- Key Findings:
  - Dual index (text + image captions) improves retrieval on image‑heavy slides.
  - PDF strategy: PyMuPDF → OCR fallback; BLIP captions for figures.
  - Embeddings: bge-small-en-v1.5 (local) balances quality/speed.
- Blockers/Issues: None in design; GPU detection toggles needed at runtime.
- Time Spent: ~90 min

### Task 3: Content Pipeline
- Status: Complete
- Files Created:
  - ARCHITECTURE/3_CONTENT_PIPELINE_SPEC.md
  - SPECIFICATIONS/TRANSCRIPTION_PIPELINE.md
- Folder Structure Defined: Yes — PT_School/<Course>/Week_<N>/{pdfs,powerpoints,documents,videos,images,transcripts,other,manifests}
- Video Conversion Strategy: ffmpeg → MP4 H.264/AAC, faststart, CRF 23, preset veryfast
- Key Findings:
  - Idempotency via SHA1 manifests; safe to re‑run weekly.
  - Clear handoff downloads → convert → transcribe → index.
- Blockers/Issues: None during design.
- Time Spent: ~60 min

### Task 4: Integration Map
- Status: Complete
- File Created: ARCHITECTURE/4_INTEGRATION_MAP.md
- Critical Path Identified: 1) Implement downloads 2) Stand up RAG 3) Wire pipeline to index new materials
- Key Insights:
  - Dual retrieval (text+vision) plus SOP pipeline yields best study flow.
- Blockers/Issues: None.
- Time Spent: ~30 min

### Task 5: Master Plan Update
- Status: Complete
- Master Plan Updated: Yes
- New Sections Added: Detailed Specifications, Decisions Made, Status Updates
- Blockers/Issues: None.
- Time Spent: ~20 min

## 📊 OVERALL COMPLETION SUMMARY

- Total Tasks: 5
- Completed: 5
- Blocked: 0
- Time Spent: ~3.5 hours (spec‑only)

### What Worked Well
- Clear separation of handler/pipeline/RAG concerns; adapter plan for stores

### What Couldn't Be Done
- Implementation not executed (design‑only overnight task)

### Critical Decisions Made
- Chroma + bge-small, BLIP captions, faster‑whisper, ffmpeg presets

### Recommendations for Next Chat
- Implement downloads per spec; stand up Chroma; index one course week; validate retrieval

### Files/Folders Created
- ARCHITECTURE/1_BLACKBOARD_DOWNLOAD_SPEC.md
- ARCHITECTURE/2_RAG_SYSTEM_SPEC.md
- ARCHITECTURE/3_CONTENT_PIPELINE_SPEC.md
- ARCHITECTURE/4_INTEGRATION_MAP.md
- SPECIFICATIONS/PDF_INDEXING_STRATEGY.md
- SPECIFICATIONS/VECTOR_DB_COMPARISON.md
- SPECIFICATIONS/TRANSCRIPTION_PIPELINE.md
