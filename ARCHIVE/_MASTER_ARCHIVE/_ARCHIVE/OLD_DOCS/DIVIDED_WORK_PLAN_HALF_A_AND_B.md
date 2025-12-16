# DIVIDED WORK PLAN - TWO HALVES

**Created:** November 12, 2025  
**Goal:** Clear ownership + execution path  
**Format:** HALF A (Understanding/Planning) | HALF B (Implementation/Integration)

---

## 📊 WORK DIVISION PHILOSOPHY

**HALF A = "Know What You're Doing"**
- Understand the system architecture
- Document the real workflows
- Make strategic decisions
- Plan integration approach
- Create specifications

**HALF B = "Do What Needs Doing"**
- Execute against clear specs
- Build missing pieces
- Test integrations
- Document results
- Prepare for next phase

**Total Time Investment:** ~12-16 hours split 50/50 (6-8 hours each half)

---

# ⚡ HALF A: UNDERSTANDING & STRATEGIC PLANNING (6-8 hours)

**Owner:** Trey (or whoever does research/planning)  
**Outcome:** Clear architecture decisions + implementation specs  
**Success Criteria:** All 12 tasks complete with zero ambiguity

---

## HALF A TASK 1: Find & Verify StudyMCP Location (1 hour)

**What to do:**
1. Search Windows for StudyMCP source code
2. Check if it's local or cloud-hosted
3. Determine if it's your code or someone else's
4. Document the full path + repository info

**How to search:**

```powershell
# Search in common locations
$locations = @(
    "C:\Users\treyt\OneDrive\Desktop",
    "C:\Users\treyt\OneDrive\Documents", 
    "C:\Users\treyt\OneDrive",
    "C:\Users\treyt\AppData"
)

foreach ($loc in $locations) {
    Get-ChildItem $loc -Recurse -ErrorAction SilentlyContinue | 
        Where-Object {$_.Name -match "study|mcp|codex"} | 
        Select-Object FullName
}
```

**Documentation to create:**
- StudyMCP location: ___________
- Type: (Your code / Third-party / Hybrid)
- Access: (Local files / Cloud / API endpoint)
- Status: (Active / Archived / Unknown)

**File to create:** `HALF_A_FINDINGS/1_STUDYMCP_LOCATION.md`

---

## HALF A TASK 2: Understand Current Anki Integration (1 hour)

**What to do:**
1. Check if AnkiConnect is installed/running
2. Search for existing Anki integration code
3. Verify credentials storage location
4. Understand current add-card method

**How to check:**

```powershell
# Check AnkiConnect
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8765" -TimeoutSec 2
    Write-Host "✅ AnkiConnect running"
} catch {
    Write-Host "❌ AnkiConnect not running"
}

# Look for Anki integrations
Get-ChildItem "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm" -Recurse | 
    Where-Object {$_.Name -match "anki"} | 
    Select-Object FullName
```

**Check these files specifically:**
- `PROGRAMS/card-generator/generators/*` - How does it export?
- `.env` files - Any AnkiConnect config?
- `unified_control_center/` - Any Anki setup docs?

**Documentation to create:**
- AnkiConnect available: Yes/No
- Current export method: (File-based / API / Manual)
- Anki credentials location: ___________
- Recommended integration path: ___________

**File to create:** `HALF_A_FINDINGS/2_ANKI_INTEGRATION_CURRENT.md`

---

## HALF A TASK 3: Map The Real Workflow (1 hour)

**What to do:**
1. Draw the actual data flow for card creation
2. Identify all systems involved
3. Mark the broken links
4. Document success path

**Create a document showing:**

```
CURRENT DESIRED STATE:
ChatGPT asks → StudyMCP receives → addCardToDeck called → Anki updated → Dashboard shows

CURRENT ACTUAL STATE (BROKEN LINK):
ChatGPT asks → StudyMCP receives → ??? → Manual export to Anki

YOUR JOB: Fill the ???
```

