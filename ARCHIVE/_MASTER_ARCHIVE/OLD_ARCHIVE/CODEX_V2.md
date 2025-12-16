# 📋 CODEX_V2.md - DrCodePT-Swarm Revised Overnight Work Queue
**Created**: November 13, 2025 (Revised from Original CODEX)  
**Status**: Ready for Overnight Execution  
**CHANGE**: ❌ Chroma → ✅ AnythingLLM + Ollama/Dolphin (Unrestricted RAG)
**Worker**: Claude (overnight instance)  
**Execution Time**: ~6-8 hours unattended work

---

## 🎯 OVERNIGHT MISSION (REVISED)

Complete these tasks sequentially. Document progress in this file as you go. At the end, add a COMPLETION REPORT showing what succeeded and what hit blockers.

**Key Insight:** You already have Dr. CodePT v0.1 (CLI) and Anatomy MCP working. This overnight work is about documenting the EXISTING AnythingLLM/Ollama infrastructure and creating a unified launch system.

---

## 🚀 OVERNIGHT TASK QUEUE (REVISED)

### **TASK 1: Verify & Document LAUNCH.bat** ✅
**Objective**: Create unified launcher that starts: Docker → Ollama → AnythingLLM → Syncthing
**Input**: Existing START_DRCODEPT.bat + START_CODEX.bat patterns  
**Output**: `LAUNCH.bat` (new file in root)  
**Time**: ~30 minutes

**Steps:**
1. Document what LAUNCH.bat SHOULD do:
   - Start Docker (if not running)
   - Pull/run Ollama container
   - Pull/run AnythingLLM container
   - Verify ports: Ollama on 11434, AnythingLLM on 3001
   - Start Syncthing for file sync (if applicable)
   - Display status and URLs
   
2. Create LAUNCH.bat script (PowerShell-based, similar to START_DRCODEPT.ps1)
   
3. Document all URLs:
   - Ollama API: http://localhost:11434
   - AnythingLLM Web: http://localhost:3001
   - FastMCP Server: http://localhost:8000 (existing)

**Success Criteria:**
- Single command to launch entire unrestricted RAG system
- Clear output showing all services running
- Fallback for "already running" scenarios

**Progress**: ⏳ To start

---

### **TASK 2: Document AnythingLLM Setup** ✅
**Objective**: Create clear guide for AnythingLLM usage (UI, document upload, querying)
**Input**: AnythingLLM localhost:3001 interface (existing)  
**Output**: `ARCHITECTURE/ANYTHINGLLM_SETUP_GUIDE.md`  
**Time**: ~45 minutes

**Steps:**
1. Document AnythingLLM interface:
   - First-time setup (localhost:3001)
   - Document upload process (PDF, TXT, Markdown)
   - Workspace creation + naming conventions
   - Settings: Model selection, temperature, context window

2. Integration points:
   - How to select Ollama as the backend LLM
   - How to select Dolphin model specifically
   - RAG settings (chunk size, retrieval count)

3. Workflows documented:
   - "Upload a PDF" → step-by-step
   - "Query documents with RAG" → step-by-step
   - "Switch models/backends" → settings path
   - "Access from CLI" (Dr. CodePT v0.1 integration)

4. Usage within Dr. CodePT:
   - anythingllm_client.py connection details
   - How queries flow: Dr. CodePT → AnythingLLM → Ollama/Dolphin → response

**Success Criteria:**
- Someone could follow this guide and have AnythingLLM working from scratch
- Clear explanation of why this is "unrestricted" (Dolphin has no censoring)
- Integration points with Dr. CodePT clearly marked

**Progress**: ⏳ To start

---

### **TASK 3: Create Ollama/Dolphin Unrestricted RAG Spec** ✅
**Objective**: Document why Ollama+Dolphin is better than Chroma+restricted LLM  
**Input**: Existing fastmcp-server code, Dr. CodePT v0.1  
**Output**: `ARCHITECTURE/OLLAMA_UNRESTRICTED_RAG_SPEC.md`  
**Time**: ~60 minutes

**Steps:**
1. **Unrestricted vs. Restricted comparison**:
   - What "content filtering" means (in Claude, ChatGPT, standard LLMs)
   - Why Dolphin is uncensored (trained without safety filters)
   - Implications for medical study content (can ask sensitive questions freely)
   - Use cases: Drug interactions, contraindications, ethical dilemmas, etc.

