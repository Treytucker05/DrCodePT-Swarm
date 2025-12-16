# HALF B EXECUTION CHECKLIST
**Status:** ✅ ALL CODE COMPLETE - READY TO EXECUTE  
**Date:** November 12, 2025  
**Timeline:** 3-4 hours to completion

---

## 🎯 WHAT'S READY

✅ **addcardtodeck.py** - Production-ready (515 lines, fully documented)  
✅ **test_addcardtodeck.py** - Complete test suite (355 lines, 15+ test cases)  
✅ **SERVER_PY_INTEGRATION.md** - Integration instructions (271 lines)  
✅ **Decisions locked in:**
  - Per-module duplicate detection ✅
  - Hierarchical deck naming "Course::Module" ✅
  - Hybrid bridge: AnkiConnect → deck.json → pending.json queue ✅
  - All code written and ready to execute ✅

---

## 📋 EXECUTION PHASES (Do These in Order)

### PHASE 1: PRE-FLIGHT CHECKS (30 minutes)

**What to verify before running any code:**

```powershell
# 1. Python environment
python --version                    # Should be 3.8+
pip list | findstr fastmcp requests # Should both be present

# 2. Verify .env exists
cat "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server\.env"
# Should include:
# ANKI_HOST=127.0.0.1
# ANKI_PORT=8765
# PT_SCHOOL_PATH=C:\PT School

# 3. Check AnkiConnect connectivity
# (Anki must be open with AnkiConnect plugin)
curl -X POST http://127.0.0.1:8765 -H "Content-Type: application/json" `
  -d '{"action": "deckNames", "version": 6}'
# Should return: {"result": [...], "error": null}

# 4. Verify ngrok tunnel
curl http://localhost:8000/health
# Should return JSON health status

# 5. Verify C:\PT School\ exists
Get-ChildItem "C:\PT School\" -Directory
# Should show: Anatomy, Legal-and-Ethics, Lifespan-Development, Clinical-Pathology, PT-Examination-Skills
```

**Checklist:**
- [ ] Python 3.8+ installed
- [ ] FastMCP + requests packages installed
- [ ] .env file exists with ANKI_HOST/PORT
- [ ] AnkiConnect responds to HTTP requests
- [ ] ngrok tunnel to FastMCP running
- [ ] C:\PT School\ exists with all 5 course directories

**If any checks fail:** Stop and fix before proceeding to Phase 2.

---

### PHASE 2: RUN TEST SUITE (30 minutes)

**This validates the code before integrating into server.py:**

```powershell
cd "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server"

# Install pytest if needed
pip install pytest pytest-asyncio

# Run tests
pytest test_addcardtodeck.py -v -s

# Expected output:
# test_validate_input_valid PASSED ✓
# test_validate_input_short_course PASSED ✓
# test_validate_input_short_front PASSED ✓
# test_validate_input_short_back PASSED ✓
# test_validate_input_empty_tags PASSED ✓
# test_duplicate_detection_first_card PASSED ✓
# test_duplicate_detection_per_module PASSED ✓
# test_duplicate_detection_different_modules_allowed PASSED ✓
# test_get_deck_path PASSED ✓
# test_card_persistence_to_disk PASSED ✓
# test_error_handling_all_invalid_input PASSED ✓
# test_error_handling_special_characters PASSED ✓
# test_workflow_five_cards_same_module PASSED ✓
# test_workflow_multiple_modules PASSED ✓
#
# ==================== 14 passed in X.XXs ====================
```

**Checklist:**
- [ ] All 14 tests passing
- [ ] No import errors
- [ ] No file permission errors
- [ ] C:\PT School\ now has Test-Course and Integration-Test folders (created by tests)

**If tests fail:** Check error message, see TROUBLESHOOTING section below.

---

### PHASE 3: INTEGRATE INTO server.py (30 minutes)

**Add addCardToDeck to your FastMCP server:**

1. **Copy the integration code:**
   - Open: `SERVER_PY_INTEGRATION.md`
   - Copy the code snippets
   - Paste into `PROGRAMS/fastmcp-server/server.py`

2. **Exact location to add imports:**
   ```python
   # At the TOP of server.py with other imports:
   from addcardtodeck import (
       addCardToDeck as add_card_to_deck,
       retry_pending_cards,
       get_pending_cards_count
   )
   ```

3. **Exact location to add tool definitions:**
   ```python
   # WHERE YOUR OTHER TOOLS ARE DEFINED (list_modules, search_facts, etc)
   @mcp_server.define_tool
   async def addCardToDeck(...):
       # Copy from SERVER_PY_INTEGRATION.md
   ```

4. **Verify syntax:**
   ```powershell
   python -m py_compile "PROGRAMS/fastmcp-server/server.py"
   # If no error: Python syntax is valid
   ```

**Checklist:**
- [ ] Import statement added at top of server.py
- [ ] addCardToDeck tool registered
- [ ] retryPendingCards tool registered (optional but recommended)
- [ ] getPendingCardsCount tool registered (optional but recommended)
- [ ] File has no syntax errors (py_compile passes)

---

### PHASE 4: START SERVER & VERIFY TOOLS (15 minutes)

**Start FastMCP server with new tool:**

```powershell
cd "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\PROGRAMS\fastmcp-server"

