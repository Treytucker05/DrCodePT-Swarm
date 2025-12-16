
# 🚀 IMPLEMENTATION ROADMAP: AnythingLLM + Ollama + Dolphin
**Created**: November 13, 2025  
**Owner**: Trey Tucker  
**Status**: Ready for Implementation  
**Architecture**: Unrestricted Local RAG (Option B)  
**Timeline**: 2 weeks to full production

---

## 📋 EXECUTIVE SUMMARY

**What You're Building:**
A local-first, unrestricted RAG system that:
- Indexes your PT course materials
- Provides unrestricted medical reasoning (no Claude filters)
- Generates Anki flashcards automatically
- Integrates with Blackboard for material downloads
- Runs completely offline

**Key Decisions:**
- ✅ AnythingLLM (web UI + RAG orchestration)
- ✅ Ollama (local inference engine)
- ✅ Dolphin model (unrestricted reasoning)
- ✅ Chroma embedding (local vector DB)
- ✅ CPU-optimized workflow (no GPU needed)

**Expected Timeline:**
- Phase 1 (Setup): 4-6 hours
- Phase 2 (Integration): 6-8 hours
- Phase 3 (Automation): 8-10 hours
- Phase 4 (Polish): 4-6 hours
- **Total: ~25-30 hours over 2 weeks**

---

## 🎯 PHASE 1: FOUNDATION (Tonight + Tomorrow)
**Objective**: Get AnythingLLM + Ollama + Dolphin running locally, index one test PDF, verify retrieval

**Time**: 4-6 hours

### **1A: Pre-Flight Checks (30 min)**

**Task**: Verify Docker, storage, network

```bash
# Check Docker is installed
docker --version
# Expected: Docker version 20.x or higher

# Check available storage
# Open File Explorer
# C: drive right-click → Properties
# Need: ✅ 11.8GB showing

# Check internet speed
# Download speedtest: https://speedtest.net
# Need: ✅ 5+ Mbps for model downloads
```

**Success Criteria:**
- ✅ Docker installed + running
- ✅ 11.8GB confirmed
- ✅ Internet >5 Mbps

**Blockers to Watch:**
- Docker not installed → Download from docker.com
- Storage lower than expected → Delete temp files in C:\Windows\Temp
- WiFi slow → Download models on wired connection if possible

---

### **1B: Download Models (2-3 hours, mostly waiting)**

**This is the big one. Models need to download on good WiFi.**

#### **Step 1: Download Dolphin Model (~4-7GB)**

```bash
# Open PowerShell as Administrator
# Navigate to any folder

ollama pull dolphin-mixtral
# OR for smaller variant:
ollama pull dolphin-mixtral:7b

# Expected output:
# "pulling from library/dolphin-mixtral..."
# [=========================>] 100%
# "Success!"

# Verify it's there:
ollama list
# Should see "dolphin-mixtral  7b  4.1GB"
```

**Time**: 15-30 min (depends on internet speed)  
**Storage used**: ~4-7GB  

**Blockers:**
- "ollama: command not found" → Ollama not installed, install from ollama.ai
- "connection refused" → Ollama not running, start it first

#### **Step 2: Download Embedding Model**

```bash
# In the same terminal
ollama pull nomic-embed-text
# Expected output: "...Success!"

# Verify:
ollama list
# Should see TWO models now
```

**Time**: 5-10 min  
**Storage used**: ~200MB  

#### **Step 3: Verify Models Load**

```bash
# Test Dolphin
ollama run dolphin-mixtral "What is the anatomy of the median nerve?"
# Should get a response (30-60 sec on CPU)

# If it works: ✅ You're ready
# If it fails: Check Docker memory (docker stats)
```

**Success Criteria:**
- ✅ Both models downloaded
- ✅ `ollama list` shows both
- ✅ Test query returns a response

---

### **1C: Launch AnythingLLM (15 min)**

**Option 1: Using Docker (Recommended)**

```bash
# Create storage directory
mkdir C:\Users\treyt\.anythingllm

# Run AnythingLLM container
docker run -d -p 3001:3001 ^
  -v C:\Users\treyt\.anythingllm:/home/anythingllm/storage ^
  --network host ^
  mintplexlabs/anythingllm:latest

# Expected: Container ID printed

# Wait 30 seconds for startup
# Open browser: http://localhost:3001
```

