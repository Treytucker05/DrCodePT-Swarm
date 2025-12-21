# 🚀 START HERE - Your Agent is Ready!

## ⚡ Quick Start (5 Minutes)

### 1. Install Dependencies
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Launch Agent
```powershell
launchers\TREYS_AGENT.bat
```

### 3. Try It Out
```
> help
> menu
> Execute: open my PT School folder
```
Tip: Default is chat-only. Use Execute/Team/Auto/Swarm/Plan when you want action.

---

## 🎯 What Your Agent Can Do

### ✅ **NEW: Self-Healing Autonomous Mode**
Break down complex tasks, execute with automatic error recovery, and learn from mistakes.

**Try it:**
```
> Plan: setup Google Tasks API and test it
```

### ✅ **NEW: Google APIs Integration**
Full OAuth2 integration for Tasks, Gmail, and Calendar.

**Try it:**
```
> setup google apis
> Plan: list my Google Tasks
```

### ✅ **NEW: Issue Tracking**
Track all errors, attempts, and solutions for continuous learning.

**Try it:**
```
> issues
```

### ✅ **Yahoo Mail Management**
Login, clean spam, manage folders, test IMAP.

**Try it:**
```
> open yahoo mail
> clean yahoo spam
```

### ✅ **Autonomous Execution**
Run any task with dynamic replanning.

**Try it:**
```
> Auto: create a Python calculator
```

### ✅ **Research Mode**
Deep research with citations and sources.

**Try it:**
```
> Research: best Python project structure
```

### ✅ **Learn Mode**
Record your actions as reusable playbooks.

**Try it:**
```
> Learn: how to download school files
```

---

## 📚 Documentation

**Read these in order:**

1. **`ENHANCEMENT_SUMMARY.md`** ← **Start here!** Complete overview of new features
2. **`USAGE_EXAMPLES.md`** - Real-world workflows and examples
3. **`QUICK_REFERENCE.md`** - Command cheat sheet
4. **`TROUBLESHOOTING.md`** - Common issues and solutions
5. **`AGENT_SETUP_GUIDE.md`** - Complete setup guide (500+ lines)
6. **`SETUP_CHECKLIST.md`** - Verification checklist

---

## 🔥 Try These First

### Example 1: Google Tasks Setup
```
> Plan: setup Google Tasks API and create a task called "Test Task"
```

**What happens:**
1. Opens Google Cloud Console
2. You enable APIs and create credentials
3. Agent runs OAuth2 flow
4. Creates test task
5. Shows success

### Example 2: Email Organization
```
> Plan: login to Yahoo and clean spam
```

**What happens:**
1. Logs into Yahoo Mail
2. Deletes spam
3. Shows summary

### Example 3: Research and Learn
```
> Research: OAuth2 vs API keys
```

**What happens:**
1. Searches multiple sources
2. Compares approaches
3. Provides recommendations
4. Cites sources

---

## 🎓 Key Commands

### Execute (Quick actions)
```
> Execute: open my PT School folder
```
Run a quick action or playbook.

### Planning (NEW!)
```
> Plan: [complex task]
```
Breaks down task, executes with error recovery.

### Autonomous
```
> Auto: [task]
```
Runs task with dynamic replanning.

### Team
```
> Team: [task]
```
Runs observe -> research -> plan -> execute -> verify -> reflect.

### Swarm
```
> Swarm: [task]
```
Runs parallel sub-agents for comparisons or synthesis.

### Research
```
> Research: [topic]
```
Deep research with sources.

### Think
```
> Think: [task]
```
Planning only (no tools).

### Learn
```
> Learn: [task name]
```
Record actions as playbook.

### Credentials
```
> Cred: [site]
> creds
```
Save/list credentials.

### Issues (NEW!)
```
> issues
> issues open
> issues resolved
```
Track errors and solutions.

### Help
```
> help
> playbooks
```
Show commands and saved playbooks.

---

## 🚨 Important Notes

### Google API Setup
1. Need Google Cloud Project (free tier OK)
2. Enable APIs: Tasks, Gmail, Calendar
3. Create OAuth2 credentials (Desktop app)
4. Download `credentials.json`
5. Save to `agent/memory/google_credentials.json`

### Dependencies
```powershell
pip install -r requirements.txt
```

Includes:
- Google API client libraries
- Playwright for browser automation
- Cryptography for credential storage
- And more...

### 2FA Support
Agent pauses for:
- 2FA challenges
- OAuth2 authorization
- Destructive action confirmations

---

## 💡 Pro Tips

### 1. Use Plain Language
```
> I need to setup Google Tasks
> Can you help me organize my Yahoo folders?
```

### 2. Let It Plan Complex Tasks
```
> Plan: setup all Google APIs and test them
```

### 3. Check Issues for Learning
```
> issues resolved
```

### 4. Save Credentials Once
```
> Cred: yahoo
> Cred: google
```

### 5. Use Playbooks for Repeated Tasks
```
> Learn: download school files
```

Then:
```
> download school files
```

---

## 🎉 You're Ready!

**Start with:**
```
> Plan: setup Google Tasks API and create a task called "Learn to use my agent"
```

**Then explore:**
- `ENHANCEMENT_SUMMARY.md` - Complete feature overview
- `USAGE_EXAMPLES.md` - Real-world workflows
- `TROUBLESHOOTING.md` - Common issues

**Have fun!** 🚀

---

## 📞 Need Help?

1. **In-agent:** `> help`
2. **Troubleshooting:** `TROUBLESHOOTING.md`
3. **Examples:** `USAGE_EXAMPLES.md`
4. **Issues:** `> issues`

**Remember:** The agent learns from every error. The more you use it, the smarter it gets!
