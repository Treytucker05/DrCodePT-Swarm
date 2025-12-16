# HALF B IMPLEMENTATION PLAN - Anki Bridge + addCardToDeck
**Created:** November 12, 2025  
**Based on:** HALF A findings (hybrid Anki bridge approach)  
**Target:** ChatGPT → addCardToDeck → Anki working by end of session

---

## 🎯 THE HYBRID ANKI BRIDGE STRATEGY

You decided on **hybrid approach**: 
- Primary: Try AnkiConnect API (live Anki desktop update)
- Secondary: Fallback to deck.json file writes (offline OK)
- Result: System works whether Anki is running or not

```
ChatGPT Request
    ↓
addCardToDeck(front, back, tags, course, module)
    ↓
1. Validate + hash check (duplicate detection)
    ↓
2. Try AnkiConnect API (if running on :8765)
    ├─ Success → Card in Anki instantly ✅
    └─ Failure → Continue to step 3
    ↓
3. Fallback: Write to deck.json + audit log
    ├─ Success → Card saved locally ✅
    └─ Failure → Return error + log
    ↓
Dashboard syncs from disk (always has latest)
```

---

## 📋 PHASE 1: PRE-IMPLEMENTATION CHECKLIST (30 minutes)

### Step 1: Verify Current .env
```powershell
# Check PROGRAMS/fastmcp-server/.env exists and has:
Get-Content "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server\.env"

# Should include:
# ANKI_HOST=127.0.0.1
# ANKI_PORT=8765
# PT_SCHOOL_PATH=C:\PT School
# NGROK_TUNNEL=[your tunnel URL]
```

### Step 2: Verify Python Dependencies
```powershell
cd "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server"
python -m pip list | findstr /i "fastmcp requests sqlalchemy"

# If missing, install:
pip install fastmcp requests sqlalchemy
```

### Step 3: Check AnkiConnect Connectivity
```powershell
# Test if Anki desktop is running with AnkiConnect
# (Anki must be open + AnkiConnect plugin installed)

powershell -Command "
try {
    \$response = Invoke-WebRequest -Uri 'http://127.0.0.1:8765' -TimeoutSec 2
    Write-Host '✅ AnkiConnect reachable'
} catch {
    Write-Host '⚠️  AnkiConnect not responding (will use file-based fallback)'
}
"
```

### Step 4: Verify ngrok Tunnel
```powershell
# Check if ngrok tunnel to FastMCP is active
curl -X GET http://localhost:8000/health

# Should return JSON health status
```

### Step 5: Verify C:\PT School Structure
```powershell
# Check directories exist for all 5 courses
Get-ChildItem "C:\PT School" -Directory | Select-Object Name
# Should show: Anatomy, Legal-and-Ethics, Lifespan-Development, Clinical-Pathology, PT-Examination-Skills
```

**Checklist completion:** All 5 steps passing ✅

---

## 🔨 PHASE 2: IMPLEMENT addCardToDeck FUNCTION

### File: `PROGRAMS/fastmcp-server/addcardtodeck.py`