**Map these workflows:**
1. "Create card via ChatGPT" - what actually happens?
2. "Save card locally" - where does it go?
3. "Import to Anki" - current process?
4. "Verify card appears" - how is this done?

**Documentation to create:**
```
CURRENT WORKFLOW:
Step 1: User describes topic to ChatGPT
Step 2: ChatGPT calls [which tool?]
Step 3: [System X] does [what?]
Step 4: Data saved to [where?]
Step 5: [Manual step?] Import to Anki
Result: Card appears in Anki

DESIRED WORKFLOW:
Step 1: User describes topic to ChatGPT
Step 2: ChatGPT calls addCardToDeck
Step 3: Anki desktop updated automatically
Step 4: Dashboard reflects the new card
Result: Zero manual steps
```

**File to create:** `HALF_A_FINDINGS/3_WORKFLOW_ANALYSIS.md`

---

## HALF A TASK 4: Audit Your 5 PT Courses (1 hour)

**What to do:**
1. Verify all 48 due dates were extracted
2. Check data structure in database
3. Ensure courses are ready for card generation
4. Document any gaps

**How to check:**

```powershell
# Check Blackboard data
$dbPath = "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\blackboard-agent\opstore.db"

# List what's in C:\PT School\
Get-ChildItem "C:\PT School\" -Recurse | Select-Object FullName
```

**Verify each course has:**
- ✅ Folder created in C:\PT School\
- ✅ Due dates extracted (Blackboard)
- ✅ Initial deck structure ready
- ✅ No data corruption

**Documentation to create:**

```
COURSE AUDIT - November 12, 2025

Legal & Ethics
- Due dates extracted: 14 / 14 ✅
- Folder exists: C:\PT School\Legal-and-Ethics\ ✅
- Sample due date: [list 1]
- Status: Ready for cards

Lifespan Development
- Due dates extracted: 2 / 2 ✅
- Status: Ready for cards

Clinical Pathology
- Due dates extracted: 22 / 22 ✅
- Status: Ready for cards

Human Anatomy
- Due dates extracted: 6 / 6 ✅
- Status: Ready for cards

PT Examination Skills
- Due dates extracted: 4 / 4 ✅
- Status: Ready for cards

TOTAL: 48 / 48 ✅
```

**File to create:** `HALF_A_FINDINGS/4_COURSE_AUDIT.md`

---

## HALF A TASK 5: Define addCardToDeck Specification (1 hour)

**What to do:**
1. Write technical spec for the missing tool
2. Define inputs/outputs
3. Plan error handling
4. Document integration points

**Create a specification file with:**

```markdown
# addCardToDeck Tool - Technical Specification

## Function Signature
addCardToDeck(
    course: str,          # "Anatomy"
    module: str,          # "Chapter 5 - Muscles"
    front: str,           # Question/prompt
    back: str,            # Answer/explanation
    tags: list[str],      # ["anatomy", "muscles", "origin"]
    difficulty: str,      # "easy" | "medium" | "hard"
    source: str           # "ChatGPT" | "Dashboard" | "Manual"
) → AddCardResult

## Return Type
class AddCardResult:
    success: bool
    cardId: str          # Unique ID for tracking
    message: str
    ankiStatus: str      # "added_to_anki" | "saved_local" | "error"
    errors: list[str]

## Implementation Approach
[ ] Option A: Use AnkiConnect API (localhost:8765)
[ ] Option B: Save to C:\PT School\, Anki imports from there
[ ] Option C: Anki plugin that pulls from StudyMCP
[ ] Recommendation: ________

## Data Flow
ChatGPT.addCardToDeck() 
  → StudyMCP.addCardToDeck()
  → [Anki connection method]
  → Anki desktop updated
  → Dashboard syncs
  → Card visible in all interfaces

## Error Scenarios
1. Anki offline - [Action?]
2. Card duplicate - [Action?]
3. Invalid parameters - [Action?]
4. Storage full - [Action?]
```

**File to create:** `HALF_A_FINDINGS/5_ADDCARDTODECK_SPEC.md`

