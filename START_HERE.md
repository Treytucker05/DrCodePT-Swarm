# 🤖 TREY'S AGENT - Your Personal AI Assistant

> **A powerful autonomous AI agent that learns, remembers, and executes tasks for business automation, coding, research, and more.**

---

## 🚀 Quick Start (3 Steps)

### 1. Authenticate Codex CLI
```powershell
codex auth login
```

### 2. Install Browser Automation
```powershell
.venv\Scripts\activate
playwright install chromium
```

### 3. Launch the Agent
```powershell
launchers\TREYS_AGENT.bat
```

**That's it!** You're ready to go. 🎉

---

## 📚 Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[REVIEW_AND_ACTION_PLAN.md](REVIEW_AND_ACTION_PLAN.md)** | Complete review & recommendations | **Start here** - Overview of everything |
| **[AGENT_SETUP_GUIDE.md](AGENT_SETUP_GUIDE.md)** | Comprehensive setup guide | Detailed configuration & troubleshooting |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Command cheat sheet | Daily use - quick command lookup |
| **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** | Step-by-step checklist | First-time setup verification |
| **[.env](.env)** | Configuration file | Customize agent behavior |

---

## 🎯 What Can It Do?

### 1. **Learn & Remember Tasks** 🧠
Record any task once, run it instantly forever:
```
> Learn: login to school portal
> Learn: organize downloads folder
> Learn: generate weekly report
```

### 2. **Autonomous Execution** 🤖
Complex tasks with dynamic replanning:
```
> Auto: research AI agents and create a summary document
> Auto: build a REST API with authentication
> Auto: analyze my project structure and suggest improvements
```

### 3. **Deep Research** 🔍
Iterative research with multiple sources:
```
> Research: Python async best practices
> Research: machine learning deployment strategies
```

### 4. **Code Generation** 💻
Build and debug code projects:
```
> create a python web scraper
> Auto: add error handling to my script
> Auto: write unit tests for my API
```

### 5. **Web Automation** 🌐
Browser automation with Playwright:
```
> Learn: download assignments from Canvas
> Auto: scrape product prices from Amazon
```

### 6. **Desktop Control** 🖥️
Execute system commands and file operations:
```
> organize my desktop files
> backup important documents
> find and remove duplicate files
```

---

## 🎓 Operation Modes

| Mode | Trigger | Use Case | Example |
|------|---------|----------|---------|
| **Execute** | Default | Run learned tasks instantly | `> organize downloads` |
| **Learn** | `Learn:` | Record new tasks | `> Learn: login to Yahoo` |
| **Autonomous** | `Auto:` | Complex multi-step tasks | `> Auto: build a calculator` |
| **Research** | `Research:` | Deep research | `> Research: AI agents` |
| **Collab** | `Collab:` | Interactive planning | `> Collab: reorganize project` |
| **Mail** | `Mail:` | Email management | `> Mail: review inbox` |

---

## ⚡ Quick Commands

```
> help                          # Show all commands
> playbooks                     # List saved tasks
> Learn: [task name]            # Record a new task
> Auto: [task]                  # Run autonomous mode
> Research: [topic]             # Deep research
> Cred: [site]                  # Save credentials
> creds                         # List saved credentials
> unsafe on/off                 # Toggle safety mode
> exit                          # Quit
```

---

## 🔧 Configuration

Edit `.env` to customize behavior:

```env
# Performance
CODEX_TIMEOUT_SECONDS=600
CODEX_REASONING_EFFORT=medium

# Features
AUTO_ENABLE_WEB_GUI=1
AUTO_ENABLE_DESKTOP=1
AUTO_ALLOW_HUMAN_ASK=1

# Safety
AGENT_UNSAFE_MODE=0
AUTO_FS_ANYWHERE=0
```

See [AGENT_SETUP_GUIDE.md](AGENT_SETUP_GUIDE.md) for all options.

---

## 🎯 Your Use Cases

