# TREY'S AGENT - Quick Reference


Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
## Launch
```powershell
launchers\TREYS_AGENT.bat
```

## Core commands (known to work)
| Command | Description | Example |
|---|---|---|
| `help` | Show command help | `> help` |
| `menu` | Show legacy menu (if enabled) | `> menu` |
| `playbooks` | List saved playbooks | `> playbooks` |
| `creds` | List saved credentials | `> creds` |
| `cred: <site>` | Save credentials | `> Cred: yahoo` |
| `issues` | List tracked issues | `> issues` |
| `exit` / `quit` | Exit agent | `> exit` |

## Modes (current reality)
- Chat (default): stable, no tools.
- Execute: partial (playbooks run, some steps still manual).
- Research: works for web summaries.
- Auto / Team / Plan: experimental (may need manual intervention).
- Swarm: broken for repo audits (avoid for now).
- Think: planning only (no tools).

## Examples that work
```
> Execute: open Desktop
> Research: OAuth2 vs API keys
> issues
```

## Google OAuth setup (manual steps)
```
> setup google apis
```
You must complete login/2FA and download `credentials.json` manually, then save it to:
`agent/memory/google_credentials.json`.

## Troubleshooting
### Codex not found
```powershell
Get-Command codex
codex login
```

### Playwright missing
```powershell
.venv\Scripts\activate
playwright install chromium
```

## File locations
- Playbooks: `agent/playbooks/`
- Credentials: `agent/memory/credential_store.json`
- Run logs: `agent/runs/`

See `TROUBLESHOOTING.md` and `AGENT_SETUP_GUIDE.md` for details.
