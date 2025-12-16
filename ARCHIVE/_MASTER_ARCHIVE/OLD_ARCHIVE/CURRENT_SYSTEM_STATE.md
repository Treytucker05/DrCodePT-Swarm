# 📋 CURRENT SYSTEM STATE (November 11, 2025)

**Document:** Full system audit after reading all files

---

## ✅ WHAT EXISTS (WORKING)

### **1. Anatomy MCP (Advanced System)**
**Location:** `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\tools\anatomy_mcp\`

**State:** Complete + Documented (ready to test)

**Components:**
- `entities.py` (237 lines) - Detects anatomy entities (muscles, nerves, arteries, etc.)
- `aligner.py` (167 lines) - Aligns slide sections to transcript windows (TF-IDF)
- `verifier.py` (210 lines) - Two-source verification (4 verification tiers)
- `manifest_loader.py` (109 lines) - Loads manifest.yaml + resolves glob patterns
- `server.py` (383 lines) - Complete MCP server (FastMCP)

**Adapters:** PDF, PPTX, TXT, CSV parsers

**Features:**
- ✅ Fact extraction from slides + transcripts
- ✅ Entity detection + confidence scoring
- ✅ Transcript-to-slide alignment
- ✅ Dual-source verification (4 tiers: Verified, Flex, Needs Review, Not Covered)
- ✅ Multi-format export: JSONL, Anki (TSV), Markdown
- ✅ SQLite facts database
- ✅ Coverage reports

**Current Scope:** Week 9 (Gluteal & Posterior Thigh) pilot

**Export Formats:**
- JSONL: Raw facts with provenance
- **Anki TSV:** `front\tback\n` format (verified facts only)
- Markdown: Human-readable with verification status grouping

---

### **2. Dr. CodePT v0.1 (Python CLI)**
**Location:** `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\core\drcodept_v0.1\`

**State:** Complete + Ready to use

**Components:**
- `drcodept.py` (260 lines) - Main CLI application
- `core/anythingllm_client.py` - Connects to AnythingLLM
- `core/rag_handler.py` - Query + citation handling
- **`generators/anki_generator.py`** (154 lines) - Anki card generation
- `generators/npte_generator.py` - NPTE question generation

**Anki Generator Features:**
- Connects to AnythingLLM + local Ollama
- Generates cards in JSON format
- Supports: `front`, `back`, `page`, `tags`
- Exports to CSV (Anki importable)
- Weak area focused decks
- Image-based cards

**Commands:**
- `study <topic>` - Full workflow (NPTE + Anki)
- `anki <topic> [n]` - Generate n Anki cards
- `npte <topic> [n]` - Generate n NPTE questions
- `drill <topic>` - Practice test mode
- `query <question>` - Ask with citations

**Output:** JSON files → CSV → Anki import

---

## 🔗 CURRENT INTEGRATION STATE

**Current Workflow (Manual):**
1. You + ChatGPT gather materials
2. Generate card data
3. Send to AnkiGenerator → JSON
4. Import to Anki

**Anatomy MCP Purpose:** Extract facts from slides/transcripts (not yet integrated with Anki generator)

**Missing Link:** How Anatomy MCP facts → Anki cards

---

## 🎯 WHAT'S NOT YET CONNECTED

❌ Anatomy MCP facts (verified, categorized) → AnkiGenerator input  
❌ Anatomy MCP to all 5 PT courses (currently Week 9 pilot only)  
❌ Unified "use Anatomy MCP facts OR ChatGPT materials" in AnkiGenerator  
❌ Automated facts → Anki without manual ChatGPT step  

---

## 💡 PHASE 2C CORE QUESTIONS (NOW CLEAR)

This changes my approach. Let me ask the RIGHT question:

**PHASE 2C - REVISED QUESTION 3:**

**Should the unified MCP system:**

**A) Extend Anatomy MCP to all 5 courses** (same architecture: extract facts → verify → export)

**B) Build separate MCP just for ChatGPT Bridge** (you feed it cards from ChatGPT, it outputs Anki)

**C) Connect both** (Anatomy MCP extracts facts, AnkiGenerator accepts both Anatomy facts AND ChatGPT cards)

**Which makes sense for your workflow?**

---

📊 **Chat Status:** 104k/190k used | ~86k remaining | ✅ Safe