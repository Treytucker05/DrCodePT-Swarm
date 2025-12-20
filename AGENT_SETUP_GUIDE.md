# TREY'S AGENT - Complete Setup Guide

## 🎯 Overview

Trey's Agent is a powerful autonomous AI assistant that can:
- **Learn & Remember Tasks**: Record your workflows and replay them instantly
- **Autonomous Execution**: Complete complex tasks with dynamic replanning
- **Research**: Deep research with iterative refinement
- **Code Generation**: Build and debug code projects
- **Web Automation**: Browser automation with Playwright
- **Desktop Control**: Execute system commands and file operations

---

## ✅ Current Status

### What's Working:
- ✅ Agent launches successfully
- ✅ Codex CLI integration (`codex.ps1` detected)
- ✅ Virtual environment (`.venv`)
- ✅ Core dependencies installed
- ✅ Multiple operation modes (Execute, Learn, Research, Autonomous, Collab)
- ✅ Credential management system
- ✅ Playbook system for task recording

### What Needs Configuration:
- ⚠️ Codex CLI authentication (ChatGPT Pro)
- ⚠️ Playwright browser setup
- ⚠️ Environment variables
- ⚠️ Optional: Additional tool integrations

---

## 🚀 Quick Start

### 1. Launch the Agent

```powershell
launchers\TREYS_AGENT.bat
```

### 2. First Time Setup

When you first launch, the agent will:
1. Activate the Python virtual environment
2. Load any existing playbooks
3. Show you the command prompt

### 3. Basic Commands

```
> help                          # Show all commands
> playbooks                     # List saved tasks
> Learn: [task name]            # Record a new task
> Auto: [task]                  # Run autonomous mode
> Research: [topic]             # Deep research mode
> exit                          # Quit
```

---

## 📋 Detailed Setup

### Step 1: Verify Codex CLI

Your Codex CLI is installed at: `C:\Users\treyt\...\codex.ps1`

**Test it:**
```powershell
codex --version
```

**Authenticate with ChatGPT Pro:**
```powershell
codex auth login
```

### Step 2: Install Playwright Browsers

For web automation, install browser drivers:

```powershell
.venv\Scripts\activate
playwright install chromium
```

Or install all browsers:
```powershell
playwright install
```

### Step 3: Create Environment Configuration

Create a `.env` file in the root directory:

```env
# === CODEX CONFIGURATION ===
CODEX_TIMEOUT_SECONDS=600
CODEX_REASONING_EFFORT=medium

# === AUTONOMOUS MODE SETTINGS ===
AUTO_MAX_STEPS=30
AUTO_TIMEOUT_SECONDS=600
AUTO_PLANNER_MODE=react
AUTO_ENABLE_WEB_GUI=1
AUTO_ENABLE_DESKTOP=1
AUTO_ALLOW_HUMAN_ASK=1

# === AGENT BEHAVIOR ===
TREYS_AGENT_DEFAULT_MODE=execute
TREYS_AGENT_PROMPT_ON_AMBIGUOUS=0

# === SAFETY SETTINGS ===
AGENT_UNSAFE_MODE=0
AUTO_FS_ANYWHERE=0

# === OPTIONAL: Credential Prompts ===
TREYS_AGENT_CRED_PROMPT_SITES=yahoo,gmail,github
```

### Step 4: Verify Dependencies

Check that all required packages are installed:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

**Required packages:**
- `cryptography` - Encrypted credential storage
- `playwright` - Browser automation
- `pyautogui` - Desktop automation
- `python-dotenv` - Environment variables
- `pydantic` - Data validation
- `PyYAML` - YAML parsing
- `requests` - HTTP requests
- `colorama` - Terminal colors
- `pytest` - Testing

---

## 🎓 How to Use Each Mode

### 1. **Execute Mode (Default)**

Just type what you want to do. The agent will:
1. Check if a matching playbook exists
2. If yes → Run it instantly (no LLM needed)
3. If no → Use Codex to generate and execute

**Examples:**
```
> create a python calculator
> organize my desktop files
> download my school assignments
```

### 2. **Learn Mode** 🧠

Record a task so the agent can replay it later:

```
> Learn: how to login to my school portal
```

The agent will:
1. Ask you to perform the task step-by-step
2. Record your actions (browser clicks, keyboard input, etc.)
3. Save it as a playbook
4. Next time you ask, it runs instantly!

**Perfect for:**
- Website logins
- Repetitive workflows
- Multi-step processes
- Data entry tasks

### 3. **Autonomous Mode** 🤖

Fully autonomous task execution with dynamic replanning:

```
> Auto: research autonomous AI agents and create a summary document
```

The agent will:
1. Break down the task into steps
2. Execute each step
3. Observe results
4. Replan if needed
5. Continue until complete

**Features:**
- Self-correcting
- Can use web browsing
- Can write code
- Can execute system commands
- Asks for approval on risky actions (unless unsafe mode is on)