# Start server
python server.py

# Expected output (in server logs):
# INFO: ✅ addCardToDeck module loaded successfully
# INFO: ✅ PT School path verified: C:\PT School
# INFO: Server running on http://localhost:8000
```

**Verify in new PowerShell window:**

```powershell
# Test tool is registered
curl -X GET http://localhost:8000/api/tools/available

# Expected response includes:
# {
#   "tools": [
#     "list_modules",
#     "ingest_module",
#     "search_facts",
#     "export_module",
#     "addCardToDeck",          # NEW
#     "retryPendingCards",      # NEW
#     "getPendingCardsCount"    # NEW
#   ]
# }
```

**Checklist:**
- [ ] Server starts without errors
- [ ] No import errors in logs
- [ ] addCardToDeck tool shows in /api/tools/available
- [ ] ngrok tunnel still active

---

### PHASE 5: MANUAL END-TO-END TEST (45 minutes)

**Test the complete workflow:**

#### Test 1: Add Card via HTTP (Simulating ChatGPT)

```powershell
# In new PowerShell window, with server running:

# Single card test
curl -X POST http://localhost:8000/addCardToDeck `
  -H "Content-Type: application/json" `
  -d @- << EOF
{
  "course": "Anatomy",
  "module": "Chapter 5 - Muscles",
  "front": "What is the origin of the biceps?",
  "back": "The long head originates from the supraglenoid tubercle of the scapula; the short head from the coracoid process.",
  "tags": ["anatomy", "biceps", "upper-arm"],
  "difficulty": "medium",
  "source": "test"
}
EOF

# Expected response:
# {
#   "success": true,
#   "cardId": "abc123...",
#   "message": "Card added to Anki (live sync)",
#   "ankiStatus": "added_to_anki",
#   "errors": []
# }
```

#### Test 2: Verify in Anki

```
1. Open Anki desktop
2. Look for deck: "Anatomy::Chapter 5 - Muscles"
3. Should contain the biceps card you just added
4. Expected: Card appears within 5 seconds
```

#### Test 3: Verify on Disk

```powershell
# Check C:\PT School\
Get-ChildItem "C:\PT School\Anatomy\Chapter-5-Muscles\deck.json"

# Read the file
Get-Content "C:\PT School\Anatomy\Chapter-5-Muscles\deck.json" | ConvertFrom-Json | Select-Object -ExpandProperty cards | Select-Object id, front, created
```

#### Test 4: Test Duplicate Detection

```powershell
# Try to add same card again
curl -X POST http://localhost:8000/addCardToDeck `
  -H "Content-Type: application/json" `
  -d @- << EOF
{
  "course": "Anatomy",
  "module": "Chapter 5 - Muscles",
  "front": "What is the origin of the biceps?",
  "back": "The long head originates from the supraglenoid tubercle of the scapula; the short head from the coracoid process.",
  "tags": ["anatomy", "biceps"],
  "difficulty": "medium"
}
EOF

# Expected response:
# {
#   "success": false,
#   "cardId": "abc123...",
#   "message": "Card already exists in Chapter 5 - Muscles",
#   "ankiStatus": "duplicate",
#   "errors": ["Duplicate card in this module"]
# }
```

#### Test 5: Test Offline Fallback (Simulate Anki being down)

```powershell
# 1. Close Anki desktop
# 2. Send another card:
curl -X POST http://localhost:8000/addCardToDeck `
  -H "Content-Type: application/json" `
  -d @- << EOF
{
  "course": "Anatomy",
  "module": "Chapter 5 - Muscles",
  "front": "What is the insertion of the triceps?",
  "back": "The triceps inserts on the olecranon process of the ulna.",
  "tags": ["anatomy", "triceps"],
  "difficulty": "medium"
}
EOF

# Expected response:
# {
#   "success": true,
#   "cardId": "xyz789...",
#   "message": "Card saved locally (AnkiConnect offline)",
#   "ankiStatus": "saved_local",
#   "errors": []
# }

# 3. Verify on disk (card should be saved):
Get-Content "C:\PT School\Anatomy\Chapter-5-Muscles\deck.json" | ConvertFrom-Json | Select-Object -ExpandProperty cards | Measure-Object
# Should now have 2 cards
```