```python
"""
addCardToDeck - Hybrid Anki bridge (API + file fallback)
Implements the specification from HALF A findings.
"""

import hashlib
import json
import os
import requests
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    filename='addcardtodeck.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CardAdditionError(Exception):
    """Raised when card addition fails"""
    pass

async def addCardToDeck(
    course: str,
    module: str,
    front: str,
    back: str,
    tags: list,
    difficulty: str = "medium",
    source: str = "chatgpt"
) -> dict:
    """
    Add a card to Anki deck via hybrid bridge (AnkiConnect + fallback).
    
    Args:
        course: Course name (e.g., "Anatomy")
        module: Module/chapter (e.g., "Chapter 5")
        front: Card front (question)
        back: Card back (answer)
        tags: List of tags (e.g., ["anatomy", "muscles"])
        difficulty: "easy" | "medium" | "hard"
        source: Origin of card request
    
    Returns:
        {
            "success": bool,
            "cardId": str (hash-based ID),
            "message": str,
            "ankiStatus": str ("added_to_anki" | "saved_local" | "error"),
            "errors": list[str]
        }
    """
    try:
        # ============================================================
        # 1. VALIDATE INPUT
        # ============================================================
        validation_errors = _validate_input(course, module, front, back, tags)
        if validation_errors:
            return _error_response("Validation failed", validation_errors, "error")
        
        # ============================================================
        # 2. GENERATE CARD ID (SHA256 hash)
        # ============================================================
        card_id = hashlib.sha256(f"{front}|{back}".encode()).hexdigest()[:16]
        
        card_obj = {
            "id": card_id,
            "course": course,
            "module": module,
            "front": front,
            "back": back,
            "tags": tags,
            "difficulty": difficulty,
            "source": source,
            "created": datetime.now().isoformat(),
            "hash": hashlib.sha256(f"{front}|{back}".encode()).hexdigest()
        }
        
        # ============================================================
        # 3. CHECK FOR DUPLICATES (in local storage)
        # ============================================================
        if _card_exists(card_obj):
            logging.warning(f"DUPLICATE_DETECTED: {card_id}")
            return {
                "success": False,
                "cardId": card_id,
                "message": "Card with identical front/back already exists",
                "ankiStatus": "duplicate",
                "errors": ["Duplicate card"]
            }
        
        # ============================================================
        # 4. PRIMARY METHOD: Try AnkiConnect API
        # ============================================================
        anki_result = _try_anki_connect(card_obj)
        if anki_result["success"]:
            logging.info(f"CARD_ADDED_VIA_API: {card_id}")
            _save_to_disk(card_obj, "api_primary")
            return {
                "success": True,
                "cardId": card_id,
                "message": "Card added to Anki via API",
                "ankiStatus": "added_to_anki",
                "errors": []
            }
        
        # ============================================================
        # 5. FALLBACK METHOD: Save to deck.json
        # ============================================================
        storage_result = _save_to_disk(card_obj, "fallback")
        if storage_result["success"]:
            logging.info(f"CARD_SAVED_LOCAL: {card_id} (AnkiConnect offline)")
            return {
                "success": True,
                "cardId": card_id,
                "message": "Card saved locally (AnkiConnect offline)",
                "ankiStatus": "saved_local",
                "errors": []
            }
        
        # ============================================================
        # 6. BOTH METHODS FAILED
        # ============================================================
        logging.error(f"CARD_ADD_FAILED: {card_id} - {storage_result['error']}")
        return _error_response(
            "Failed to add card (both API and storage failed)",
            [storage_result['error']],
            "error"
        )
        
    except Exception as e:
        logging.error(f"UNEXPECTED_ERROR: {str(e)}", exc_info=True)
        return _error_response(f"Unexpected error: {str(e)}", [str(e)], "error")


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def _validate_input(course, module, front, back, tags):
    """Validate all input parameters"""
    errors = []
    
    if not course or not isinstance(course, str) or len(course) < 2:
        errors.append("course must be non-empty string (min 2 chars)")
    if not module or not isinstance(module, str) or len(module) < 2:
        errors.append("module must be non-empty string (min 2 chars)")
    if not front or not isinstance(front, str) or len(front) < 5:
        errors.append("front must be at least 5 characters")
    if not back or not isinstance(back, str) or len(back) < 10:
        errors.append("back must be at least 10 characters")
    if not isinstance(tags, list) or len(tags) == 0:
        errors.append("tags must be non-empty list")
    
    return errors


def _card_exists(card_obj):
    """Check if card hash already exists in storage"""
    try:
        course = card_obj["course"].replace(" & ", "-").replace(" ", "-")
        module = card_obj["module"].replace(" ", "-")
        deck_path = f"C:\\PT School\\{course}\\{module}\\deck.json"
        
        if not os.path.exists(deck_path):
            return False
        
        with open(deck_path, 'r', encoding='utf-8') as f:
            deck = json.load(f)
        
        card_hash = card_obj["hash"]
        for existing_card in deck.get("cards", []):
            if existing_card.get("hash") == card_hash:
                return True
        
        return False
    except Exception as e:
        logging.error(f"DUPLICATE_CHECK_ERROR: {str(e)}")
        return False


def _try_anki_connect(card_obj):
    """Try to add card via AnkiConnect API"""
    try:
        url = "http://127.0.0.1:8765"
        
        payload = {
            "action": "addNote",
            "version": 6,
            "params": {
                "note": {
                    "deckName": f"{card_obj['course']}::{card_obj['module']}",
                    "modelName": "Basic",
                    "fields": {
                        "Front": card_obj["front"],
                        "Back": card_obj["back"]
                    },
                    "tags": card_obj["tags"]
                }
            }
        }
        
        response = requests.post(url, json=payload, timeout=2)
        result = response.json()
        
        if result.get("error"):
            return {"success": False, "error": result["error"]}
        
        return {
            "success": True,
            "noteId": result.get("result"),
            "method": "AnkiConnect API"
        }
    
    except requests.exceptions.Timeout:
        return {"success": False, "error": "AnkiConnect timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "AnkiConnect connection refused"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _save_to_disk(card_obj, method="fallback"):
    """Save card to deck.json file"""
    try:
        course = card_obj["course"].replace(" & ", "-").replace(" ", "-")
        module = card_obj["module"].replace(" ", "-")
        
        course_path = f"C:\\PT School\\{course}"
        module_path = os.path.join(course_path, module)
        deck_file = os.path.join(module_path, "deck.json")
        
        # Create directories if needed
        os.makedirs(module_path, exist_ok=True)
        
        # Load or create deck
        if os.path.exists(deck_file):
            with open(deck_file, 'r', encoding='utf-8') as f:
                deck = json.load(f)
        else:
            deck = {
                "course": card_obj["course"],
                "module": card_obj["module"],
                "cards": []
            }
        
        # Add card
        deck["cards"].append({
            "id": card_obj["id"],
            "front": card_obj["front"],
            "back": card_obj["back"],
            "tags": card_obj["tags"],
            "difficulty": card_obj["difficulty"],
            "source": card_obj["source"],
            "created": card_obj["created"],
            "hash": card_obj["hash"]
        })
        
        # Save to file
        with open(deck_file, 'w', encoding='utf-8') as f:
            json.dump(deck, f, indent=2, ensure_ascii=False)
        
        logging.info(f"SAVED_TO_DISK: {deck_file} via {method}")
        return {"success": True, "path": deck_file}
        
    except Exception as e:
        logging.error(f"DISK_SAVE_ERROR: {str(e)}")
        return {"success": False, "error": str(e)}


def _error_response(message, errors, status):
    """Format error response"""
    logging.error(f"ERROR_RESPONSE: {message} | Errors: {errors}")
    return {
        "success": False,
        "cardId": None,
        "message": message,
        "ankiStatus": status,
        "errors": errors
    }
```

