# 🚀 TREY'S AGENT - Usage Examples

## Quick Start

Launch the agent:
```powershell
launchers\TREYS_AGENT.bat
```

---

## 🎯 Google APIs Setup (NEW!)

### Setup Google Tasks, Gmail, and Calendar APIs

**What it does:**
- Guides you through Google Cloud Console setup
- Enables required APIs (Tasks, Gmail, Calendar)
- Creates OAuth2 credentials
- Tests all three APIs
- Saves credentials securely

**Command:**
```
> setup google apis
```

**Or use plain language:**
```
> Plan: setup Google Tasks API and test it
```

**Steps:**
1. Agent opens Google Cloud Console
2. You enable APIs and create OAuth2 credentials
3. Download `credentials.json`
4. Save to `agent/memory/google_credentials.json`
5. Agent runs OAuth2 flow (browser opens)
6. Sign in and authorize
7. Agent tests all APIs

**After setup, you can:**
```
> Plan: list my Google Tasks
> Plan: check my Gmail inbox
> Plan: show my calendar events
> Plan: create a task "Buy groceries"
```

---

## 🧠 Self-Healing Autonomous Mode (NEW!)

### Plan and Execute with Error Recovery

**What it does:**
- Breaks down complex tasks into steps
- Executes with automatic error recovery
- Learns from past issues
- Retries with different approaches
- Tracks all attempts for future reference

**Command:**
```
> Plan: [your complex task]
```

**Examples:**

#### Example 1: Multi-Step API Setup
```
> Plan: setup Google Tasks API, test it, and create a task called "Test Task"
```

**What happens:**
1. Agent creates execution plan
2. Opens Google Cloud Console
3. Guides you through setup
4. Tests the API
5. Creates the task
6. If any step fails, it retries automatically

#### Example 2: Email Organization
```
> Plan: consolidate my Yahoo folders and create rules to auto-sort emails
```

**What happens:**
1. Logs into Yahoo Mail
2. Scans all folders
3. Suggests consolidation plan
4. Moves emails
5. Creates filter rules
6. Tests the rules

#### Example 3: Research and Implementation
```
> Plan: research the best Python logging library and implement it in my project
```

**What happens:**
1. Researches logging libraries
2. Compares options
3. Recommends best choice
4. Installs the library
5. Creates example code
6. Tests it

---

## 📋 Issue Tracking (NEW!)

### View Tracked Issues

**List all issues:**
```
> issues
```

**List only open issues:**
```
> issues open
```

**List resolved issues:**
```
> issues resolved
```

**What you see:**
- Issue ID and timestamp
- Task that failed
- Error message
- Number of attempts
- Solution (if resolved)

**Example output:**
```
[ISSUE TRACKER]
Total: 5 | Open: 1 | Resolved: 4

[RESOLVED] 20251220_143022
  Task: setup Google Tasks API
  Error: credentials.json not found
  Attempts: 2
  Solution: Downloaded credentials.json to agent/memory/

[OPEN] 20251220_150145
  Task: consolidate Yahoo folders
  Error: Timeout waiting for folder list
  Attempts: 3
```

---

## 🎭 Existing Features

### Yahoo Mail Management

#### Login to Yahoo Mail
```
> open yahoo mail
```

#### Clean Spam Folder
```
> clean yahoo spam
```

#### Test IMAP Connection
```
> test yahoo imap
```

#### Setup App Password
```
> setup yahoo app password
```

---

### Credentials Management

#### Save Credentials
```
> Cred: yahoo
Username/email: your.email@yahoo.com
Password: (hidden)
```

#### List Saved Credentials
```
> creds
```

---

### Autonomous Mode

#### Run Any Task
```
> Auto: [task]
```

**Examples:**
```
> Auto: create a Python calculator
> Auto: download my school files
> Auto: organize my desktop
```

---

### Research Mode

#### Deep Research
```
> Research: [topic]
```

**Examples:**
```
> Research: best Python project structure
> Research: autonomous AI agents
> Research: OAuth2 vs API keys
```

---

### Learn Mode

#### Record New Playbook
```
> Learn: [task name]
```

**Example:**
```
> Learn: how to download school files
```

Then perform the task manually. The agent records your actions and creates a playbook.

---

### Collab Mode