**Test Checklist:**
- [ ] Test 1: HTTP request succeeds
- [ ] Test 2: Card appears in Anki within 5 seconds
- [ ] Test 3: Card saved to deck.json with correct content
- [ ] Test 4: Duplicate correctly rejected
- [ ] Test 5: Offline fallback works (saved_local status)

---

### PHASE 6: TEST IN CHATGPT (30 minutes)

**Now test the real workflow via ChatGPT:**

1. **Open ChatGPT** (with StudyMCP connected)

2. **Send this message:**
   ```
   Create 3 flashcards for my Anatomy deck about the shoulder muscles:
   1. Origin of the deltoid
   2. Insertion of the rotator cuff
   3. Action of the supraspinatus
   ```

3. **Expected behavior:**
   - ChatGPT calls addCardToDeck for each card
   - Cards appear in Anki within 5 seconds (or saved locally if Anki offline)
   - Dashboard shows new cards if you refresh
   - Logging shows successful card additions

4. **Verify cards were created:**
   ```powershell
   # Check logs
   cat "PROGRAMS/fastmcp-server/addcardtodeck.log" | tail -20
   # Should show: CARD_ADDED_VIA_API or CARD_SAVED_LOCAL entries
   
   # Check Anki
   # Deck: Anatomy::Chapter X (whatever ChatGPT chose)
   # Should have new cards
   ```

**ChatGPT Test Checklist:**
- [ ] ChatGPT successfully calls addCardToDeck tool
- [ ] No errors in ChatGPT response
- [ ] Cards appear in Anki (or saved locally)
- [ ] Logs show success entries

---

## ✅ SUCCESS CRITERIA (All must be true)

- [ ] All 14 unit tests passing
- [ ] Server starts without errors
- [ ] Tool appears in /api/tools/available
- [ ] Manual HTTP test creates card
- [ ] Card appears in Anki (or saved_local if Anki offline)
- [ ] Card persists to deck.json
- [ ] Duplicate detection works
- [ ] Offline fallback works
- [ ] ChatGPT successfully calls tool
- [ ] Cards visible in Anki/Dashboard after ChatGPT request

**When all 10 above are checked: HALF B is COMPLETE ✅**

---

## 🔧 TROUBLESHOOTING

### "ModuleNotFoundError: No module named 'addcardtodeck'"
**Solution:** Make sure addcardtodeck.py is in the same directory as server.py:
```powershell
Get-ChildItem "PROGRAMS/fastmcp-server" -Filter "addcardtodeck.py"
```

### "AnkiConnect timeout" or "connection refused"
**Solution:** Anki must be running with AnkiConnect plugin installed:
```
1. Open Anki desktop
2. Tools → Add-ons → Get Add-ons → Search "AnkiConnect"
3. Restart Anki
4. Test: curl -X POST http://127.0.0.1:8765 ...
```

### "Test database locked" error
**Solution:** Don't run tests while server is running (different database access):
```powershell
# Stop server first
# Run tests
# Restart server
```

### Cards saving to deck.json but not appearing in Anki
**Solution:** This is expected if Anki is offline. Once Anki comes back online:
```powershell
# Call retry endpoint
curl -X POST http://localhost:8000/retryPendingCards
```

### Permission denied writing to C:\PT School\
**Solution:** Check folder permissions:
```powershell
# Verify write access
Test-Path "C:\PT School\" -PathType Container
icacls "C:\PT School\"
# Should show your user with full permissions (F)
```

---

## 📊 TIMELINE

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Pre-flight checks | 30 min | Ready |
| 2 | Run test suite | 30 min | Ready |
| 3 | Integrate into server.py | 30 min | Ready |
| 4 | Start server & verify | 15 min | Ready |
| 5 | Manual E2E tests | 45 min | Ready |
| 6 | ChatGPT workflow test | 30 min | Ready |
| **Total** | **Complete HALF B** | **3-4 hours** | **Ready to execute** |

---

## 🚀 YOU'RE READY

**All code is written. All tests are defined. All integration points are documented.**

**Next step:** Start with PHASE 1 (Pre-flight checks).

**Questions?** Check SERVER_PY_INTEGRATION.md or TROUBLESHOOTING section above.

**Good luck! 🎉**

