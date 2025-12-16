# START HERE - DrCodePT-Swarm

Last Updated: November 13, 2025
Current Phase: Phase 3 - Tool Use API Integration
Status: Phase 2 Complete â†’ Phase 3 Planning

---

## What is DrCodePT-Swarm?

An AI-powered study automation system for UTMB DPT coursework that orchestrates three integrated components:

- Blackboard Agent â€” Scrapes course data, announcements, due dates from UTMB portal
- Dr. CodePT (RAG Client) â€” Queries your textbooks via AnythingLLM (RAG-only)
- FastMCP Server â€” Bridges ChatGPT via MCP and syncs cards to Anki

---

## Phase 2 Complete: What Works

| Component | Status | Details |
|-----------|--------|---------|
| Blackboard Login | Ready | Selenium automation working |
| Course Extraction | Ready | All 5 courses loaded from UTMB |
| Due Dates Extracted | Ready | 48 total (Legal 14, Lifespan 2, Pathology 22, Anatomy 6, Exam Skills 4) |
| Anki Integration | Ready | Card pipeline tested |
| FastMCP Server | Ready | Running, tools registered |

---

## Tool Use Architecture (Phase 3)

Goal: ChatGPT orchestrates tools via MCP. You talk naturally; tools handle the work.

See: PROJECT_STATUS.md and EXECUTION_PLAN.md for details.

---

## Quick Navigation

| File | Purpose |
|------|---------|
| PROJECT_STATUS.md | Current phase, completed work, next steps |
| SYSTEM_INVENTORY.md | What exists (code, configs, data) |
| EXECUTION_PLAN.md | Specific Phase 3 milestones and action items |
| MASTER_PLAN.md | Long-term vision and architecture |
| CODEX.md | AI agent role definitions and protocols |

---

## Relaunching With Codex Cloud (fast checklist)

- Make the repo available: upload a fresh zip of this folder or point Codex Cloud at your private Git remote.
- When Codex asks for permissions, allow edits/tests inside the repo sandbox so tool runs can execute.
- For the SDK sample, go to `PROGRAMS/codex-agent-sdk-demo/`, run `npm install`, then `npm run demo -- "<task>"` (set `CODEX_WORKDIR` to the target project path if needed).
- Keep “how to launch” notes here and in `PROGRAMS/codex-agent-sdk-demo/README.md`; update them if paths or steps change.

---

## Getting Started (Run Commands)

- Blackboard Agent
  - Path: PROGRAMS/blackboard-agent
  - Run: python agent.py (install requirements.txt first)

- Dr. CodePT â€” RAG Client
  - Path: PROGRAMS/drcodept-rag
  - Run: START_DR_CODEPT_RAG.bat (or python drcodept.py) (requires AnythingLLM at http://localhost:3001)

- FastMCP Server (ChatGPT â†” Anki)
  - Path: PROGRAMS/fastmcp-server
  - Run: START_MCP_SERVER.bat or python -m uvicorn server:app --host 127.0.0.1 --port 8000

General orientation:
1) Read PROJECT_STATUS.md for current progress
2) Check SYSTEM_INVENTORY.md to see what's deployed
3) Review EXECUTION_PLAN.md for immediate action items
4) Browse PROGRAMS/ for working code

Codex Tasks (for Claude â†’ Codex coordination):
- Folder: Codex Tasks
- Inbox: Codex Tasks/TASKS.md
- Persistent state: Codex Tasks/CLAUDE_STATE.md