2. **Architecture: Ollama + Dolphin inside AnythingLLM**:
   - Ollama runs as local inference engine
   - AnythingLLM is the RAG layer + frontend
   - Workflow: Query → AnythingLLM RAG search → context injection → Ollama/Dolphin inference → response
   - No external API calls, no filtering, fully local

3. **Why Dolphin specifically**:
   - Based on Llama models (good reasoning)
   - Uncensored by design (trained on unrestricted data)
   - Can discuss controversial topics without evasion
   - Good for medical content (diagnostic reasoning, edge cases)

4. **Compared to previous plan (Chroma)**:
   - Chroma: Vector DB only (needs external LLM for responses)
   - AnythingLLM+Ollama: Full RAG pipeline (search + inference all local)
   - Advantage: Faster, fewer dependencies, better integration

5. **Limitations**:
   - CPU-only: inference will be slower
   - Model quality: Dolphin is good but not GPT-4 level
   - No multimodal: Can't do image understanding (unlike vision models)

6. **Performance expectations**:
   - Response time: 10-30 sec per query on CPU (depends on context length)
   - Document indexing: Fast in AnythingLLM
   - No rate limits, no API costs

**Success Criteria:**
- Clear explanation of why this is better for your use case
- Documented tradeoffs (speed vs. local control)
- Realistic expectations for CPU-only performance

**Progress**: ⏳ To start

---

### **TASK 4: Create AnythingLLM Setup Spec (Step-by-Step)** ✅
**Objective**: Detailed implementation guide to get AnythingLLM + Dolphin running  
**Input**: LAUNCH.bat architecture, Ollama specs  
**Output**: `ARCHITECTURE/ANYTHINGLLM_DOLPHIN_SETUP_SPEC.md`  
**Time**: ~45 minutes

**Steps:**
1. **Prerequisites check**:
   - Docker installed? Check command: `docker --version`
   - Ollama ready? Check: `ollama --version`
   - Port 3001 available? Check: `netstat -ano | findstr 3001`
   - Port 11434 available? Check: `netstat -ano | findstr 11434`

2. **Ollama Setup**:
   - Pull Dolphin model: `ollama pull dolphin-mixtral` (or latest variant)
   - Verify model loads: `ollama list`
   - Test inference: Simple curl command to http://localhost:11434/api/generate

3. **AnythingLLM Setup**:
   - Run Docker container: `docker run --rm --network host -e STORAGE_DIR=/home/anythingllm/storage anythingllm/anythingllm:latest`
   - Wait for startup message
   - Open http://localhost:3001
   - Create workspace: "PT_School_RAG"
   - Select Ollama as LLM provider
   - Configure Ollama connection: http://localhost:11434
   - Select Dolphin model

4. **First Document Upload**:
   - Upload a test PDF (corrupted or not)
   - Monitor indexing progress
   - Run test query: "What is this document about?"

5. **Integration with Dr. CodePT**:
   - Update anythingllm_client.py to point to localhost:3001
   - Test: `python drcodept.py query "test query"`
   - Verify response comes from Ollama/Dolphin

6. **Troubleshooting Guide**:
   - Port conflicts resolution
   - Model download failures (retry logic)
   - AnythingLLM container fails to start
   - Ollama not responding

**Success Criteria:**
- Someone could follow this and have a working unrestricted RAG in 30 min
- All troubleshooting covered
- Clear integration path to Dr. CodePT

**Progress**: ⏳ To start

---

### **TASK 5: Document Dr. CodePT v0.1** ✅
**Objective**: Explain what the existing CLI system does and how it uses AnythingLLM
**Input**: Existing Dr. CodePT code (if findable), anythingllm_client.py  
**Output**: `ARCHITECTURE/DRCODEPT_V0_1_DOCUMENTATION.md`  
**Time**: ~40 minutes

**Steps:**
1. **Overview of Dr. CodePT v0.1**:
   - CLI interface for study automation
   - Main commands: `study`, `anki`, `npte`, `drill`, `query`
   - Backend: AnythingLLM + Ollama/Dolphin

2. **anythingllm_client.py interface**:
   - Connection to localhost:3001
   - Query method signature
   - Citation/provenance handling
   - Error handling

3. **Workflows documented**:
   - `drcodept query "question"` → RAG search + Dolphin answer
   - `drcodept anki "topic" [n]` → Generate Anki cards from materials
   - `drcodept npte "topic" [n]` → Generate NPTE practice questions
   - `drcodept drill "topic"` → Practice mode (quiz-style)

4. **Integration with Anatomy MCP**:
   - How Anatomy MCP facts could feed into Dr. CodePT
   - Potential flow: Extract facts → Pass to Dr. CodePT anki generator → Create cards

