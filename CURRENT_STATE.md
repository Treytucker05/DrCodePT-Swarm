# CURRENT_STATE.md (Snapshot)

**Status:** Historical/Archive. Do not update as a source of truth. See `AGENT_BEHAVIOR.md` and `conductor/tracks.md`.



Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
## Summary (Dec 28, 2025)
- Chat mode works for simple queries.
- Execute/playbooks are partially working; some flows still require manual steps.
- Swarm mode is currently broken for repo audits.
- Google OAuth setup still requires manual login/2FA and manual download placement.
- "DO NOT execute" wrapper is only applied to swarm reasoning agents; chat/playbook are not wrapped.
- Codex CLI profiles in `~/.codex/config.toml` target gpt-5 for reasoning and gpt-5.2-codex for execution.

## What Works
- Chat-only conversation (no tools by default).
- Research mode (web_search + summaries).
- Basic Execute/playbook actions for shell/python/browser flows.
- Credential storage and issue tracking.

## Partially Working / Manual Steps
- Playbooks: some flows still need manual intervention.
- Google OAuth setup: requires manual browser login/2FA and manual credentials download.
- Windows-MCP (Desktop Commander) is available but not wired into execute playbook runner yet.

## Broken
- Swarm mode for repo audits (fails in practice).

## Tools and Integrations (Existing)
- Tools: shell, python_exec, browser (Playwright), desktop (PyAutoGUI), web_search, web_fetch, research, notify, screen_recorder, code_review, fs, vision.
- Integrations: Google APIs (Tasks/Gmail/Calendar), Yahoo Mail (IMAP), MCP servers (filesystem, github, google-calendar, google-tasks).
- Codex CLI: local login via `codex login`, no API key required.

## Current File Structure (Top-Level)
- `agent/` - main runtime (modes, tools, integrations, llm, playbooks, memory)
- `docs/` - documentation
- `launchers/` - helper launch scripts
- `runs/` - execution artifacts
- `tests/` - test suite
- `playbooks/` - stored workflows

## Notes
- Playbook runner currently supports `shell`, `python`, and `browser` steps only.
- A Windows-MCP-based Google OAuth playbook exists, but needs MCP execution support in `agent/modes/execute.py` to run.