#### Interactive Planning
```
> Collab: [goal]
```

**Example:**
```
> Collab: organize my Yahoo folders and clean rules
```

---

## 🔥 Real-World Workflows

### Workflow 1: Complete Google Integration

**Goal:** Set up all Google services and test them

```
> Plan: setup Google APIs for Tasks, Gmail, and Calendar, then test each one
```

**What happens:**
1. Opens Google Cloud Console
2. You enable APIs and create credentials
3. Agent runs OAuth2 flow
4. Tests Tasks API
5. Tests Gmail API
6. Tests Calendar API
7. Shows summary of what's working

---

### Workflow 2: Email Cleanup and Organization

**Goal:** Clean up Yahoo mail and set up auto-sorting

```
> Plan: login to Yahoo, clean spam, consolidate folders, and create rules
```

**What happens:**
1. Logs into Yahoo Mail
2. Deletes spam
3. Scans all folders
4. Suggests consolidation
5. Moves emails
6. Creates filter rules
7. Tests rules

---

### Workflow 3: Task Management Setup

**Goal:** Set up Google Tasks and create initial tasks

```
> Plan: setup Google Tasks API, create a task list called "Work", and add 3 tasks
```

**What happens:**
1. Sets up Google Tasks API
2. Creates "Work" task list
3. Adds 3 tasks
4. Shows task list

---

### Workflow 4: Calendar Integration

**Goal:** Set up calendar and add events

```
> Plan: setup Google Calendar API and add an event for tomorrow at 2pm
```

**What happens:**
1. Sets up Google Calendar API
2. Creates event for tomorrow at 2pm
3. Shows event details

---

## 🛠️ Advanced Usage

### Unsafe Mode

**Enable unsafe mode** (skips confirmations):
```
> unsafe on
```

**Disable unsafe mode:**
```
> unsafe off
```

---

### View Playbooks

**List all saved playbooks:**
```
> playbooks
```

---

### Help

**Show all commands:**
```
> help
```

---

## 💡 Tips

### 1. Use Plain Language
The agent understands natural language. Just describe what you want:
```
> I need to setup Google Tasks
> Can you help me organize my Yahoo folders?
> Create a Python script that calculates taxes
```

### 2. Let It Plan Complex Tasks
For multi-step tasks, use `Plan:` to get automatic error recovery:
```
> Plan: setup all Google APIs and test them
```

### 3. Check Issues for Learning
Review resolved issues to see how the agent solved problems:
```
> issues resolved
```

### 4. Save Credentials Once
Save credentials once, use everywhere:
```
> Cred: yahoo
> Cred: google
```

### 5. Use Playbooks for Repeated Tasks
If you do something often, teach it once:
```
> Learn: download school files
```

Then just say:
```
> download school files
```

---

## 🚨 Troubleshooting

### Issue: Google API Setup Fails

**Solution:**
1. Make sure you downloaded `credentials.json`
2. Save it to `agent/memory/google_credentials.json`
3. Run: `pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client`
4. Try again: `> setup google apis`

---

### Issue: Plan Mode Fails

**Solution:**
1. Check issues: `> issues open`
2. Review the error
3. Try with more specific instructions
4. Or use Auto mode: `> Auto: [task]`

---

### Issue: Credentials Not Working

**Solution:**
1. For Yahoo IMAP, use app password: `> setup yahoo app password`
2. For Google, use OAuth2: `> setup google apis`
3. Update credentials: `> Cred: [site]`

---

## 📚 More Help

- **Troubleshooting Guide:** `TROUBLESHOOTING.md`
- **Setup Guide:** `AGENT_SETUP_GUIDE.md`
- **Quick Reference:** `QUICK_REFERENCE.md`
- **Setup Checklist:** `SETUP_CHECKLIST.md`

---

## 🎉 You're Ready!

Your agent can now:
- ✅ Set up Google APIs (Tasks, Gmail, Calendar)
- ✅ Plan and execute complex tasks
- ✅ Recover from errors automatically
- ✅ Learn from past issues
- ✅ Manage Yahoo Mail
- ✅ Save and use credentials
- ✅ Record new playbooks
- ✅ Research topics
- ✅ And much more!

**Start with:**
```
> Plan: setup Google Tasks API and create a task called "Learn to use my agent"
```

Have fun! 🚀