**Option 2: Using LAUNCH.bat (If Already Set Up)**

```bash
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm
LAUNCH.bat
# This starts everything (fastmcp + Ollama + AnythingLLM)
```

**Success Criteria:**
- ✅ http://localhost:3001 loads
- ✅ Welcome screen or login appears
- ✅ No errors in console

**If it doesn't load:**
```bash
# Check container logs
docker logs anythingllm

# If port 3001 is in use
netstat -ano | findstr :3001
# Kill the process or use different port
```

---

### **1D: First-Time Setup in AnythingLLM (20 min)**

**Step 1: Create Admin Account**
1. Go to http://localhost:3001
2. Create username/password (save these!)
3. Click "Get Started"

**Step 2: Configure LLM Provider**
1. Bottom left: Click gear (⚙️)
2. Go to "LLM Preference"
3. Select: "Ollama"
4. Base URL: `http://localhost:11434`
5. Model: `dolphin-mixtral`
6. Save

**Step 3: Configure Embeddings**
1. Still in Settings
2. Go to "Embedding Preference"
3. Select: "Local (built-in)"
4. Save (no model selection needed)

**Step 4: Create First Workspace**
1. Click "New Workspace"
2. Name: `PT_School_Testing`
3. Click Create
4. You're now in the workspace

**Success Criteria:**
- ✅ Admin account created
- ✅ Ollama connected (settings show green checkmark)
- ✅ Workspace created and visible

---

### **1E: Index Test Document (30 min)**

**Step 1: Prepare Test PDF**
1. Find any PT course PDF (Anatomy, Pathology, anything)
2. Save to Desktop for easy access

**Step 2: Upload to AnythingLLM**
1. In PT_School_Testing workspace
2. Click "+ Upload Documents" (usually top right or center)
3. Select your PDF
4. Click Upload

**Step 3: Monitor Indexing**
1. You'll see progress bar
2. AnythingLLM is:
   - Extracting text from PDF
   - Creating embeddings
   - Storing in vector DB
3. Wait for "Ready" status (usually 2-5 min for first file)

**Success Criteria:**
- ✅ PDF shows as "Indexed" in workspace
- ✅ No errors in console
- ✅ File appears in document list

**If indexing fails:**
- PDF corrupted → Try different PDF
- Memory issue → Close other apps, restart Docker
- Long wait (>10 min) → Normal for large PDFs, wait it out

---

### **1F: Test Retrieval (15 min)**

**Step 1: Write a Test Query**
1. At bottom of AnythingLLM: Chat box
2. Type a simple question about your PDF
   - Example: "What is the origin of the gluteus medius?"
   - Or: "What were the main topics in this document?"

**Step 2: Submit Query**
1. Press Enter or click Send
2. Ollama will think (20-30 sec on CPU)
3. Response appears

**Step 3: Verify Response**
1. Answer should cite your PDF
2. Click citation to see original text
3. Verify response matches document content

**Success Criteria:**
- ✅ Query returns a response
- ✅ Response has citations
- ✅ Citations match document
- ✅ Response is unrestricted (no Claude filters)

**Example Success:**
```
Q: "What are the contraindications for aggressive PT?"
A: "Based on your materials, the contraindications include... [detailed medical info, no hedging]"
Citations: Document_Name.pdf, page 5
```

---

## ✅ PHASE 1 COMPLETION CHECKLIST

- [ ] Docker running
- [ ] 11.8GB storage confirmed
- [ ] Dolphin model downloaded (~4-7GB)
- [ ] Embedding model downloaded (~200MB)
- [ ] AnythingLLM running at localhost:3001
- [ ] Admin account created
- [ ] Ollama configured in AnythingLLM
- [ ] Workspace created
- [ ] Test PDF uploaded and indexed
- [ ] Query tested and returned response
- [ ] Citations verified

**If all checked: Phase 1 = COMPLETE ✅**

**Storage After Phase 1:**
- Before: 11.8GB free
- Models: -7.2GB
- AnythingLLM container: -500MB
- After: ~4GB free
- **Status**: Tight but workable

**Storage Management:**
If you hit limits during Phase 2:
1. Move old archives to OneDrive
2. Clear Windows temp: `C:\Windows\Temp`
3. Or: Move AnythingLLM storage to OneDrive (reconfigure in Docker)

---

