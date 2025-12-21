# 🔧 TREY'S AGENT - Troubleshooting Guide

## Issues You've Encountered & Solutions

### ✅ FIXED: Login Playbook Hangs Forever

**Problem**: Login playbook hangs/spins after Yahoo opens because it ended with `keep_open` (waits forever until you close the browser).

**Solution**: ✅ **FIXED** - Removed `pause_for_user` step from `yahoo-login` playbook. Now it:
1. Opens Yahoo Mail
2. Waits for Inbox/Compose/Search to confirm login
3. Saves session state
4. Takes screenshot
5. **Returns control immediately**

**Test it**:
```
> open yahoo mail
```
Should complete in ~10-30 seconds.

---

### ✅ FIXED: Login Waits for Spam Selector

**Problem**: Login playbook waited for the Spam selector, so it often didn't detect "logged in" and kept spinning even though the inbox loaded.

**Solution**: ✅ **FIXED** - Changed wait selector to:
```
Inbox OR Compose button OR Search box
```
Now detects login success immediately when mailbox loads.

---

### ✅ FIXED: "Open Yahoo Mail" Triggers Destructive Warning

**Problem**: "Open Yahoo mail" prompted destructive confirmation because the playbook matched "Spam" in its selectors.

**Solution**: ✅ **FIXED** - Added more specific triggers to `yahoo-login`:
- "open yahoo mail"
- "go to yahoo mail"
- "check yahoo mail"
- "open my yahoo mail"

These now match **before** the spam cleanup playbook.

---

### ⚠️ PENDING: Folder Work Never Starts

**Problem**: Folder consolidation hasn't been done yet, so auto-triage can't be applied cleanly.

**Solution**: Create a folder management playbook.

**Workaround**: Use Auto mode:
```
> Auto: consolidate my Yahoo mail folders
```

---

### ✅ FIXED: IMAP Scanning Folder Name Issues

**Problem**: IMAP scanning used to fail on folder names due to bad LIST parsing/quoting.

**Status**: ✅ **FIXED** (earlier) - IMAP integration now handles quoted folder names correctly.

**Test it**:
```
> test yahoo imap
```

---

### ⚠️ IMAP Test Fails - Wrong Credentials

**Problem**: IMAP test failed due to wrong credentials (needs app password, not regular password).

**Solution**: Run the app password setup:
```
> setup yahoo app password
```

**Steps**:
1. Opens Yahoo Account Security
2. Guides you to App Passwords
3. You generate password (label it "DrCodePT")
4. Copy the password
5. Press Enter
6. Agent saves it as `yahoo_imap` credential

**Then test**:
```
> test yahoo imap
```

---

### ⚠️ PENDING: Rules Cleanup Can't Be Done via IMAP

**Problem**: "Rules cleanup" can't be done via IMAP; Yahoo rules only visible in web UI, so the agent can't read/delete them without a browser playbook.

**Solution**: Create a browser-based rules cleanup playbook (see below).

**Workaround**: Use Auto mode:
```
> Auto: open Yahoo mail settings and show me the rules
```

---

### ⚠️ Auto Mode LLM Errors/Timeouts

**Problem**: Auto mode runs sometimes fail with LLM error/timeout, so it stops immediately and doesn't troubleshoot.

**Solutions**:

#### 1. Increase Timeout
Edit `.env`:
```env
CODEX_TIMEOUT_SECONDS=900  # 15 minutes
AUTO_TIMEOUT_SECONDS=900
```

#### 2. Reduce Reasoning Effort
Edit `.env`:
```env
CODEX_REASONING_EFFORT=low  # Faster responses
```

#### 3. Reduce Max Steps
Edit `.env`:
```env
AUTO_MAX_STEPS=15  # Fewer steps = faster completion
```

#### 4. Check Codex Authentication
```powershell
codex login status
codex login  # If needed
```

#### 5. Retry with Explicit Mode
Instead of:
```
> create a python calculator
```

Try:
```
> Auto: create a python calculator
```

---

### ⚠️ PENDING: Scanning Everything Too Slow

**Problem**: Scanning everything at once was too slow; chunked scanning wasn't available until now.

**Solution**: Use IMAP with limit parameter.

**Example**: Scan only recent messages:
```python
from agent.integrations import yahoo_mail
items = yahoo_mail.list_messages(limit=10, folder='INBOX')
```

**Or use Auto mode with specific instructions**:
```
> Auto: scan the last 20 messages in my Yahoo inbox
```

---

## Common Issues & Quick Fixes

### Issue: Agent Won't Launch

**Symptoms**: Batch file fails, Python errors

**Solutions**:
1. Check virtual environment:
   ```powershell
   .venv\Scripts\activate
   python --version
   ```

2. Reinstall dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Check Python path in bootstrap file

---

### Issue: Codex CLI Not Found

**Symptoms**: "Codex CLI not found" error

**Solutions**:
1. Check installation:
   ```powershell
   Get-Command codex
   codex --version
   ```

2. Authenticate:
   ```powershell
   codex login
   ```

3. Verify ChatGPT Pro subscription is active

---

### Issue: Playwright Browser Fails

**Symptoms**: "Browser not found", "Chromium not installed"

**Solutions**:
1. Install browsers:
   ```powershell
   .venv\Scripts\activate
   playwright install chromium
   ```

2. Or install all browsers:
   ```powershell
   playwright install
   ```

3. Check `.env`:
   ```env
   AUTO_ENABLE_WEB_GUI=1
   ```

---

### Issue: Permission Denied Errors

**Symptoms**: "Access denied", "Permission denied"

