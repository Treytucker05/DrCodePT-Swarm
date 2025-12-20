# 🚀 TREY'S AGENT - Quick Reference

## Launch Agent
```powershell
launchers\TREYS_AGENT.bat
```

## Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show all commands | `> help` |
| `playbooks` | List saved tasks | `> playbooks` |
| `exit` / `quit` | Exit agent | `> exit` |
| `creds` | List saved credentials | `> creds` |

## Operation Modes

### 1. Execute Mode (Default)
Just type what you want:
```
> create a python calculator
> organize my desktop
```

### 2. Learn Mode 🧠
Record a task for instant replay:
```
> Learn: login to school portal
> Learn: download assignments
```

### 3. Autonomous Mode 🤖
Fully autonomous with replanning:
```
> Auto: research AI agents and create summary
> Loop: build a REST API for user management
```

### 4. Research Mode 🔍
Deep research with sources:
```
> Research: Python async best practices
```
Then choose depth: `light` / `balanced` / `deep`

### 5. Collab Mode 💬
Interactive planning:
```
> Collab: reorganize my project structure
```

### 6. Mail Mode 📧
Email management:
```
> Mail: review Yahoo inbox and suggest rules
```

## Credential Management

### Save Credentials
```
> Cred: yahoo
Username: your.email@yahoo.com
Password: ********
```

### List Credentials
```
> creds
```

## Safety Controls

### Enable Unsafe Mode (⚠️ Use with caution)
```
> unsafe on
```

### Disable Unsafe Mode
```
> unsafe off
```

## Environment Variables Quick Reference

```env
# Speed & Performance
CODEX_TIMEOUT_SECONDS=600
CODEX_REASONING_EFFORT=medium

# Autonomous Limits
AUTO_MAX_STEPS=30
AUTO_TIMEOUT_SECONDS=600

# Features
AUTO_ENABLE_WEB_GUI=1
AUTO_ENABLE_DESKTOP=1
AUTO_ALLOW_HUMAN_ASK=1

# Safety
AGENT_UNSAFE_MODE=0
AUTO_FS_ANYWHERE=0
```

## Common Tasks

### Business Automation
```
> Learn: generate weekly report
> Auto: analyze sales data and create presentation
```

### Coding
```
> Auto: create a REST API with authentication
> Research: best practices for API security
```

### Research
```
> Research: machine learning deployment strategies
> Auto: create study guide from research papers
```

### Desktop Management
```
> Learn: organize downloads folder
> Auto: find and remove duplicate files
```

## Troubleshooting

### Codex Not Found
```powershell
Get-Command codex
codex login
```

### Playwright Issues
```powershell
.venv\Scripts\activate
playwright install chromium
```

### Permission Errors
Check `.env` file:
```env
AUTO_FS_ALLOWED_ROOTS=C:\Projects;C:\Documents
```

## File Locations

- **Playbooks**: `agent/playbooks/`
- **Credentials**: `agent/memory/credential_store.json`
- **Run Logs**: `agent/runs/autonomous/`
- **Config**: `.env`

## Tips

1. **Start Simple**: Begin with Execute mode
2. **Learn First**: Record repetitive tasks with Learn mode
3. **Build Trust**: Use supervised Auto mode initially
4. **Go Autonomous**: Enable unsafe mode once comfortable
5. **Use Research**: Research before complex coding tasks

## Getting Help

```
> help                    # In-agent help
```

See `AGENT_SETUP_GUIDE.md` for detailed documentation.