5. **Anki Generator details**:
   - Takes RAG context (from AnythingLLM)
   - Generates front/back cards
   - Exports to CSV
   - Imports to Anki directly

6. **Current limitations**:
   - Single workspace (PT_School_RAG)
   - CPU-only performance
   - Model knowledge cutoff (Dolphin is based on older LLamas)

**Success Criteria:**
- Clear explanation of how to use Dr. CodePT
- Shows integration with AnythingLLM backend
- Explains Anki card generation workflow

**Progress**: ⏳ To start

---

### **TASK 6: Create Unified System Architecture** ✅
**Objective**: Map all 3 systems together: Desktop Agent + Blackboard + AnythingLLM/Ollama RAG  
**Input**: Tasks 1-5 outputs  
**Output**: `ARCHITECTURE/UNIFIED_SYSTEM_V2.md`  
**Time**: ~50 minutes

**Steps:**
1. **System Components (Revised)**:
   - **Desktop Agent**: Blackboard automation, file management (existing FastMCP)
   - **Content Pipeline**: Blackboard → organize → AnythingLLM workspace
   - **AnythingLLM RAG**: Local knowledge base with Ollama/Dolphin backend
   - **Dr. CodePT CLI**: Study commands (query, anki, npte, drill)
   - **Anatomy MCP**: Fact extraction from slides/transcripts (optional integration)

2. **Full User Workflow**:
   - Day 1: `LAUNCH.bat` → starts Docker/Ollama/AnythingLLM
   - Day 2: `drcodept query "What's the innervation of the gluteus medius?"` 
     → Queries AnythingLLM → Searches indexed materials → Ollama/Dolphin answers
   - Day 3: Upload new Pathology PDF to AnythingLLM → Immediately searchable
   - Day 4: `drcodept anki "nervous system" 20` → Generates 20 cards from materials → Anki

3. **Data Flow Diagram (ASCII)**:
   ```
   Blackboard Files
         ↓
   [Desktop Agent Downloads]
         ↓
   C:\PT_School\<Course>\Week_<N>\
         ↓
   [Upload to AnythingLLM]
         ↓
   [Indexed in AnythingLLM Workspace]
         ↓
   User Query via Dr. CodePT CLI
         ↓
   AnythingLLM RAG Search + Context
         ↓
   Ollama/Dolphin Inference
         ↓
   Response with Citations
         ↓
   Anki Card Generation (optional)
   ```

4. **Critical Path (Implementation Order)**:
   - ✅ LAUNCH.bat (get system running)
   - ✅ Blackboard downloads (get materials)
   - ✅ AnythingLLM workspace + indexing (make searchable)
   - ✅ Dr. CodePT queries (study interface)
   - ⏳ Anatomy MCP integration (fact extraction layer, optional)

5. **Success Metrics**:
   - "Run LAUNCH.bat, then query my materials immediately"
   - "Upload a new PDF, it's searchable within 2 minutes"
   - "Generate Anki cards from materials automatically"
   - "All local, no API dependencies, no content filtering"

**Success Criteria:**
- Shows how Blackboard → AnythingLLM → Dr. CodePT → Anki all connect
- Clear implementation roadmap
- Realistic performance expectations

**Progress**: ⏳ To start

---

### **TASK 7: Update MASTER_PLAN.md** ✅
**Objective**: Reflect the revised architecture (AnythingLLM instead of Chroma)  
**Input**: All tasks 1-6 outputs + current MASTER_PLAN  
**Output**: Updated `MASTER_PLAN.md`  
**Time**: ~30 minutes

**Steps:**
1. **Add new section: ARCHITECTURE REVISION (Nov 13)**
   - Explain why AnythingLLM+Ollama+Dolphin replaces Chroma
   - Key benefit: Unrestricted responses, full RAG pipeline, local control
   - Tradeoff: CPU-only performance acceptable for medical study use case

2. **Update Component 3 (RAG System)**:
   - OLD: Chroma + bge-small embeddings
   - NEW: AnythingLLM + Ollama/Dolphin backend
   - Same indexing strategy (PDFs, transcripts, web content)
   - Same search + context injection
   - New: Unrestricted inference (Dolphin has no content filters)

3. **Update Next Immediate Steps**:
   - Create LAUNCH.bat
   - Document AnythingLLM setup
   - Verify Ollama/Dolphin running
   - Test Dr. CodePT queries
   - Implement Blackboard downloads
   - Wire pipeline

