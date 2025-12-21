# ✅ TREY'S AGENT - Setup Checklist

## Pre-Flight Checklist

### ✅ Core Requirements
- [x] Python virtual environment (`.venv`)
- [x] Dependencies installed (`requirements.txt`)
- [x] Codex CLI installed (`codex.ps1`)
- [x] Agent launcher (`launchers\TREYS_AGENT.bat`)
- [x] Configuration file (`.env`)

### ⚠️ Optional Setup (Recommended)

#### 1. Authenticate Codex CLI
```powershell
codex login
```
**Status**: ⚠️ Required for LLM features

#### 2. Install Playwright Browsers
```powershell
.venv\Scripts\activate
playwright install chromium
```
**Status**: ⚠️ Required for web automation

#### 3. Configure Environment
- [x] `.env` file created
- [ ] Review and customize settings
- [ ] Set filesystem access paths (if needed)

#### 4. Test Basic Functionality
```powershell
launchers\TREYS_AGENT.bat
> help
> playbooks
> exit
```

---

## First-Time Setup Steps

### Step 1: Authenticate Codex
```powershell
codex login
```
Follow the prompts to authenticate with your ChatGPT Pro account.

### Step 2: Install Browser Automation
```powershell
.venv\Scripts\activate
playwright install chromium
```

### Step 3: Test the Agent
```powershell
launchers\TREYS_AGENT.bat
```

In the agent:
```
> help
> create a hello world python script
```

### Step 4: Learn Your First Task
```
> Learn: open notepad
```
Follow the prompts to record the task.

### Step 5: Test Autonomous Mode
```
> Auto: create a simple todo list in a text file
```

---

## Verification Tests

### Test 1: Basic Launch
```powershell
launchers\TREYS_AGENT.bat
```
**Expected**: Agent banner, "Ready! X playbooks loaded"

### Test 2: Help Command
```
> help
```
**Expected**: Full command list displayed

### Test 3: Codex Integration
```
> create a hello world python script
```
**Expected**: Script created successfully

### Test 4: Learn Mode
```
> Learn: test task
```
**Expected**: Recording interface appears

### Test 5: Playbooks
```
> playbooks
```
**Expected**: List of saved playbooks (or "No playbooks saved yet")

---

## Configuration Checklist

### `.env` File Settings

#### Performance Settings
- [ ] `CODEX_TIMEOUT_SECONDS` - Set based on your needs (default: 600)
- [ ] `CODEX_REASONING_EFFORT` - low/medium/high (default: medium)
- [ ] `AUTO_MAX_STEPS` - Max autonomous steps (default: 30)

#### Feature Toggles
- [ ] `AUTO_ENABLE_WEB_GUI` - Enable browser automation (default: 1)
- [ ] `AUTO_ENABLE_DESKTOP` - Enable desktop control (default: 1)
- [ ] `AUTO_ALLOW_HUMAN_ASK` - Agent can ask questions (default: 1)

#### Memory Settings
- [ ] `AGENT_MEMORY_EMBED_MODEL` - SentenceTransformer model (default: all-MiniLM-L6-v2)
- [ ] `AGENT_MEMORY_FAISS_DISABLE` - Disable FAISS (default: 0)

#### Behavior Settings
- [ ] `TREYS_AGENT_DEFAULT_MODE` - execute/research/collab (default: execute)
- [ ] `TREYS_AGENT_PROMPT_ON_AMBIGUOUS` - Ask when unclear (default: 0)

---

## Troubleshooting Checklist

### Issue: Agent won't launch
- [ ] Check Python virtual environment is activated
- [ ] Verify `launchers\_bootstrap_python_env.bat` exists
- [ ] Run `pip install -r requirements.txt`

### Issue: "Codex CLI not found"
- [ ] Run `Get-Command codex` to verify installation
- [ ] Check PATH includes Codex CLI location
- [ ] Reinstall Codex CLI if needed

### Issue: "Codex authentication failed"
- [ ] Run `codex login`
- [ ] Verify ChatGPT Pro subscription is active
- [ ] Check internet connection

### Issue: Browser automation fails
- [ ] Run `playwright install chromium`
- [ ] Check `AUTO_ENABLE_WEB_GUI=1` in `.env`
- [ ] Verify Playwright is in `requirements.txt`

### Issue: Permission denied errors
- [ ] Check file/folder permissions on the target path

### Issue: Agent is too slow
- [ ] Reduce `CODEX_TIMEOUT_SECONDS`
- [ ] Set `CODEX_REASONING_EFFORT=low`
- [ ] Reduce `AUTO_MAX_STEPS`

### Issue: Agent asks too many questions
- [ ] Set `TREYS_AGENT_PROMPT_ON_AMBIGUOUS=0`
- [ ] Set `AUTO_ALLOW_HUMAN_ASK=0` (for full autonomy)

---

## Security Checklist

### Credential Security
- [ ] Keep `agent/memory/credential_store.json` secure
- [ ] Keep `agent/memory/credential_key.key` secure
- [ ] Don't commit these files to version control
- [ ] Backup credential files securely

### Filesystem
- [ ] Confirm expected paths are accessible by the user account

### Environment File
- [ ] Keep `.env` file secure
- [ ] Don't commit to public repositories
- [ ] Review all settings before use

---

## Recommended First Tasks

### Week 1: Learning Phase
- [ ] Test basic execution: `> create a hello world script`
- [ ] Learn a simple task: `> Learn: open notepad`
- [ ] Test playbook: `> open notepad`
- [ ] Save credentials: `> Cred: [site]`
- [ ] Try research: `> Research: Python best practices`

### Week 2: Supervised Autonomy
- [ ] Use Auto mode: `> Auto: organize my desktop files`
- [ ] Learn more complex tasks
- [ ] Build trust with the agent

### Week 3+: Full Autonomy
- [ ] Use autonomous research
- [ ] Complex multi-step tasks
- [ ] Integrate into daily workflow

---

## Maintenance Checklist

### Weekly
- [ ] Review agent logs in `agent/runs/`
- [ ] Check playbook accuracy
- [ ] Update credentials if needed
- [ ] Review `.env` settings

### Monthly
- [ ] Update dependencies: `pip install -r requirements.txt --upgrade`
- [ ] Update Playwright: `playwright install --upgrade`
- [ ] Backup playbooks and credentials
- [ ] Review and clean old run logs

### As Needed
- [ ] Update Codex CLI
- [ ] Add new playbooks
- [ ] Adjust configuration based on usage
- [ ] Review configuration settings

---

## Support Resources

### Documentation
- `AGENT_SETUP_GUIDE.md` - Complete setup guide
- `QUICK_REFERENCE.md` - Quick command reference
- `agent/README.md` - Technical documentation

### In-Agent Help
```
> help          # Show all commands
> playbooks     # List saved tasks
> creds         # List credentials
```

### Testing
```powershell
# Test Codex
codex exec "print('Hello')"

# Test Codex schemas
python scripts/check_codex_schemas.py

# Test Playwright
.venv\Scripts\activate
python -c "from playwright.sync_api import sync_playwright; print('OK')"

# Test Agent
launchers\TREYS_AGENT.bat
```

---

## Next Steps

1. ✅ Complete authentication: `codex login`
2. ✅ Install browsers: `playwright install chromium`
3. ✅ Test basic functionality
4. ✅ Learn your first task
5. ✅ Try autonomous mode
6. ✅ Review and customize `.env`
7. ✅ Start automating!

**You're ready to go! 🚀**