---

## HALF A TASK 6: Create Integration Architecture Doc (1 hour)

**What to do:**
1. Document how all 5 systems connect
2. Show data dependencies
3. Identify breaking points
4. Plan upgrade path

**Create architecture document showing:**

```
SYSTEM DEPENDENCIES DIAGRAM

┌─────────────────────────────────────────────────────────────┐
│                      YOUR SYSTEM                            │
└─────────────────────────────────────────────────────────────┘

1. BLACKBOARD-AGENT
   ├─ Input: UTMB portal credentials
   ├─ Output: 48 due dates → opstore.db
   └─ Used by: Dashboard (shows schedule)

2. CARD-GENERATOR
   ├─ Input: Study material (ChatGPT or StudyMCP)
   ├─ Logic: PERRIO Protocol v6.4
   └─ Output: JSON cards → Storage

3. FASTMCP-SERVER (Anatomy extraction)
   ├─ Input: Anatomy materials (slides, transcripts)
   ├─ Tools: list_modules, ingest_module, search_facts, export_module
   ├─ Missing: addCardToDeck
   └─ Output: Verified facts → Database

4. STUDYMCP (ChatGPT bridge - REAL ONE)
   ├─ Connected: ChatGPT via ngrok
   ├─ Tools: [list current tools]
   ├─ Missing: addCardToDeck
   └─ Output: [What does it produce?]

5. DASHBOARD-API
   ├─ Input: Web UI (courses/decks/cards)
   ├─ Storage: C:\PT School\ (JSON files)
   ├─ API: 11 endpoints
   └─ Status: Management interface (not primary workflow)

CRITICAL QUESTION:
Which MCP server is PRIMARY?
[ ] FASTMCP-SERVER (local Anatomy extraction)
[ ] STUDYMCP (ChatGPT connection)
[ ] Both (different purposes)
```

**File to create:** `HALF_A_FINDINGS/6_INTEGRATION_ARCHITECTURE.md`

---

## HALF A TASK 7: Decision Matrix - Priority Planning (0.5 hours)

**What to do:**
Create a decision framework for next steps

**Document choices:**

```markdown
# Strategic Decision Matrix

## Q1: Which workflow is MOST IMPORTANT?
[ ] A) ChatGPT → Auto-create cards → Anki (minimal manual work)
[ ] B) Dashboard UI management (web-based control)
[ ] C) Both equally
Recommendation: ________

## Q2: Where should addCardToDeck live?
[ ] A) In StudyMCP (ChatGPT-facing)
[ ] B) In FASTMCP-SERVER (Anatomy-focused)
[ ] C) Separate service
Recommendation: ________

## Q3: Anki integration method?
[ ] A) AnkiConnect API (Anki desktop talks HTTP)
[ ] B) File-based (write to C:\PT School\, Anki imports)
[ ] C) Anki plugin (direct access to Anki database)
Recommendation: ________

## Q4: Timeline expectation?
[ ] A) Complete by end of week
[ ] B) Complete by end of month
[ ] C) Ongoing development
Recommendation: ________

## Q5: Should local Dashboard be?
[ ] A) Primary interface (most important)
[ ] B) Secondary tool (nice to have)
[ ] C) Archived (focus on ChatGPT)
Recommendation: ________
```

**File to create:** `HALF_A_FINDINGS/7_DECISION_MATRIX.md`

---

## HALF A TASK 8: System Dependencies Checklist (0.5 hours)

**What to do:**
Verify all dependencies are installed/available

**Create checklist:**

```markdown
# System Requirements Verification

## Python Packages
[ ] FastMCP - `pip list | grep fastmcp`
[ ] Selenium - For Blackboard scraping
[ ] Flask/Express - For API
[ ] Claude SDK - For AI operations
[ ] AnkiConnect (if using API method)

## External Services
[ ] Anki Desktop - Running? Accessible?
[ ] Blackboard - Login credentials working?
[ ] Claude API - Key configured?
[ ] ngrok - For ChatGPT connection?
[ ] AnythingLLM - (if using for RAG)

## File Paths
[ ] C:\PT School\ - Writable?
[ ] opstore.db - Readable?
[ ] StudyMCP - Accessible?

## Ports
[ ] :7400 (Dashboard API)
[ ] :8000 (FastMCP server)
[ ] :8765 (AnkiConnect - if used)
[ ] :3001 (AnythingLLM - if used)
```