4. **Add Decision Note**:
   - Why AnythingLLM > Chroma for your use case
   - Reference to OLLAMA_UNRESTRICTED_RAG_SPEC.md

**Success Criteria:**
- Master Plan is single source of truth for new architecture
- Clear explanation of the pivot + reasoning

**Progress**: ⏳ To start

---

## 📝 COMPLETION REPORT (Fill This In As You Go)

### Task 1: Verify & Document LAUNCH.bat
- Status: ⏳ In Progress / ✅ Complete / ❌ Blocked
- File Created: `LAUNCH.bat`
- Key Findings:
  - [To be filled in]
- Blockers/Issues: 
  - [To be filled in]
- Time Spent: [To be filled in]

### Task 2: Document AnythingLLM Setup
- Status: ⏳ In Progress / ✅ Complete / ❌ Blocked
- File Created: `ARCHITECTURE/ANYTHINGLLM_SETUP_GUIDE.md`
- Key Findings:
  - [To be filled in]
- Blockers/Issues:
  - [To be filled in]
- Time Spent: [To be filled in]

### Task 3: Ollama/Dolphin Unrestricted RAG Spec
- Status: ⏳ In Progress / ✅ Complete / ❌ Blocked
- File Created: `ARCHITECTURE/OLLAMA_UNRESTRICTED_RAG_SPEC.md`
- Key Findings:
  - [To be filled in]
- Blockers/Issues:
  - [To be filled in]
- Time Spent: [To be filled in]

### Task 4: AnythingLLM Dolphin Setup Spec
- Status: ⏳ In Progress / ✅ Complete / ❌ Blocked
- File Created: `ARCHITECTURE/ANYTHINGLLM_DOLPHIN_SETUP_SPEC.md`
- Key Findings:
  - [To be filled in]
- Blockers/Issues:
  - [To be filled in]
- Time Spent: [To be filled in]

### Task 5: Dr. CodePT v0.1 Documentation
- Status: ⏳ In Progress / ✅ Complete / ❌ Blocked
- File Created: `ARCHITECTURE/DRCODEPT_V0_1_DOCUMENTATION.md`
- Key Findings:
  - [To be filled in]
- Blockers/Issues:
  - [To be filled in]
- Time Spent: [To be filled in]

### Task 6: Unified System Architecture
- Status: ⏳ In Progress / ✅ Complete / ❌ Blocked
- File Created: `ARCHITECTURE/UNIFIED_SYSTEM_V2.md`
- Key Findings:
  - [To be filled in]
- Blockers/Issues:
  - [To be filled in]
- Time Spent: [To be filled in]

### Task 7: Update MASTER_PLAN.md
- Status: ⏳ In Progress / ✅ Complete / ❌ Blocked
- Master Plan Updated: [Yes/No]
- New Sections Added: [To be filled in]
- Blockers/Issues:
  - [To be filled in]
- Time Spent: [To be filled in]

---

## 📊 OVERALL COMPLETION SUMMARY

**Total Tasks**: 7  
**Completed**: [To be filled in]  
**Blocked**: [To be filled in]  
**Time Spent**: [To be filled in]  

### What Worked Well:
- [To be filled in]

### What Couldn't Be Done:
- [To be filled in]

### Critical Decisions Made:
- AnythingLLM + Ollama/Dolphin (unrestricted) vs. Chroma
- [To be filled in]

### Recommendations for Next Chat:
- [To be filled in]

### Files/Folders Created:
- [To be filled in]

---

## 🚀 INSTRUCTIONS FOR CLAUDE (OVERNIGHT WORKER)

Execute tasks 1-7 in order. Work continuously. Document progress in this CODEX_V2 file.

**Key Context:**
- You already have Dr. CodePT v0.1 CLI + Anatomy MCP in the system
- This overnight work is DOCUMENTATION + ARCHITECTURE, not code implementation
- Focus on clarity: Trey needs to understand how to launch and use the system

**For Each Task:**
1. Read objective, input, output, steps
2. Do the research (read code, understand flows)
3. Write the output file(s)
4. Update COMPLETION REPORT
5. Move to next task

**If You Get Blocked:**
- Document what you tried
- Explain why
- Suggest alternative
- Move on

**At the End:**
- Fill OVERALL COMPLETION SUMMARY
- Trey will read this in morning and know exactly what was done

---

**Created By**: Claude (Nov 13, Revised Plan)  
**Status**: Ready for Overnight Execution  
**Expected Completion**: Early Morning (Nov 13-14)