## 🎯 PHASE 2: INTEGRATION (Tomorrow Afternoon + Evening)
**Objective**: Wire AnythingLLM to Blackboard downloads, Anki, and fastmcp-server

**Time**: 6-8 hours

### **2A: Create Integration Layer (1-2 hours)**

**File**: `PROGRAMS/fastmcp-server/anythingllm_connector.py`

```python
# Purpose: Connect fastmcp-server tools to AnythingLLM workspace
# Tasks:
#  - Query AnythingLLM from fastmcp tools
#  - Send responses to Anki card generator
#  - Add citations to generated cards

class AnythingLLMConnector:
    def __init__(self):
        self.anythingllm_url = "http://localhost:3001"
        self.workspace = "PT_School_Testing"
    
    def query_workspace(self, question):
        """Query a workspace and get response with citations"""
        # Implementation details in Phase 2 spec
    
    def generate_cards_from_query(self, topic, num_cards):
        """Query + generate cards + add to Anki"""
        # Implementation details in Phase 2 spec
```

**Tasks:**
1. Build HTTP client to AnythingLLM API
2. Implement workspace querying
3. Parse citations from responses
4. Wire to existing `generate_flashcards` tool

**Success Criteria:**
- ✅ Can query AnythingLLM from Python
- ✅ Responses returned with citations
- ✅ Integrated with existing fastmcp tools

---

### **2B: Blackboard → AnythingLLM Pipeline (2-3 hours)**

**File**: `PROGRAMS/blackboard-agent/handlers/anythingllm_indexer.py`

```python
class AnythingLLMIndexer:
    def download_and_index_course(self, course_id, workspace_name):
        """Download course materials + automatically index to AnythingLLM"""
        # 1. Use existing Blackboard handler to download files
        # 2. Save to temp folder
        # 3. Upload to AnythingLLM workspace
        # 4. Monitor indexing
        # 5. Report status
```

**Tasks:**
1. Modify Blackboard handler to save downloads to staging folder
2. Create script to upload folder to AnythingLLM
3. Monitor indexing progress
4. Handle errors gracefully

**Integration Point:**
```
Blackboard (via existing handler)
    ↓ downloads files
Staging folder: C:\Users\treyt\PT_School_Staging\
    ↓ upload script
AnythingLLM workspace
    ↓ auto-indexing
Ready to query
```

**Success Criteria:**
- ✅ Download course PDF from Blackboard
- ✅ File appears in AnythingLLM workspace
- ✅ Can query it within 5 min of download

---

### **2C: Update fastmcp-server Tools (1-2 hours)**

**Modify existing tools to use AnythingLLM:**

1. `generate_flashcards` → Now queries AnythingLLM first
2. `search_materials` → Uses AnythingLLM vector search
3. `ingest_file` → Routes to AnythingLLM uploader

**Before:**
```
generate_flashcards(text) 
  → LLM generates cards from provided text
  → No context from your materials
```

**After:**
```
generate_flashcards(topic)
  → Query AnythingLLM workspace
  → Get context from YOUR materials
  → Generate cards based on context
  → Add citations to cards
  → Push to Anki
```

**Success Criteria:**
- ✅ All tools updated
- ✅ Claude can call tools without error
- ✅ Responses cite your materials

---

### **2D: End-to-End Test (1 hour)**

**Test Workflow:**

```bash
# Terminal 1: Start everything
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm
LAUNCH.bat

# Terminal 2: Manual test via Python
cd PROGRAMS/fastmcp-server
python -c "
from anythingllm_connector import AnythingLLMConnector
aqc = AnythingLLMConnector()

# Test 1: Query
response = aqc.query_workspace('What is the innervation of the median nerve?')
print(response)
print(response['citations'])

# Test 2: Generate cards
cards = aqc.generate_cards_from_query('median nerve anatomy', 5)
print(f'Generated {len(cards)} cards')
"

# Terminal 3: Verify cards in Anki
# Open Anki desktop
# Check DrCodePT deck
# Should see 5 new cards
```

**Success Criteria:**
- ✅ Query returns response with citations
- ✅ 5 cards generated
- ✅ Cards appear in Anki
- ✅ Cards include citations

---

## ✅ PHASE 2 COMPLETION CHECKLIST

