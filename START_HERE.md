# START HERE


Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
Docs index: `DOCS_INDEX.md`
## Quick Start (5 minutes)
### 1) Install dependencies
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Launch the agent
```powershell
launchers\TREYS_AGENT.bat
```

### 3) Try a few safe commands
```
> help
> menu
> Execute: open Desktop
> Research: best Python project structure
```
Tip: Default is chat-only. Use Execute/Auto/Team/Plan when you want action.

---

## What works today (honest status)
- Chat capability: stable
- Execute/playbooks: partially working (some flows still need manual steps)
- Research capability: works for web summaries
- Swarm capability: currently broken for repo audits
- Google OAuth setup: requires manual browser login/2FA and manual download placement

---

## Google APIs setup (manual steps required)
Run:
```
> setup google apis
```
You will still need to:
1. Sign in to Google Cloud Console (manual login/2FA).
2. Enable APIs: Google Tasks API, Gmail API, Google Calendar API.
3. Create OAuth client ID (Desktop app).
4. Download `credentials.json`.
5. Save it to `agent/memory/google_credentials.json`.

---

## Key commands (stable first)
```
> help
> menu
> playbooks
> creds
> issues
```

## Modes (use with care)
- Chat (default): conversation only, no tools.
- Execute: quick actions/playbooks (partial).
- Auto/Team/Plan: experimental; may need manual intervention.
- Swarm: broken for repo audits right now.
- Research: works for web summaries.
- Think: planning only (no tools).

---

## Documentation map
Read these next:
1. `QUICK_REFERENCE.md` - command cheat sheet
2. `TROUBLESHOOTING.md` - common issues
3. `AGENT_SETUP_GUIDE.md` - full setup guide

---

## Need help?
```
> help
```
Also see `TROUBLESHOOTING.md`.
