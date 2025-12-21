# 🚀 TREY'S AGENT - Quick Reference

## Launch Agent
```powershell
launchers\TREYS_AGENT.bat
```

## Core Commands
| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show command help | `> help` |
| `menu` | Show capability menu | `> menu` |
| `playbooks` | List saved tasks | `> playbooks` |
| `creds` | List saved credentials | `> creds` |
| `cred: <site>` | Save credentials | `> Cred: yahoo` |
| `issues` | List tracked issues | `> issues open` |
| `grade` | Grade the last run | `> grade` |
| `connect: <server>` | Connect to MCP server | `> Connect: github` |
| `mcp list` | List MCP tools | `> mcp list` |
| `resume` | Resume the most recent run | `> resume` |
| `maintenance` | Summarize recent runs | `> maintenance` |
| `exit` / `quit` | Exit agent | `> exit` |

## Operation Modes
### 1. Chat-only (Default)
Just type what you want; the agent will talk without running tools.
If you want action, use Execute:/Auto:/Team:/Swarm:/Plan: or reply "execute" when prompted.

### 2. Execute Mode (Quick actions)
Run a quick action or playbook:
```
> Execute: open my PT School folder
> Execute: organize my desktop
```

### 3. Learn Mode
Record a task for instant replay:
```
> Learn: login to school portal
> Learn: download assignments
```

### 4. Auto Mode
Fully autonomous with replanning:
```
> Auto: research AI agents and create summary
> Loop: build a REST API for user management
```

### 5. Plan Mode
Plan first, then execute:
```
> Plan: setup Google Tasks API and test it
```

### 6. Team Mode
Supervisor loop with checkpoints:
```
> Team: audit my project and propose fixes
```

### 7. Swarm Mode
Parallel sub-agents:
```
> Swarm: compare 3 CRMs and summarize pros/cons
```

### 8. Research Mode
Deep research with sources:
```
> Research: Python async best practices
```
Then choose depth: `light` / `balanced` / `deep`

### 9. Think Mode
Planning only (no tools):
```
> Think: design a rollout plan for the repo
```

### 10. Collab Mode
Interactive planning:
```
> Collab: reorganize my project structure
```

### 11. Mail Mode
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

## Environment Variables Quick Reference

```env
# Speed & Performance
CODEX_TIMEOUT_SECONDS=600
CODEX_REASONING_EFFORT=medium

# Autonomous Limits
AUTO_MAX_STEPS=30
AUTO_TIMEOUT_SECONDS=600
AUTO_PLANNER_MODE=auto

# Features
AUTO_ENABLE_WEB_GUI=1
AUTO_ENABLE_DESKTOP=1
AUTO_ALLOW_HUMAN_ASK=1

# Memory
AGENT_MEMORY_EMBED_MODEL=all-MiniLM-L6-v2
AGENT_MEMORY_FAISS_DISABLE=0

# Agent Behavior
TREYS_AGENT_DEFAULT_MODE=execute
TREYS_AGENT_CRED_PROMPT_SITES=yahoo,gmail,github
EXEC_ALLOW_PYTHON=0
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
Check file/folder permissions on the target path.

## File Locations

- **Playbooks**: `agent/playbooks/`
- **Credentials**: `agent/memory/credential_store.json`
- **Run Logs**: `agent/runs/autonomous/`
- **Config**: `.env`

## Tips

1. **Start Simple**: Chat first, then use Execute mode for actions
2. **Learn First**: Record repetitive tasks with Learn mode
3. **Build Trust**: Use supervised Auto mode initially
4. **Go Autonomous**: Run longer, multi-step tasks once comfortable
5. **Use Research**: Research before complex coding tasks

## Getting Help

```
> help                    # In-agent help
```

See `AGENT_SETUP_GUIDE.md` for detailed documentation.
