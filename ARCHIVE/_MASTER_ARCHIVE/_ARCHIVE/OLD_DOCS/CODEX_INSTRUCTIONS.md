# CODEX INSTRUCTIONS - Tonight's Task

**Current Status:** Architecture discovered - Real work identified  
**Time:** Tonight (while Trey is away)  
**Owner:** Codex (AI agent)  
**Deadline:** Have findings & next steps ready for tomorrow chat

---

## 🎯 What We Discovered Today

**GOOD NEWS:**
✅ Folder reorganization complete (PROGRAMS, IN_DEVELOPMENT, DOCS)
✅ Dashboard API built & running on :7400
✅ Dashboard loads & displays courses/decks
✅ Can create decks and cards locally
✅ API saves data to C:\PT School\ successfully
✅ StudyMCP connected to ChatGPT via ngrok

**THE REAL PICTURE:**
- ChatGPT is connected to **StudyMCP** (not the local FastMCP)
- StudyMCP has: `list_modules`, `ingest_module`, `search_facts`, `export_module`
- **MISSING:** `addCardToDeck` tool (needed for ChatGPT to create cards directly)

**THE REAL GOAL:**
ChatGPT → StudyMCP.addCardToDeck() → Anki (direct card creation)

---

## 🎯 Your Mission Tonight

### CRITICAL TASK: Find StudyMCP Source Code & Plan addCardToDeck Tool

**Task 1: Locate StudyMCP Code**

SearchServe directories for the StudyMCP server code:

```powershell
# Is it in DrCodePT-Swarm?
Get-ChildItem "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm" -Recurse -Filter "*.py" | Where-Object {$_.FullName -match "mcp|study"} | Select-Object FullName

# Check PROGRAMS/fastmcp-server for variations
Get-ChildItem "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server" -Recurse | Select-Object FullName

# Check if there's a separate StudyMCP folder somewhere
Get-ChildItem "C:\" -Recurse -ErrorAction SilentlyContinue -Filter "*studymcp*" -Type d | Select-Object FullName | Head -20
```

**Report:**
- [ ] Found StudyMCP source code location: ___________
- [ ] Is it local or cloud-hosted?
- [ ] Can you read the source code?

---

### Task 2: Understand Anki Integration

Figure out how cards should reach Anki:

**Check for AnkiConnect:**
```powershell
# Is AnkiConnect running?
try {
  Invoke-WebRequest -Uri "http://127.0.0.1:8765" -TimeoutSec 2
  Write-Host "✅ AnkiConnect is running on 8765"
} catch {
  Write-Host "❌ AnkiConnect NOT running"
}
```

**Check for Anki credentials:**
```powershell
# Search for Anki config
Get-ChildItem "C:\Users\treyt" -Recurse -Filter "*.env" | Select-Object FullName

# Look for Anki-related config
Get-ChildItem "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm" -Recurse | Where-Object {$_.Name -match "anki|credential"} | Select-Object FullName
```

**Report:**
- [ ] AnkiConnect running? Yes/No
- [ ] Anki credentials found at: ___________
- [ ] Method to add cards: File-based? API? Direct plugin?

---

### Task 3: Document What addCardToDeck Needs

Create a file: `ADDCARDTODECK_DESIGN.md` with:

```markdown
# addCardToDeck Tool Design

## Input Parameters (What ChatGPT will send)
- course: string (e.g., "Anatomy")
- module: string (e.g., "Chapter 5")
- front: string (question)
- back: string (answer)
- tags: array (e.g., ["anatomy", "muscles"])
- difficulty: string (easy/medium/hard)

## Output (What tool returns to ChatGPT)
- success: boolean
- cardId: string
- message: string
- anki_status: "added_to_anki" | "saved_local" | "error"

## Integration Points
- [ ] Takes input from ChatGPT
- [ ] Calls Anki API (or saves to file)
- [ ] Returns status to ChatGPT
- [ ] Logs action for audit trail

## Anki Connection Method
[Describe how it reaches Anki: AnkiConnect, file-based, plugin, etc.]

## Error Handling
- What if Anki is offline?
- What if card already exists?
- What if invalid parameters?
```

---

### Task 4: Update STATUS.md

Add a new section documenting tonight's findings:

```markdown
## Phase 2C Smoke Test Results (November 12, 2025)

### ✅ What Works
- API server running cleanly on :7400
- Dashboard loads and displays courses/decks
- Can create decks via UI
- Can create cards via UI (saved locally)
- Data persists to C:\PT School\
- StudyMCP connected to ChatGPT via ngrok

### ❌ What's Missing
- `addCardToDeck` tool in StudyMCP
- Direct ChatGPT → Anki card creation workflow

### 🔍 Discovery: Real Architecture
- ChatGPT connected to StudyMCP (not local FastMCP)
- StudyMCP is content ingestion & search (not card creation)
- Need to ADD `addCardToDeck` tool to StudyMCP

### 📋 Next Steps (Tomorrow)
1. Locate StudyMCP source code
2. Add `addCardToDeck` tool
3. Test ChatGPT → StudyMCP → Anki workflow
4. Verify card appears in Anki
```

---

## 📊 Deliverables for Tomorrow

When Trey returns, have ready:

- [ ] StudyMCP source code location identified
- [ ] Anki integration method documented
- [ ] `ADDCARDTODECK_DESIGN.md` created
- [ ] STATUS.md updated with findings
- [ ] List of questions/blockers (if any)

---

## 🔧 If You Find StudyMCP Code

IF you locate the StudyMCP source:

1. Read it to understand current tools
2. Plan how `addCardToDeck` fits in
3. Identify what Anki library/API it uses
4. Check if dependencies are installed
5. Document findings for tomorrow's implementation

**DO NOT modify code tonight** - just document & plan.

---

## 📞 Important Notes

- **Dashboard API is COMPLETE** for its purpose (RAG/agent system)
- **Real goal:** ChatGPT → MCP → Anki (not web dashboard)
- **Smoke test partially passed:** Infrastructure works, but missing the card creation tool
- **You're on the right track** - just need to build the missing piece

---

## 💡 Think About

Before tomorrow, consider:
1. Should `addCardToDeck` save locally (C:\PT School\) OR directly to Anki?
2. If directly to Anki - how? AnkiConnect? API?
3. Should it validate cards before adding?
4. Should it check for duplicates?
5. How should it handle errors?

---

## ✅ Success Criteria for Tonight

You'll be done when:

- [ ] StudyMCP source code located
- [ ] Anki integration method identified
- [ ] ADDCARDTODECK_DESIGN.md written
- [ ] STATUS.md updated
- [ ] Blockers/questions documented

**You don't need to build it tonight - just identify it and plan it.**

---

**Status:** 🏗️ ARCHITECTURE DISCOVERY COMPLETE - Ready to Build  
**Mission:** Find StudyMCP + Plan addCardToDeck Tool  
**Deadline:** Tomorrow morning  
**Owner:** Codex  
**Next Chat:** Trey reviews findings + we build addCardToDeck