---

## 📌 PHASE 3: INTEGRATE INTO FastMCP SERVER

### File: `PROGRAMS/fastmcp-server/server.py` (Add this section)

```python
# At the top of server.py, add:
from addcardtodeck import addCardToDeck as add_card_to_deck

# Register the tool in your MCP tools list:
@mcp_server.define_tool
async def addCardToDeck(
    course: str,
    module: str,
    front: str,
    back: str,
    tags: list,
    difficulty: str = "medium",
    source: str = "chatgpt"
) -> dict:
    """
    Add a flashcard to Anki deck.
    
    This tool creates a new flashcard and adds it to your Anki deck.
    It uses a hybrid approach: tries AnkiConnect API first, falls back 
    to local file storage if Anki is offline.
    """
    return await add_card_to_deck(course, module, front, back, tags, difficulty, source)

# Test that it's registered
@mcp_server.define_tool
async def listMCPTools() -> dict:
    """List all available MCP tools"""
    return {
        "tools": [
            "list_modules",
            "ingest_module", 
            "search_facts",
            "export_module",
            "addCardToDeck"  # NEW
        ]
    }
```

---

## 🧪 PHASE 4: TEST SUITE

### File: `test_addcardtodeck.py`

```python
"""
Test suite for addCardToDeck hybrid bridge
"""

import pytest
import asyncio
import os
import json
from addcardtodeck import addCardToDeck

@pytest.mark.asyncio
async def test_add_card_success():
    """Test successful card addition"""
    result = await addCardToDeck(
        course="Anatomy",
        module="Chapter 5",
        front="What is the origin of the biceps?",
        back="The long head originates from the supraglenoid tubercle of the scapula; the short head from the coracoid process.",
        tags=["anatomy", "muscle", "biceps"],
        difficulty="medium"
    )
    assert result["success"] == True
    assert result["cardId"] is not None
    print(f"✅ Card added: {result['cardId']} (via {result['ankiStatus']})")


@pytest.mark.asyncio
async def test_add_card_duplicate():
    """Test duplicate detection"""
    front = "What is the origin of the biceps?"
    back = "The long head originates from the supraglenoid tubercle of the scapula; the short head from the coracoid process."
    
    # Add first
    result1 = await addCardToDeck(
        course="Anatomy",
        module="Chapter 5",
        front=front,
        back=back,
        tags=["anatomy"],
        difficulty="medium"
    )
    assert result1["success"] == True
    
    # Try to add duplicate
    result2 = await addCardToDeck(
        course="Anatomy",
        module="Chapter 5",
        front=front,
        back=back,
        tags=["anatomy"],
        difficulty="medium"
    )
    assert result2["success"] == False
    assert "duplicate" in result2["ankiStatus"].lower()
    print("✅ Duplicate detection working")


@pytest.mark.asyncio
async def test_add_card_invalid_input():
    """Test invalid input handling"""
    result = await addCardToDeck(
        course="",  # Invalid
        module="",
        front="",
        back="",
        tags=[],
        difficulty=""
    )
    assert result["success"] == False
    assert len(result["errors"]) > 0
    print("✅ Input validation working")


def test_storage_persistence():
    """Test cards are saved to disk"""
    deck_file = "C:\\PT School\\Anatomy\\Chapter-5\\deck.json"
    if os.path.exists(deck_file):
        with open(deck_file, 'r') as f:
            deck = json.load(f)
        assert len(deck["cards"]) > 0
        print(f"✅ Persistence verified: {len(deck['cards'])} cards on disk")


@pytest.mark.asyncio
async def test_error_handling():
    """Test error scenarios"""
    # Very short inputs
    result = await addCardToDeck(
        course="X",  # Too short
        module="Y",  # Too short
        front="Hi",  # Too short
        back="OK",   # Too short
        tags=["tag"],
        difficulty="medium"
    )
    assert result["success"] == False
    print("✅ Error handling working")


if __name__ == "__main__":
    # Run with: pytest test_addcardtodeck.py -v
    pytest.main([__file__, "-v", "-s"])
```