- [ ] anythingllm_connector.py created and tested
- [ ] Can query AnythingLLM from fastmcp
- [ ] Blackboard → AnythingLLM pipeline working
- [ ] At least 2 courses indexed in AnythingLLM
- [ ] fastmcp tools updated to use AnythingLLM
- [ ] End-to-end test completed (Download → Index → Query → Cards → Anki)
- [ ] No errors in logs
- [ ] Can generate 5+ cards from one query

**If all checked: Phase 2 = COMPLETE ✅**

---

## 🎯 PHASE 3: AUTOMATION & SCALE (Next Week)
**Objective**: Automate entire pipeline, index all courses, validate system

**Time**: 8-10 hours

### **3A: Multi-Workspace Strategy (1-2 hours)**

Create separate workspaces for each course:
- `Legal_Ethics_RAG` (14 due dates)
- `Lifespan_RAG` (2 due dates)
- `Pathology_RAG` (22 due dates)
- `Anatomy_RAG` (6 due dates)
- `Exam_Skills_RAG` (4 due dates)

**Rationale:**
- Cleaner document organization
- Faster searches (smaller index)
- Can query specific course materials
- Can study by course

**Process:**
```bash
for each course:
  1. Create workspace in AnythingLLM
  2. Download all materials via Blackboard
  3. Upload to workspace
  4. Wait for indexing
  5. Test with sample query
```

**Success Criteria:**
- ✅ 5 workspaces created
- ✅ All ~50 course materials indexed
- ✅ Can switch workspaces and query

---

### **3B: Scheduled Indexing (2-3 hours)**

**Goal**: Automate checking for new course materials + indexing

```python
# scheduler_task.py

class ScheduledIndexer:
    def setup_daily_check():
        """Every morning at 6 AM:
        1. Check Blackboard for new materials
        2. Download new files
        3. Upload to AnythingLLM
        4. Report status via email/dashboard
        """
        # Implementation via APScheduler or Windows Task Scheduler
```

**Options:**
1. Windows Task Scheduler (built-in, simple)
2. APScheduler (Python, more control)
3. CRON (if WSL enabled)

**Recommended**: Windows Task Scheduler (simplest)

**Success Criteria:**
- ✅ Daily check runs at consistent time
- ✅ New materials auto-indexed
- ✅ No manual intervention needed

---

### **3C: Query CLI Tool (1-2 hours)**

**Create CLI for quick queries:**

```bash
# Usage from terminal:
python drcodept.py query "What is the inervation of the gluteus medius?"
# Output: Answer with citations

python drcodept.py anki "shoulder anatomy" 10
# Output: Creates 10 cards, adds to Anki

python drcodept.py list-workspaces
# Output: Shows all indexed courses
```

**Implementation:**
```python
# cli.py
import click
from anythingllm_connector import AnythingLLMConnector

@click.command()
@click.option('--workspace', default='PT_School_RAG')
@click.argument('query')
def query_cmd(query, workspace):
    aqc = AnythingLLMConnector()
    response = aqc.query_workspace(query, workspace)
    click.echo(response)

@click.command()
@click.argument('topic')
@click.option('--num', default=10)
def anki_cmd(topic, num):
    aqc = AnythingLLMConnector()
    cards = aqc.generate_cards_from_query(topic, num)
    click.echo(f"Added {len(cards)} cards to Anki")
```

**Success Criteria:**
- ✅ CLI tool works
- ✅ All commands tested
- ✅ Help text clear

---

### **3D: System Validation (2-3 hours)**

**Full system test:**

```bash
Scenario 1: Download Pathology Week 9
  ✓ Materials downloaded from Blackboard
  ✓ Files organized in PT_School folder
  ✓ Auto-indexed to Pathology_RAG workspace
  ✓ Can query immediately
  
Scenario 2: Generate Exam Cards
  ✓ Query: "Top 20 concepts for pathology midterm"
  ✓ Get contextual response from materials
  ✓ Generate 20 Anki cards
  ✓ Cards appear in Anki within 2 min
  
Scenario 3: Offline Usage
  ✓ LAUNCH.bat starts everything
  ✓ Can query without internet
  ✓ Responses come only from materials (no web calls)
  
Scenario 4: Storage Management
  ✓ Index 50 PDFs (~300MB content)
  ✓ Vector DB stays <2GB
  ✓ No crashes or slowdowns
```

