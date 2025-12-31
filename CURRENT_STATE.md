# CURRENT_STATE.md (Snapshot)

**Status:** Historical/Archive. Do not update as a source of truth. See `AGENT_BEHAVIOR.md` and `conductor/tracks.md`.
**Update Note (2025-12-31):** Updated per request to capture current blockers and fixes in progress.

Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
## Summary (Dec 31, 2025)
- Unified agent fast-paths work (file create/read/open).
- Google OAuth desktop setup is mostly automated, but **multi-monitor focus** caused OCR to target the wrong window.
- Added Win32 focus + move-to-primary logic to force Chrome foreground; needs verification on multi-monitor.
- Added pytesseract to requirements and explicit OCR dependency checks.
- Codex CLI errors can occur when running a second agent in a non‑TTY terminal.

## What Works
- Chat-only conversation (no tools by default).
- Research mode (web_search + summaries).
- Basic Execute/playbook actions for shell/python/browser flows.
- Credential storage and issue tracking.

## Partially Working / Manual Steps
- Playbooks: some flows still need manual intervention.
- Google OAuth setup: manual 2FA required; automation still fails if Chrome is not foreground (multi-monitor focus).
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