**Solutions**:
1. Check file/folder permissions on the target path
2. Run as Administrator (if needed)

---

### Issue: Playbook Hangs/Spins

**Symptoms**: Playbook runs but never completes

**Solutions**:
1. Check for `pause_for_user` or `keep_open` steps
2. Verify wait selectors are correct
3. Increase timeout in playbook
4. Check browser console for errors

**Debug**:
```
> playbooks  # List all playbooks
```
Edit `agent/playbooks/index.json` to fix the playbook.

---

### Issue: Credentials Not Working

**Symptoms**: "Authentication failed", "Invalid credentials"

**Solutions**:
1. For Yahoo IMAP, use app password:
   ```
   > setup yahoo app password
   ```

2. Update credentials:
   ```
   > Cred: yahoo
   ```

3. Check saved credentials:
   ```
   > creds
   ```

4. Verify username is correct (full email address)

---

### Issue: Agent Too Slow

**Symptoms**: Takes forever to respond

**Solutions**:
1. Reduce timeout in `.env`:
   ```env
   CODEX_TIMEOUT_SECONDS=300
   ```

2. Use lighter reasoning:
   ```env
   CODEX_REASONING_EFFORT=low
   ```

3. Reduce max steps:
   ```env
   AUTO_MAX_STEPS=15
   ```

4. Use Execute mode instead of Auto:
   ```
   > create a python calculator
   ```
   Instead of:
   ```
   > Auto: create a python calculator
   ```

---

### Issue: Agent Asks Too Many Questions

**Symptoms**: Constant prompts for confirmation

**Solutions**:
1. Disable ambiguity prompts in `.env`:
   ```env
   TREYS_AGENT_PROMPT_ON_AMBIGUOUS=0
   ```

2. Set default action mode on confirmation:
   ```env
   TREYS_AGENT_DEFAULT_MODE=execute
   ```

3. Reduce prompt friction by keeping tasks specific and bounded

---

## Diagnostic Commands

### Check Agent Status
```powershell
# Launch agent
launchers\TREYS_AGENT.bat

# In agent:
> help
> playbooks
> creds
```

### Check Codex
```powershell
codex --version
codex login status
codex exec "print('Hello from Codex')"
```

### Check Playwright
```powershell
.venv\Scripts\activate
playwright --version
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### Check Python Environment
```powershell
.venv\Scripts\activate
python --version
pip list
```

### Check Dependencies
```powershell
pip install -r requirements.txt --dry-run
```

---

## Configuration Quick Reference

### Performance Settings
```env
CODEX_TIMEOUT_SECONDS=600
CODEX_REASONING_EFFORT=medium
AUTO_MAX_STEPS=30
AUTO_TIMEOUT_SECONDS=600
```

### Feature Toggles
```env
AUTO_ENABLE_WEB_GUI=1
AUTO_ENABLE_DESKTOP=1
AUTO_ALLOW_HUMAN_ASK=1
```

### Memory Settings
```env
AGENT_MEMORY_EMBED_MODEL=all-MiniLM-L6-v2
AGENT_MEMORY_FAISS_DISABLE=0
```

### Behavior Settings
```env
# Default action mode when you confirm a task
TREYS_AGENT_DEFAULT_MODE=execute
TREYS_AGENT_PROMPT_ON_AMBIGUOUS=0
```

---

## Log Files & Debugging

### Agent Logs
```
agent/runs/autonomous/[timestamp]/
├── trace.jsonl          # Detailed execution trace
├── workspace/           # Working files
└── final_result.json    # Final output
```

### Playbook Recordings
```
agent/playbooks/
├── index.json           # Playbook registry
└── [task-name]/         # Individual playbooks
```

### Memory & Credentials
```
agent/memory/
├── agent_memory.json           # General memory
├── autonomous_memory.sqlite3   # Autonomous mode memory
└── credential_store.json       # Encrypted credentials
```

### Browser Sessions
```
agent/sessions/
└── yahoo_state.json     # Saved Yahoo login session
```

---

## Getting Help

### In-Agent Help
```
> help          # Show all commands
> playbooks     # List saved tasks
> creds         # List credentials
```

### Documentation
- `START_HERE.md` - Quick start guide
- `AGENT_SETUP_GUIDE.md` - Complete setup guide
- `QUICK_REFERENCE.md` - Command reference
- `SETUP_CHECKLIST.md` - Setup checklist
- `TROUBLESHOOTING.md` - This file

### Test Commands
```powershell
# Test Codex
codex exec "print('Hello')"

# Test Agent
launchers\TREYS_AGENT.bat

# Test Playwright
.venv\Scripts\activate
playwright install --help
```

---

## Emergency Reset

If everything is broken:

### 1. Reset Virtual Environment
```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Reset Playwright
```powershell
.venv\Scripts\activate
playwright uninstall
playwright install chromium
```

### 3. Reset Codex
```powershell
codex logout
codex login
```

### 4. Reset Agent Memory (⚠️ Deletes credentials!)
```powershell
Remove-Item -Recurse -Force agent\memory\*
Remove-Item -Recurse -Force agent\sessions\*
```

### 5. Reset Playbooks (⚠️ Deletes learned tasks!)
```powershell
Remove-Item -Force agent\playbooks\index.json
```

---

## Still Having Issues?

1. **Check the error message** - Most errors are self-explanatory
2. **Review the logs** - Check `agent/runs/` for detailed traces
3. **Test components individually** - Codex, Playwright, Python
4. **Simplify the task** - Start with basic commands
5. **Check configuration** - Review `.env` settings

**Remember**: The agent is working! Most issues are configuration or credential-related.
