

# Computer Use Execution Layer

Windows desktop automation with UIA-first routing, anti-thrash guards, and download watching.

## Architecture

### Central Router (`agent/autonomous/computer_use.py`)

Single choke point for all desktop actions. Tries strategies in order:

1. **UIA (UI Automation)** - Element-based clicking via `uiautomation`/`pywinauto`
2. **Keyboard Navigation** - Ctrl+F search, Tab, Enter for visible elements
3. **Vision Coordinates** - LLM screenshot analysis → PyAutoGUI pixel clicking
4. **Ask User** - Only after 2-3 failed attempts with evidence

### Components

```
ComputerUseRouter
├── WindowsUIController      # UIA element finding
├── VisionExecutor          # Screenshot → coordinates
├── AntiThrashGuard         # Visual stall detection
└── DownloadWatcher         # File system monitoring
```

### State Machine (`agent/autonomous/google_console_flow.py`)

Deterministic Google Console OAuth flow - no free-form planning.

**States:**
- `CREDENTIALS_PAGE` - Main credentials list
- `CONSENT_SCREEN` - OAuth consent setup
- `OAUTH_CLIENT_FORM` - Create client ID form
- `CLIENT_CREATED_MODAL` - Download JSON modal
- `DONE` - Credentials downloaded
- `ERROR` / `UNKNOWN` - Recovery needed

**Action Table:**
Each state has predefined actions - no LLM planning required.

## Usage

### End-to-End Calendar Check

```bash
python check_calendar.py
```

Or programmatically:

```python
from agent.commands.check_calendar import check_calendar

success, message = check_calendar(auto_setup=True)
print(message)
```

### Manual OAuth Setup

```python
from agent.autonomous.google_console_flow import create_oauth_credentials
from pathlib import Path

dest = Path.home() / ".drcodept_swarm" / "google_calendar" / "credentials.json"

success, message = create_oauth_credentials(
    destination_path=dest,
    on_step=lambda s: print(f"Step {s['step']}: {s['state']}")
)
```

### Direct Router Usage

```python
from agent.autonomous.computer_use import get_computer_use_router

router = get_computer_use_router()

# Click with UIA fallback chain
result = router.click(
    target="CREATE CREDENTIALS",
    screenshot_path=Path("current.png"),
    step_id="step_1"
)

print(f"{result.strategy.value}: {result.message}")
```

## Anti-Thrash Features

### Visual Stall Detection

Computes perceptual hash of screenshots. If 2+ consecutive screenshots are identical:
- Forces recovery action (navigate to canonical URL)
- Prevents infinite loops

```python
router.anti_thrash.check_stalled(screenshot_path)
# Returns: (is_stalled, message)
```

### Retry Limits

Hard cap of 3 retries per step. After limit:
- Escalates to `ASK_USER` strategy
- Logs evidence for debugging

```python
router.anti_thrash.check_retry_limit("step_id")
# Returns: (exceeded, message)
```

### Download Watching

Monitors `~/Downloads` for new files:

```python
# Start watching
router.download_watcher.start_watching()

# Click download button
router.click(target="DOWNLOAD JSON")

# Wait for file
file_path = router.download_watcher.wait_for_download(
    pattern="client_secret*.json",
    timeout=30.0
)

# Move and verify
success, msg = router.download_watcher.move_and_verify(
    source=file_path,
    dest=Path("~/.drcodept_swarm/google_calendar/credentials.json"),
    required_keys=["client_id", "client_secret"]
)
```

## Strategy Selection Logic

### When to Use Each Strategy

**UIA (Preferred):**
- Element has accessible name/role
- Desktop applications (Notepad, Calculator, etc.)
- Some web elements with ARIA labels

**Keyboard Navigation:**
- Text is visible on screen
- Element reachable via Ctrl+F search
- Form fields and buttons

**Vision Coordinates:**
- UIA failed (no accessible name)
- Keyboard failed (not findable)
- Web UIs without proper ARIA
- Visual-only elements (images, canvas)

**Ask User:**
- All strategies failed 2+ times
- Visual stall detected
- Retry limit exceeded

### Execution Flow

```
┌─────────────────────┐
│  click(target="X")  │
└─────────┬───────────┘
          │
          ▼
    ┌─────────────┐     Success
    │  Try UIA    │────────────┐
    └─────┬───────┘            │
          │ Fail               │
          ▼                    │
    ┌─────────────┐     Success│
    │ Try Keyboard│────────────┤
    └─────┬───────┘            │
          │ Fail               │
          ▼                    │
    ┌─────────────┐     Success│
    │ Try Vision  │────────────┤
    └─────┬───────┘            │
          │ Fail               │
          ▼                    │
    ┌─────────────┐            │
    │  Ask User   │            │
    └─────────────┘            │
                               │
          ┌────────────────────┘
          │
          ▼
    ┌─────────────┐
    │   Return    │
    │  ActionResult│
    └─────────────┘
```

## State Machine Details

### Google Console OAuth Flow