**File to create:** `HALF_A_FINDINGS/8_DEPENDENCIES.md`

---

## HALF A TASK 9: Current Status Update (0.5 hours)

**What to do:**
Update your STATUS.md with HALF A findings

**Locations to check/update:**
1. Root STATUS.md
2. unified_control_center/CURRENT_SYSTEM_STATE.md
3. Create new: HALF_A_FINDINGS/9_STATUS_UPDATE.md

**Include:**
- What works (verified)
- What's incomplete
- What's blocking
- Next 3 immediate actions

---

## HALF A TASK 10: Create HALF B Specifications (0.5 hours)

**What to do:**
Write the exact instructions for HALF B implementation

**This is your handoff document.** It should be so clear that someone else can execute it without questions.

**File to create:** `HALF_A_FINDINGS/10_HALF_B_SPECIFICATIONS.md`

**Include:**
1. Exact files to modify/create
2. Code patterns to follow
3. Testing steps
4. Success criteria
5. Known risks

---

## HALF A DELIVERABLES CHECKLIST

When HALF A is complete, you should have:

- [x] 1_STUDYMCP_LOCATION.md - Where StudyMCP lives
- [x] 2_ANKI_INTEGRATION_CURRENT.md - Current Anki setup
- [x] 3_WORKFLOW_ANALYSIS.md - Current vs. desired flow
- [x] 4_COURSE_AUDIT.md - All 48 due dates verified
- [x] 5_ADDCARDTODECK_SPEC.md - Technical specification
- [x] 6_INTEGRATION_ARCHITECTURE.md - How all 5 systems connect
- [x] 7_DECISION_MATRIX.md - Strategic choices
- [x] 8_DEPENDENCIES.md - All requirements verified
- [x] 9_STATUS_UPDATE.md - Current state documented
- [x] 10_HALF_B_SPECIFICATIONS.md - Exact build instructions

**Created:** `HALF_A_FINDINGS/` folder with all 10 documents

**Time investment:** ~6-8 hours

---

---

# 🔨 HALF B: IMPLEMENTATION & INTEGRATION (6-8 hours)

**Owner:** Developer (Python/JavaScript experience recommended)  
**Prerequisite:** HALF A completion + all 10 specifications ready  
**Outcome:** Working addCardToDeck tool + end-to-end testing  
**Success Criteria:** ChatGPT → Anki workflow verified working

---

## HALF B TASK 1: Prepare Development Environment (1 hour)

**What to do:**
1. Create working branch/folder
2. Set up logging/debugging
3. Prepare test data
4. Verify all dependencies

**Exact steps:**

```powershell
# Create working folder
mkdir "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\HALF_B_WORK"

# Copy key files for reference
Copy-Item "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\card-generator\*" `
          -Destination "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\HALF_B_WORK\reference_card_generator\" -Recurse

# Test Python environment
python --version  # Should be 3.8+
pip list | findstr fastmcp

# Test Anki connectivity
# (Run test specified in HALF A #8)
```

**Files created:**
- `HALF_B_WORK/setup_complete.txt` (timestamp)
- `HALF_B_WORK/dependencies_verified.log`

---

## HALF B TASK 2: Implement addCardToDeck Core Function (1.5 hours)

**What to do:**
1. Create the function following the spec
2. Implement chosen Anki integration method
3. Add error handling
4. Add logging

**Code structure (Python template):**

```python
# file: addcardtodeck.py

class CardAdditionError(Exception):
    """Custom exception for card addition failures"""
    pass