### Business Automation
```
> Learn: generate weekly sales report
> Learn: send status update email
> Auto: analyze quarterly data and create presentation
```

### Coding Projects
```
> Research: REST API best practices
> Auto: create a REST API with authentication
> Auto: add unit tests and documentation
```

### Study Systems
```
> Research: effective study techniques
> Collab: create a study plan for machine learning
> Auto: organize study materials by topic
```

### Desktop Management
```
> Learn: organize downloads folder
> Auto: find and remove duplicate files
> Auto: backup important documents
```

---

## 🔐 Security Features

- **Encrypted Credentials**: Secure storage for website passwords
- **Filesystem Safety**: Restricted access to approved folders
- **Approval Mode**: Review actions before execution
- **Audit Logs**: Complete trace of all operations

---

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│         TREY'S AGENT                    │
├─────────────────────────────────────────┤
│  Modes:                                 │
│  • Execute (Playbook Replay)            │
│  • Learn (Task Recording)               │
│  • Autonomous (Dynamic Planning)        │
│  • Research (Deep Research)             │
│  • Collab (Interactive Planning)        │
│  • Mail (Email Management)              │
├─────────────────────────────────────────┤
│  Core Systems:                          │
│  • Codex CLI Integration                │
│  • Playwright Browser Automation        │
│  • PyAutoGUI Desktop Control            │
│  • Encrypted Credential Storage         │
│  • SQLite Memory Management             │
│  • YAML Playbook System                 │
└─────────────────────────────────────────┘
```

---

## 🎓 Learning Path

### Week 1: Learning Phase
- Test basic execution
- Learn 3-5 simple tasks
- Save credentials for common sites
- Try research mode

### Week 2: Supervised Autonomy
- Use Auto mode with approval
- Review each action
- Build trust with the agent

### Week 3+: Full Autonomy
- Enable unsafe mode for trusted tasks
- Complex multi-step tasks
- Integrate into daily workflow

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Codex CLI not found" | Run `codex auth login` |
| "Browser automation failed" | Run `playwright install chromium` |
| "Permission denied" | Add folder to `AUTO_FS_ALLOWED_ROOTS` in `.env` |
| Agent too slow | Reduce `CODEX_TIMEOUT_SECONDS` in `.env` |

See [AGENT_SETUP_GUIDE.md](AGENT_SETUP_GUIDE.md) for detailed troubleshooting.

---

## 📁 Project Structure

```
DrCodePT-Swarm/
├── agent/
│   ├── treys_agent.py          # Main entry point
│   ├── modes/                  # Operation modes
│   ├── autonomous/             # Autonomous agent core
│   ├── memory/                 # Persistent storage
│   ├── playbooks/              # Saved tasks
│   └── llm/                    # LLM integrations
├── launchers/
│   └── TREYS_AGENT.bat         # Main launcher
├── .env                        # Configuration
└── [Documentation files]
```

---

## 🎉 You're Ready!

Your agent is **fully functional** and ready to use. Start with simple tasks and gradually increase complexity.

**Recommended First Steps:**
1. ✅ Authenticate: `codex auth login`
2. ✅ Install browsers: `playwright install chromium`
3. ✅ Launch: `launchers\TREYS_AGENT.bat`
4. ✅ Test: `> create a hello world python script`
5. ✅ Learn: `> Learn: open notepad`

**Read [REVIEW_AND_ACTION_PLAN.md](REVIEW_AND_ACTION_PLAN.md) for complete details.**

---

## 📞 Support

- **In-Agent Help**: `> help`
- **Documentation**: See files listed above
- **Test Codex**: `codex exec "print('Hello')"`
- **Test Agent**: `launchers\TREYS_AGENT.bat`

---

## 🚀 Happy Automating!

Your personal AI assistant is ready to:
- ✅ Automate repetitive tasks
- ✅ Build and debug code
- ✅ Research topics deeply
- ✅ Control your desktop
- ✅ Browse the internet
- ✅ Learn and remember everything

**Let's get started!** 🎯