**Run tests:**
```powershell
cd "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server"
pytest test_addcardtodeck.py -v -s
```

---

## 🔍 PHASE 5: END-TO-END WORKFLOW TEST

### Manual Test Script

```powershell
# Step 1: Start FastMCP server
cd "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server"
python server.py
# Wait for: "Server running on http://localhost:8000"

# Step 2: Test API endpoint
curl -X POST http://localhost:8000/addCardToDeck `
  -H "Content-Type: application/json" `
  -d @- << EOF
{
  "course": "Anatomy",
  "module": "Chapter 5",
  "front": "What is the gluteus maximus?",
  "back": "The gluteus maximus is the largest and most superficial of the gluteal muscles...",
  "tags": ["anatomy", "glutes"],
  "difficulty": "easy"
}
EOF

# Step 3: Open ChatGPT + test natural language
# Say: "Add a card to my Anatomy deck about the biceps muscle"
# Expected: Card appears in Anki (or saved locally if offline)

# Step 4: Verify in Anki
# Open Anki desktop
# Check: Anatomy::Chapter 5 deck has the new card

# Step 5: Verify on disk
Get-Content "C:\PT School\Anatomy\Chapter-5\deck.json" | ConvertFrom-Json | % { $_.cards | Measure-Object }
# Should show: Count=X (where X is number of cards added)
```

---

## 📊 PHASE 6: DEPLOYMENT CHECKLIST

Before calling HALF B complete:

- [ ] addcardtodeck.py created + no syntax errors
- [ ] Integrated into server.py + tool registered
- [ ] Test suite runs: `pytest test_addcardtodeck.py -v` (all pass)
- [ ] Manual E2E test: ChatGPT → addCardToDeck → Anki ✅
- [ ] Cards persist to C:\PT School\ ✅
- [ ] Duplicate detection working ✅
- [ ] Fallback (offline Anki) working ✅
- [ ] Logging auditable (`addcardtodeck.log` exists + entries)
- [ ] Updated STATUS.md with completion notes

---

## 🎯 SUCCESS CRITERIA

**HALF B is complete when:**

1. ✅ addCardToDeck tool callable from ChatGPT
2. ✅ Cards save to Anki when Anki is open
3. ✅ Cards save to deck.json when Anki is offline
4. ✅ Duplicates rejected correctly
5. ✅ All test scenarios passing
6. ✅ E2E workflow: ChatGPT → Anki verified
7. ✅ Documentation updated
8. ✅ Anatomy/Exam Skills dates refreshed from Blackboard

---

**Timeline:** 4-6 hours (code + test + E2E)  
**Owner:** HALF B developer  
**Blocker:** None identified  
**Ready to start:** YES