**Success Criteria:**
- ✅ All 4 scenarios pass
- ✅ No errors in logs
- ✅ System stable for 8+ hours
- ✅ Response times consistent

---

## ✅ PHASE 3 COMPLETION CHECKLIST

- [ ] 5 workspaces created and populated
- [ ] ~50 course materials indexed (~300MB)
- [ ] All materials searchable
- [ ] Scheduled daily check working
- [ ] CLI tool ready for use
- [ ] All 4 validation scenarios passed
- [ ] System stable (8+ hours runtime)
- [ ] Response times documented

**If all checked: Phase 3 = COMPLETE ✅**

---

## 🎯 PHASE 4: POLISH & PRODUCTION (Week 2)
**Objective**: Error handling, dashboards, documentation

**Time**: 4-6 hours

### **4A: Error Handling & Recovery (1-2 hours)**

```python
# Scenarios to handle:
1. AnythingLLM offline → Retry with backoff
2. Ollama crashed → Auto-restart Ollama
3. Indexing failed → Log + retry later
4. Query timeout → Return "Please try again"
5. Storage full → Archive old workspaces
```

### **4B: Logging & Monitoring (1 hour)**

```python
# Log all operations:
# - Query timestamps
# - Response quality
# - Errors
# - Performance metrics

# Create dashboard showing:
# - System uptime
# - Last indexing time
# - Query count
# - Storage usage
```

### **4C: Documentation (1-2 hours)**

- [ ] User guide (how to query, generate cards)
- [ ] Troubleshooting guide
- [ ] API reference for CLI tools
- [ ] Architecture diagram (this system)
- [ ] Backup/recovery procedures

### **4D: Backup Strategy (30 min)**

```bash
# Weekly backup:
# 1. Export AnythingLLM vector DB
# 2. Save to OneDrive
# 3. Can restore if needed
```

---

## 💾 STORAGE MANAGEMENT THROUGHOUT

### **Current Situation:**
- Free space: 11.8GB
- After Phase 1: ~4GB free
- Phase 2 target: Use 3GB (for 50 PDFs)
- Phase 3: Use 2GB (for optimized indexes)

### **If You Hit Limits:**

**Option 1: Move AnythingLLM Storage to OneDrive**
```bash
# Stop AnythingLLM
docker stop anythingllm

# Move storage to OneDrive
robocopy C:\Users\treyt\.anythingllm C:\Users\treyt\OneDrive\AnythingLLM_Storage /MIR

# Restart with new path
docker run -d -p 3001:3001 ^
  -v C:\Users\treyt\OneDrive\AnythingLLM_Storage:/home/anythingllm/storage ^
  --network host ^
  mintplexlabs/anythingllm:latest
```

**Option 2: Archive Old Workspaces**
```bash
# Export unused course workspace
# Delete from AnythingLLM
# Re-import later if needed
```

**Option 3: Compress Vector DB**
- After indexing, compress embeddings
- Trade slightly slower searches for smaller storage
- Usually saves 20-30%

---

## 📊 SUCCESS METRICS

**Phase 1 Complete When:**
- ✅ Dolphin model runs locally
- ✅ Query returns unrestricted response
- ✅ Response cites your PDF

**Phase 2 Complete When:**
- ✅ End-to-end flow works (Download → Index → Query → Cards → Anki)
- ✅ 5+ cards generated and in Anki
- ✅ fastmcp tools updated

**Phase 3 Complete When:**
- ✅ All 5 courses indexed
- ✅ ~50 materials searchable
- ✅ Scheduled indexing working
- ✅ CLI tool functional
- ✅ System stable 8+ hours

**Phase 4 Complete When:**
- ✅ Error handling in place
- ✅ Documentation written
- ✅ Backup strategy active
- ✅ Ready for daily use

---

## 🚀 HOW TO PROCEED

**Tonight:**
1. Download Dolphin model
2. Launch AnythingLLM
3. Get Phase 1 running
4. Report back with Phase 1 checklist

**Tomorrow:**
1. Index all course materials
2. Build integration layer
3. Run end-to-end test

**This Week:**
1. Multi-workspace strategy
2. Scheduled indexing
3. CLI tool
4. System validation

**Next Week:**
1. Polish
2. Documentation
3. Production ready

---

**Build Status**: Ready to start  
**Next Action**: Download Dolphin model tonight  
**Questions**: Ask before Phase 1 if anything is unclear

