# Phase 2C Helper Functions - Code Added to server.py

## Location in File
**File:** `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\tools\anatomy_mcp\server.py`  
**Lines:** 520-670 (ADDED)  
**Placed:** Before the `if __name__ == "__main__":` block

---

## Function 1: _validate_card()

```python
def _validate_card(card: dict) -> dict:
    """
    Validate card structure before adding to deck.
    
    Required fields:
    - front: string (1-10000 chars)
    - back: string (1-10000 chars)
    - tags: list of strings (optional)
    - course: string (required, non-empty)
    - module: string (required, non-empty)
    - deck: string (required, non-empty)
    - difficulty: string (optional, defaults to 'medium')
    
    Returns: {"valid": bool, "error": str or None}
    """
```

**Purpose:** Validates all card fields before processing

**Returns:**
```python
{"valid": True, "error": None}  # If valid
{"valid": False, "error": "error message"}  # If invalid
```

---

## Function 2: _sanitize_text()

```python
def _sanitize_text(text: str) -> str:
    """
    Sanitize text by removing control characters and normalizing whitespace.
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Replace carriage returns with newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove control characters except newlines and tabs
    text = ''.join(c if ord(c) >= 32 or c in '\n\t' else ' ' for c in text)
    
    # Normalize whitespace (collapse multiple spaces)
    text = ' '.join(text.split())
    
    return text.strip()
```

**Purpose:** Cleans text for safe storage in JSON

**Handles:**
- Windows line breaks (\r\n → \n)
- Control characters → spaces
- Multiple spaces → single space
- Leading/trailing whitespace

---

## Function 3: _get_iso_timestamp()

```python
def _get_iso_timestamp() -> str:
    """Get current timestamp in ISO 8601 format."""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"
```

**Purpose:** Returns consistent timestamp format

**Returns:** `"2025-11-11T12:34:56.789123Z"`

---

## Function 4: _update_decks_index()

```python
def _update_decks_index(index_path: Path, deck_path: Path, deck_name: str, 
                       card_count: int, course: str) -> None:
    """
    Update or create the course-level _decks-index.json file.
    
    Structure:
    {
        "course": "Anatomy",
        "lastModified": "2025-11-11T12:34:56Z",
        "decks": [
            {
                "path": "C:\\PT School\\Anatomy\\Gluteal-Region\\deck.json",
                "name": "Week-9-Gluteal",
                "module": "Gluteal-Region",
                "cardCount": 15,
                "created": "2025-11-11T12:00:00Z",
                "lastModified": "2025-11-11T12:34:56Z"
            }
        ]
    }
    """
```

**Purpose:** Tracks all decks in a course (index file)

**Creates:** `{course_dir}/_decks-index.json`

**Updates:** Card count and timestamp each time a card is added

---

## How These Are Used in addCardToDeck()

```
Step 1: _validate_card(card)
        ↓
Step 2: Extract course/module/deck fields
        ↓
Step 3: Create directories (module_dir.mkdir)
        ↓
Step 4: Load or create deck.json
        ↓
Step 5: _sanitize_text() on front/back
        ↓
Step 6: Add card to deck["cards"]
        ↓
Step 7: Save deck.json with json.dump()
        ↓
Step 8: _update_decks_index() to track deck
        ↓
Step 9: _get_iso_timestamp() for all timestamps
        ↓
Return: Success response with paths and counts
```

---

## Integration Points

### In addCardToDeck() - Line ~301-360:

```python
# Step 1: Validate
validation = _validate_card(card)
if not validation["valid"]:
    return {"success": False, "message": ...}

# Step 5: Sanitize
new_card = {
    "front": _sanitize_text(card.get("front", "")),
    "back": _sanitize_text(card.get("back", "")),
    "added": _get_iso_timestamp()
}

# Step 10: Update index
_update_decks_index(index_path, deck_path, deck_name, 
                   len(deck["cards"]), course)
```

---

## Testing Each Function

### Test _validate_card():
```python
result = _validate_card({"front": "Q", "back": "A", "course": "Anatomy", 
                         "module": "Intro", "deck": "Week-1"})
print(result["valid"])  # True
```

### Test _sanitize_text():
```python
dirty = "Text  with\r\ncontrol\x00chars"
clean = _sanitize_text(dirty)
print(clean)  # "Text with control chars"
```

### Test _get_iso_timestamp():
```python
ts = _get_iso_timestamp()
print(ts)  # "2025-11-11T12:34:56.789123Z"
```

### Test _update_decks_index():
```python
_update_decks_index(
    Path("C:/PT School/Anatomy/_decks-index.json"),
    Path("C:/PT School/Anatomy/Intro/deck.json"),
    "Week-1",
    1,
    "Anatomy"
)
# Creates or updates _decks-index.json
```

---

## Error Handling

All functions handle errors gracefully:

- `_validate_card()` - Returns error dict if validation fails
- `_sanitize_text()` - Never fails (coerces to string)
- `_get_iso_timestamp()` - Never fails (uses built-in datetime)
- `_update_decks_index()` - Prints warning if file update fails (non-blocking)

The `addCardToDeck()` tool wraps everything in try/except and returns full traceback on error.

---

## Total Lines Added

- `_validate_card()`: ~56 lines
- `_sanitize_text()`: ~12 lines
- `_get_iso_timestamp()`: ~4 lines
- `_update_decks_index()`: ~51 lines
- Documentation/comments: ~37 lines

**Total: ~160 lines added to server.py**