async def addCardToDeck(
    course: str,
    module: str,
    front: str,
    back: str,
    tags: list[str],
    difficulty: str,
    source: str = "unknown"
) -> dict:
    """
    Add a card to Anki via [chosen method].
    
    Args:
        course: Course name (e.g., "Anatomy")
        module: Module/chapter (e.g., "Chapter 5")
        front: Card front (question)
        back: Card back (answer)
        tags: List of tags
        difficulty: "easy" | "medium" | "hard"
        source: Origin of card
    
    Returns:
        {
            "success": bool,
            "cardId": str,
            "message": str,
            "ankiStatus": str,
            "errors": list[str]
        }
    """
    try:
        # Step 1: Validate input
        _validate_inputs(course, module, front, back)
        
        # Step 2: Check for duplicates
        if _card_exists(front, back):
            return _error_response("Card duplicate", "saved_local")
        
        # Step 3: Create card object
        card = {
            "id": _generate_id(),
            "front": front,
            "back": back,
            "tags": tags,
            "difficulty": difficulty,
            "course": course,
            "module": module,
            "source": source,
            "created": datetime.now().isoformat()
        }
        
        # Step 4: Save to storage
        storage_result = _save_to_storage(card, course, module)
        
        # Step 5: Add to Anki
        anki_result = _add_to_anki(card)
        
        # Step 6: Log success
        _log_card_addition(card, anki_result)
        
        return {
            "success": True,
            "cardId": card["id"],
            "message": f"Card added successfully",
            "ankiStatus": anki_result["status"],
            "errors": []
        }
        
    except Exception as e:
        _log_error(e)
        return _error_response(str(e), "error")

def _validate_inputs(course, module, front, back):
    """Validate input parameters"""
    if not course or not isinstance(course, str):
        raise ValueError("Course must be non-empty string")
    if not module or not isinstance(module, str):
        raise ValueError("Module must be non-empty string")
    if not front or len(front) < 5:
        raise ValueError("Front must be at least 5 characters")
    if not back or len(back) < 10:
        raise ValueError("Back must be at least 10 characters")