```
START
  │
  ▼
Navigate to credentials page
  │
  ▼
Detect state → CREDENTIALS_PAGE
  │
  ├─ Click "CREATE CREDENTIALS"
  ├─ Click "OAuth client ID"
  │
  ▼
Detect state → OAUTH_CLIENT_FORM
  │
  ├─ Click "Application type"
  ├─ Click "Desktop app"
  ├─ Click "CREATE"
  │
  ▼
Detect state → CLIENT_CREATED_MODAL
  │
  ├─ Click "DOWNLOAD JSON"
  ├─ Wait for file (DownloadWatcher)
  ├─ Move to ~/.drcodept_swarm/google_calendar/
  ├─ Verify JSON structure
  │
  ▼
Detect state → DONE
  │
  ▼
END (success)
```

### Recovery Actions

If state is `UNKNOWN` or `ERROR`:

1. **Navigate to canonical URL**: `https://console.cloud.google.com/apis/credentials`
2. **Wait for page load**: 2 seconds
3. **Re-detect state**: Take new screenshot and classify

## Browser Stability

### Chrome Profile (Optional)

Set environment variables for dedicated agent profile:

```bash
export TREYS_AGENT_CHROME_USER_DATA_DIR="C:\Users\treyt\.chrome_agent"
export TREYS_AGENT_CHROME_PROFILE="Agent"
```

### Window Management

Before each screenshot/click:
- Bring Chrome to foreground
- Move to primary monitor
- Maximize window
- Ensure consistent size (1440x900)

## Logging

All actions logged with:
- Step number
- Current state
- Strategy used (UIA/keyboard/vision/ask_user)
- Result (success/failure)
- Screenshot path
- Timing information

Example log output:

```
[INFO] Step 1: State = credentials_page
[INFO]   Action: Click CREATE CREDENTIALS button
[INFO]     Result: Clicked 'CREATE CREDENTIALS' via UIA (strategy: uia)
[INFO] Step 2: State = oauth_client_form
[INFO]   Action: Click Application type dropdown
[INFO]     Result: Clicked at (450, 320) (strategy: vision)
[WARNING] Visual stall detected: 2 identical screenshots
[INFO] Executing recovery: navigating to credentials page
```

## Error Handling

### Bounded Retries

```python
MAX_STEPS = 30
MAX_IDENTICAL_SCREENSHOTS = 2
MAX_RETRIES_PER_STEP = 3
```

### Graceful Degradation

- UIA fails → try keyboard
- Keyboard fails → try vision
- Vision fails → ask user
- Never loop infinitely

### Evidence Collection

On failure, provides:
- Last 5 screenshots
- Action history
- State transitions
- Error messages

## Files

| File | Purpose |
|------|---------|
| `agent/autonomous/computer_use.py` | Central router, strategies, guards |
| `agent/autonomous/google_console_flow.py` | State machine for OAuth setup |
| `agent/commands/check_calendar.py` | End-to-end calendar check |
| `check_calendar.py` | CLI wrapper |

## Testing

### Test Calendar Access

```bash
# Full end-to-end test
python check_calendar.py
```

### Test OAuth Creation Only

```python
from agent.autonomous.google_console_flow import create_oauth_credentials
from pathlib import Path

dest = Path("./test_credentials.json")
success, msg = create_oauth_credentials(dest)
print(f"{'✓' if success else '✗'} {msg}")
```

### Test Strategy Selection

```python
from agent.autonomous.computer_use import get_computer_use_router

router = get_computer_use_router()

# Test UIA
result = router.click(target="File")
assert result.strategy.value == "uia"

# Test keyboard (for web elements)
result = router.click(target="Search")
assert result.strategy.value in ("keyboard", "vision")
```

## Performance

### Expected Timing

- **UIA click**: ~0.5s
- **Keyboard navigation**: ~1-2s
- **Vision analysis**: 5-10s (fast mode), 30-90s (reasoning mode)
- **Full OAuth flow**: 30-60s (with UIA), 90-180s (with vision fallback)

### Optimization Tips

1. **Prefer UIA**: Ensure elements have accessible names
2. **Use keyboard shortcuts**: Faster than clicking
3. **Cache screenshots**: Don't retake if state unchanged
4. **Parallel state detection**: Detect state while waiting

## Troubleshooting

### "Element not found" errors

**Cause**: Element name doesn't match
**Fix**: Check actual element name with Accessibility Insights

### "Visual stall detected"

**Cause**: UI not responding to actions
**Fix**: Increase wait times, check for modals/overlays

### "Download timeout"

**Cause**: File didn't appear in ~/Downloads
**Fix**: Check browser download settings, increase timeout

### "State detection failed"

**Cause**: Screenshot not clear or unexpected UI
**Fix**: Review screenshot, update state detection prompt

## Future Enhancements

### Phase 1 (Implemented)
- ✅ Central router
- ✅ UIA-first strategy
- ✅ Anti-thrash guards
- ✅ Download watcher
- ✅ Google Console state machine

### Phase 2 (Planned)
- ⬜ OCR integration for text-based selection
- ⬜ Multi-monitor support
- ⬜ Browser profile management
- ⬜ Coordinate refinement with retry
- ⬜ Visual feedback on clicks (debug mode)

### Phase 3 (Planned)
- ⬜ Learning from successful patterns
- ⬜ Coordinate cache for common elements
- ⬜ Multi-agent perception/action separation
- ⬜ Direct vision API integration (no subprocess)