### 4. **Research Mode** 🔍

Deep research with iterative refinement:

```
> Research: best Python project structure for AI agents
```

**Depth levels:**
- `light` - Quick overview (3-5 sources)
- `balanced` - Moderate depth (5-10 sources)
- `deep` - Comprehensive (10+ sources, multiple iterations)

### 5. **Collab Mode** 💬

Interactive planning and strategy:

```
> Collab: I want to reorganize my project structure
```

The agent will:
1. Ask clarifying questions
2. Discuss options with you
3. Create a detailed plan
4. Execute with your approval

### 6. **Mail Mode** 📧

Supervised email management:

```
> Mail: review my Yahoo inbox and suggest rules
```

---

## 🔐 Credential Management

The agent can securely store credentials for websites:

### Save Credentials:
```
> Cred: yahoo
Username/email: your.email@yahoo.com
Password: ********
```

### List Saved Credentials:
```
> creds
```

**Security:**
- Passwords are encrypted using `cryptography` library
- Stored in `agent/memory/credential_store.json`
- Encryption key in `agent/memory/credential_key.key`
- **Keep these files secure!**

---

## ⚙️ Advanced Configuration

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEX_TIMEOUT_SECONDS` | 600 | Codex CLI timeout |
| `CODEX_REASONING_EFFORT` | medium | low/medium/high |
| `AUTO_MAX_STEPS` | 30 | Max steps in autonomous mode |
| `AUTO_TIMEOUT_SECONDS` | 600 | Autonomous mode timeout |
| `AUTO_PLANNER_MODE` | react | react/plan_first |
| `AUTO_ENABLE_WEB_GUI` | 1 | Enable browser automation |
| `AUTO_ENABLE_DESKTOP` | 1 | Enable desktop control |
| `AUTO_ALLOW_HUMAN_ASK` | 1 | Agent can ask for help |
| `AUTO_FS_ANYWHERE` | 0 | Allow file access anywhere |
| `AGENT_UNSAFE_MODE` | 0 | Skip safety confirmations |
| `TREYS_AGENT_DEFAULT_MODE` | execute | execute/research/collab |
| `TREYS_AGENT_PROMPT_ON_AMBIGUOUS` | 0 | Ask when intent unclear |

### Filesystem Safety

By default, the agent can only access:
- Your Desktop
- OneDrive Desktop
- The agent's repository folder

**To allow access to specific folders:**
```env
AUTO_FS_ALLOWED_ROOTS=C:\Projects;C:\Documents;C:\Code
```

**To allow access anywhere (⚠️ use with caution):**
```env
AUTO_FS_ANYWHERE=1
```

### Unsafe Mode

By default, the agent asks for confirmation before:
- Deleting files
- Running system commands
- Making network requests
- Installing software

**To enable unsafe mode (⚠️ use with caution):**
```
> unsafe on
```

Or set in `.env`:
```env
AGENT_UNSAFE_MODE=1
```

---

## 📁 Project Structure

```
DrCodePT-Swarm/
├── agent/
│   ├── treys_agent.py          # Main entry point
│   ├── modes/                  # Operation modes
│   │   ├── autonomous.py       # Autonomous execution
│   │   ├── execute.py          # Playbook execution
│   │   ├── learn.py            # Task recording
│   │   ├── research.py         # Research mode
│   │   └── collab.py           # Collaborative planning
│   ├── autonomous/             # Autonomous agent core
│   │   ├── runner.py           # Main execution loop
│   │   ├── planning/           # Planning strategies
│   │   └── tools/              # Tool registry
│   ├── memory/                 # Persistent storage
│   │   ├── credentials.py      # Credential management
│   │   └── memory_manager.py   # Memory system
│   ├── playbooks/              # Saved task recordings
│   ├── llm/                    # LLM integrations
│   │   └── codex_cli_client.py # Codex CLI wrapper
│   └── tools/                  # Agent tools
├── launchers/
│   ├── TREYS_AGENT.bat         # Main launcher
│   └── _bootstrap_python_env.bat
├── requirements.txt            # Python dependencies
└── .env                        # Configuration (create this)
```

---

## 🐛 Troubleshooting

### Issue: "Codex CLI not found"

**Solution:**
```powershell
# Check if codex is in PATH
Get-Command codex

# If not found, reinstall Codex CLI
# Follow ChatGPT Pro Codex CLI installation guide
```

### Issue: "Playwright browser not found"

**Solution:**
```powershell
.venv\Scripts\activate
playwright install chromium
```

### Issue: "Permission denied" errors

**Solution:**
1. Run as Administrator (if needed)
2. Check `AUTO_FS_ALLOWED_ROOTS` in `.env`
3. Or enable `AUTO_FS_ANYWHERE=1` (⚠️ use with caution)

### Issue: Agent is too slow

**Solution:**
```env
# Reduce timeout
CODEX_TIMEOUT_SECONDS=300