def _save_to_storage(card, course, module):
    """Save card to C:\PT School\"""
    # Implementation depends on chosen storage method
    pass

def _add_to_anki(card):
    """Add card to Anki desktop"""
    # Implementation depends on chosen Anki integration method
    pass

def _error_response(message, status):
    """Format error response"""
    return {
        "success": False,
        "cardId": None,
        "message": message,
        "ankiStatus": status,
        "errors": [message]
    }
```

**File to create:** `PROGRAMS/fastmcp-server/addcardtodeck.py`

---

## HALF B TASK 3: Integrate into StudyMCP (1.5 hours)

**What to do:**
1. Find StudyMCP source
2. Add addCardToDeck as a tool
3. Register with MCP protocol
4. Test MCP calling it

**Integration points:**

```python
# In StudyMCP server.py or tools definition:

# Register the tool
@mcp_tool.define_tool
async def addCardToDeck(
    course: str,
    module: str,
    front: str,
    back: str,
    tags: list,
    difficulty: str,
    source: str
):
    """Add a flashcard to Anki deck"""
    from addcardtodeck import addCardToDeck as add_card
    return await add_card(course, module, front, back, tags, difficulty, source)

# In tool manifest (if used):
TOOLS = {
    "list_modules": {...},
    "ingest_module": {...},
    "search_facts": {...},
    "export_module": {...},
    "addCardToDeck": {  # NEW TOOL
        "name": "addCardToDeck",
        "description": "Create a new flashcard in Anki deck",
        "parameters": {
            "course": "string - course name",
            "module": "string - module/chapter",
            "front": "string - card front",
            "back": "string - card back",
            "tags": "array - tags",
            "difficulty": "string - difficulty level",
            "source": "string - source identifier"
        }
    }
}
```

**File to modify:** `StudyMCP/server.py` (or equivalent)

**Files to create:**
- `HALF_B_WORK/studymcp_integration_log.txt`
- `HALF_B_WORK/tool_registration_test.py`

---

## HALF B TASK 4: Implement Storage Layer (1 hour)

**What to do:**
1. Create JSON deck file structure
2. Implement save logic
3. Handle conflicts/duplicates
4. Test persistence

**Storage structure:**

```
C:\PT School\
├── Anatomy\
│   ├── _decks-index.json
│   ├── Chapter-5-Muscles\
│   │   └── deck.json
│   └── Chapter-6-Nerve-Supply\
│       └── deck.json
├── Clinical Pathology\
└── [etc for other courses]
```

**File format:**

```json
{
  "course": "Anatomy",
  "module": "Chapter 5 - Muscles",
  "deckId": "anat-ch5-muscles-20251112",
  "cards": [
    {
      "id": "card-001",
      "front": "What is the origin of the biceps?",
      "back": "The long head originates from the supraglenoid tubercle of the scapula; the short head from the coracoid process.",
      "tags": ["anatomy", "muscles", "biceps"],
      "difficulty": "medium",
      "created": "2025-11-12T10:30:00",
      "source": "ChatGPT"
    }
  ]
}
```

**Code to implement:**

```python
def _save_to_storage(card, course, module):
    """Save card to JSON deck file"""
    import os
    import json
    
    # Build paths
    course_path = f"C:\\PT School\\{course.replace(' & ', '-').replace(' ', '-')}"
    module_path = os.path.join(course_path, module.replace(' ', '-'))
    deck_file = os.path.join(module_path, "deck.json")
    
    # Create directories if needed
    os.makedirs(module_path, exist_ok=True)
    
    # Load existing deck or create new
    if os.path.exists(deck_file):
        with open(deck_file, 'r') as f:
            deck = json.load(f)
    else:
        deck = {
            "course": course,
            "module": module,
            "cards": []
        }
    
    # Add card (check for duplicates first)
    for existing in deck["cards"]:
        if existing["front"] == card["front"]:
            raise Exception("Card duplicate")
    
    deck["cards"].append(card)
    
    # Save back to file
    with open(deck_file, 'w') as f:
        json.dump(deck, f, indent=2)
    
    return {"status": "saved_local", "path": deck_file}
```

**File to create:** `PROGRAMS/fastmcp-server/storage_handler.py`

---

## HALF B TASK 5: Implement Anki Integration (1 hour)

**What to do:**
Based on HALF A decision, implement chosen method

**Option A: AnkiConnect API**

```python
import requests
import json

def _add_to_anki_via_api(card):
    """Add card to Anki via AnkiConnect API"""
    try:
        url = "http://127.0.0.1:8765"
        
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": f"{card['course']}::{card['module']}",
                    "modelName": "Basic",
                    "fields": {
                        "Front": card["front"],
                        "Back": card["back"]
                    },
                    "tags": card["tags"]
                }
            }
        }
        
        response = requests.post(url, json=payload, timeout=5)
        result = response.json()
        
        if result.get("error"):
            return {"status": "error", "message": result["error"]}
        
        return {
            "status": "added_to_anki",
            "noteId": result.get("result"),
            "message": "Card added to Anki"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

**Option B: File-based (Anki imports JSON)**

```python
def _add_to_anki_file_based(card):
    """Add card by saving to Anki import folder"""
    import os
    import csv
    
    # Anki import format: front\tback\ttags
    anki_import_dir = os.path.expanduser("~/.anki_import")
    os.makedirs(anki_import_dir, exist_ok=True)
    
    import_file = os.path.join(anki_import_dir, f"{card['course']}_import.txt")
    
    with open(import_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        tags_str = " ".join(card["tags"])
        writer.writerow([card["front"], card["back"], tags_str])
    
    return {
        "status": "saved_local",
        "message": f"Card saved to {import_file} (manual import required)"
    }
```

**Decision from HALF A will determine which to use**

**File to create:** `PROGRAMS/fastmcp-server/anki_handler.py`

---

## HALF B TASK 6: Add Logging & Error Handling (0.5 hours)

**What to do:**
1. Set up structured logging
2. Add error recovery
3. Create audit trail
4. Enable debugging

**Logging implementation:**

```python
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='C:\\Users\\treyt\\OneDrive\\Desktop\\DrCodePT-Swarm\\HALF_B_WORK\\addcardtodeck.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def _log_card_addition(card, anki_result):
    """Log successful card addition"""
    logging.info(f"CARD_ADDED: {card['id']} | Course: {card['course']} | Front: {card['front'][:50]}...")
    logging.debug(f"FULL_CARD: {json.dumps(card)}")
    logging.debug(f"ANKI_RESULT: {json.dumps(anki_result)}")

def _log_error(exception):
    """Log error with full traceback"""
    logging.error(f"ERROR: {str(exception)}", exc_info=True)

def _log_duplicate(front):
    """Log duplicate detection"""
    logging.warning(f"DUPLICATE_DETECTED: {front[:50]}...")
```

**File to create:** `PROGRAMS/fastmcp-server/logging_config.py`

---

## HALF B TASK 7: Create Unit Tests (1 hour)

**What to do:**
1. Test addCardToDeck function directly
2. Test storage persistence
3. Test Anki integration
4. Test error scenarios

**Test file:**

```python
# file: test_addcardtodeck.py

import pytest
from addcardtodeck import addCardToDeck

@pytest.mark.asyncio
async def test_add_card_success():
    result = await addCardToDeck(
        course="Anatomy",
        module="Chapter 5",
        front="What is the origin of the biceps?",
        back="The supraglenoid tubercle of the scapula...",
        tags=["anatomy", "muscle"],
        difficulty="medium"
    )
    assert result["success"] == True
    assert result["cardId"] is not None

@pytest.mark.asyncio
async def test_add_card_duplicate():
    # Add first card
    await addCardToDeck(...)
    # Try to add duplicate
    result = await addCardToDeck(...)
    assert result["success"] == False
    assert "duplicate" in result["message"].lower()

@pytest.mark.asyncio
async def test_add_card_invalid_input():
    result = await addCardToDeck(
        course="",  # Invalid: empty
        module="",
        front="",
        back="",
        tags=[],
        difficulty=""
    )
    assert result["success"] == False

def test_storage_persistence():
    # Verify cards saved to disk
    import json
    import os
    deck_file = "C:\\PT School\\Anatomy\\Chapter-5\\deck.json"
    assert os.path.exists(deck_file)
    with open(deck_file) as f:
        deck = json.load(f)
    assert len(deck["cards"]) > 0
```

**File to create:** `HALF_B_WORK/test_addcardtodeck.py`

**Run tests:**
```powershell
pytest HALF_B_WORK/test_addcardtodeck.py -v
```

---

## HALF B TASK 8: End-to-End Workflow Test (1.5 hours)

**What to do:**
1. Test full ChatGPT → Anki workflow
2. Verify all 5 systems working together
3. Document results
4. Identify remaining gaps

**Test procedure:**

```markdown
# End-to-End Workflow Test

## Setup
- [ ] Anki desktop open
- [ ] ChatGPT connected to StudyMCP
- [ ] FastMCP server running
- [ ] C:\PT School\ accessible

## Test 1: Single Card via ChatGPT
1. Open ChatGPT
2. Say: "Add a flashcard to my Anatomy deck"
3. Prompt: "Question: What is the biceps?"
        "Answer: The biceps is... [long answer]"
4. Expected: Card appears in Anki within 10 seconds
5. Verify: Check C:\PT School\Anatomy\deck.json

## Test 2: Batch Cards
1. Ask ChatGPT for 5 anatomy cards about muscles
2. Expected: All 5 appear in Anki + saved to file
3. Verify: Open Anki, check "Anatomy" deck

## Test 3: Error Handling
1. Send malformed card data
2. Expected: Error message to ChatGPT
3. Verify: Log file shows error with stack trace

## Test 4: Cross-Course Cards
1. Add cards to different courses:
   - Legal & Ethics
   - Pathology
   - Lifespan Development
2. Expected: All courses have proper folder structure
3. Verify: Each course folder has unique cards

## Results
[ ] All tests passed
[ ] No errors in logs
[ ] All 5 courses have cards
[ ] Dashboard shows new cards
```

**File to create:** `HALF_B_WORK/e2e_test_results.md`

---

## HALF B TASK 9: Integration with Dashboard (0.5 hours)

**What to do:**
1. Update Dashboard API to show new cards
2. Add sync endpoint
3. Test dashboard sees cards created via ChatGPT

**Update Dashboard:**

```javascript
// In dashboard-api/api-server.js

// Add new endpoint to list cards created via ChatGPT
app.get('/api/chatgpt-cards', (req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');
        const allCards = [];
        
        // Scan all course directories
        const coursePath = 'C:\\PT School';
        const courses = fs.readdirSync(coursePath);
        
        for (const course of courses) {
            const modulePath = path.join(coursePath, course);
            const modules = fs.readdirSync(modulePath);
            
            for (const module of modules) {
                const deckFile = path.join(modulePath, module, 'deck.json');
                if (fs.existsSync(deckFile)) {
                    const deck = JSON.parse(fs.readFileSync(deckFile));
                    allCards.push(...deck.cards);
                }
            }
        }
        
        res.json({
            success: true,
            count: allCards.length,
            cards: allCards.sort((a, b) => 
                new Date(b.created) - new Date(a.created)
            )
        });
    } catch (error) {
        res.status(500).json({success: false, error: error.message});
    }
});
```

**File to update:** `IN_DEVELOPMENT/dashboard-api/api-server.js`

---

## HALF B TASK 10: Documentation & Handoff (1 hour)

**What to do:**
1. Document what was built
2. Create troubleshooting guide
3. Update STATUS.md
4. Prepare for next phase

**Files to create:**

```markdown
# HALF_B_COMPLETION_REPORT.md

## What Was Built
- ✅ addCardToDeck() function
- ✅ StudyMCP integration
- ✅ Storage layer (C:\PT School\)
- ✅ Anki integration via [method]
- ✅ Logging + error handling
- ✅ Unit tests + E2E tests
- ✅ Dashboard sync

## Tests Passed
- ✅ Single card creation
- ✅ Batch card creation
- ✅ Duplicate detection
- ✅ Error handling
- ✅ Cross-course support
- ✅ ChatGPT → Anki workflow

## Known Issues
- [List any issues found]

## Still To Do
- [List remaining work]

## Next Phase
- [What comes after]
```

**File to create:** `HALF_B_WORK/HALF_B_COMPLETION_REPORT.md`

---

## HALF B DELIVERABLES CHECKLIST

When HALF B is complete:

- [x] addcardtodeck.py - Core function
- [x] StudyMCP integration - Tool registered
- [x] storage_handler.py - File persistence
- [x] anki_handler.py - Anki connection
- [x] logging_config.py - Structured logging
- [x] test_addcardtodeck.py - Unit tests (all passing)
- [x] e2e_test_results.md - Workflow verified
- [x] Dashboard integration - Sync working
- [x] api-server.js - Updated with new endpoint
- [x] HALF_B_COMPLETION_REPORT.md - Documentation

**Created:** All files in proper locations (PROGRAMS/, IN_DEVELOPMENT/, DOCS/)

**Time investment:** ~6-8 hours

**Result:** ChatGPT → Anki workflow 100% functional

---

---

## FINAL HANDOFF

**After HALF A + HALF B:**

1. ✅ All 4 original systems still working
2. ✅ Dashboard improved with ChatGPT card sync
3. ✅ addCardToDeck tool fully implemented
4. ✅ End-to-end workflow tested
5. ✅ 48 due dates → Cards created → Anki synced
6. ✅ Full documentation for next developer

**Time total:** 12-16 hours (6-8 hours per half)

**Next phase:** Scale to production + add analytics