# Use lighter reasoning
CODEX_REASONING_EFFORT=low

# Reduce max steps
AUTO_MAX_STEPS=15
```

### Issue: Agent asks too many questions

**Solution:**
```env
# Disable ambiguity prompts
TREYS_AGENT_PROMPT_ON_AMBIGUOUS=0

# Set default mode
TREYS_AGENT_DEFAULT_MODE=execute
```

---

## 🎯 Recommended Workflow

### Phase 1: Learning (First 2-3 weeks)

1. **Start with Learn Mode** for repetitive tasks:
   ```
   > Learn: login to my school portal
   > Learn: download assignments from Canvas
   > Learn: organize my downloads folder
   ```

2. **Use Execute Mode** to run learned tasks:
   ```
   > login to my school portal
   > download assignments
   ```

3. **Save credentials** for websites you use often:
   ```
   > Cred: school
   > Cred: yahoo
   > Cred: github
   ```

### Phase 2: Supervised Autonomy (Weeks 3-6)

1. **Use Auto mode with supervision**:
   ```
   > Auto: create a Python script to organize my files
   ```

2. **Review and approve** each action

3. **Build trust** as the agent learns your preferences

### Phase 3: Full Autonomy (Week 6+)

1. **Enable unsafe mode** for trusted tasks:
   ```
   > unsafe on
   ```

2. **Use Research mode** for autonomous research:
   ```
   > Research: latest AI agent architectures
   ```

3. **Complex multi-step tasks**:
   ```
   > Auto: analyze my project structure and suggest improvements
   ```

---

## 🔥 Power User Tips

### 1. Chain Commands

The agent can handle complex multi-step requests:
```
> Auto: research Python async best practices, create a summary document, and email it to me
```

### 2. Use Playbooks for Speed

Once you've learned a task, it runs instantly without LLM calls:
```
> Learn: backup my project files
# Later...
> backup my project files  # Runs instantly!
```

### 3. Customize Triggers

Edit `agent/playbooks/index.json` to add custom trigger phrases:
```json
{
  "backup-project": {
    "name": "Backup Project Files",
    "triggers": ["backup", "save my work", "backup project"]
  }
}
```

### 4. Use Research for Learning

Before coding something new:
```
> Research: how to implement async web scraping in Python
```

Then use the insights:
```
> Auto: create an async web scraper using the best practices
```

### 5. Collab for Planning

For big projects:
```
> Collab: I want to build a personal task management system
```

The agent will help you plan before executing.

---

## 📊 Monitoring & Logs

### Run Logs

All autonomous runs are saved in:
```
agent/runs/autonomous/[timestamp]/
├── trace.jsonl          # Detailed execution trace
├── workspace/           # Working files
└── final_result.json    # Final output
```

### Playbook Recordings

Learned tasks are saved in:
```
agent/playbooks/
├── index.json           # Playbook registry
└── [task-name]/         # Individual playbooks
    ├── steps.json
    └── metadata.json
```

### Memory

Agent memory is stored in:
```
agent/memory/
├── agent_memory.json           # General memory
├── autonomous_memory.sqlite3   # Autonomous mode memory
└── credential_store.json       # Encrypted credentials
```

---

## 🚨 Safety & Best Practices

### ✅ DO:
- Start with Learn mode for new tasks
- Review autonomous actions initially
- Use credentials for sensitive sites
- Keep `.env` and credential files secure
- Regularly backup your playbooks
- Use specific, clear instructions

### ❌ DON'T:
- Enable unsafe mode without understanding risks
- Share credential files
- Allow filesystem access everywhere
- Run untrusted playbooks
- Ignore error messages

---

## 🎓 Example Use Cases

### Business Automation
```
> Learn: generate weekly sales report
> Learn: send status update email
> Auto: analyze this quarter's data and create presentation
```

### Coding Projects
```
> Auto: create a REST API for user management
> Research: best practices for API security
> Auto: add authentication to my API
```

### Research & Learning
```
> Research: machine learning model deployment strategies
> Auto: create a study guide from these research papers
```

### Desktop Management
```
> Learn: organize my downloads folder
> Auto: find and remove duplicate files
> Auto: backup important documents to OneDrive
```

---

## 🆘 Getting Help

### In-Agent Help
```
> help
```

### Check Playbooks
```
> playbooks
```

### View Credentials
```
> creds
```

### Test Codex
```powershell
codex exec "print('Hello from Codex')"
```

---

## 🎉 You're Ready!

Your agent is configured and ready to use. Start with simple tasks and gradually increase complexity as you build trust.

**Recommended First Steps:**
1. Test basic execution: `> create a hello world python script`
2. Learn a simple task: `> Learn: open notepad`
3. Try research: `> Research: Python best practices`
4. Go autonomous: `> Auto: organize my desktop files`

**Happy Automating! 🚀**
