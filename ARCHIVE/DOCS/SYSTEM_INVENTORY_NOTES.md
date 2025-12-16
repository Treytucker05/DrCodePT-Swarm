# DrCodePT-Swarm – System Inventory (Working Notes)

_Last updated: by Codex assistant, before restart._

These notes capture what you and I decided so far so we can pick up later.

---

## 1. Core systems to KEEP (actively used)

- `LAUNCH_CODEX.bat` / `LAUNCH_CODEX.ps1`
  - Purpose: Quick way to start Codex in this folder so the assistant can inspect/edit files.
  - Status: WORKING and IMPORTANT. Do **not** remove.

- `START_MCP_SERVER.bat` + `PROGRAMS\fastmcp-server`
  - Purpose: Flashcard pipeline. ChatGPT (Study system) → FastMCP → Anki cards.
  - Status: CORE / MUST HAVE. Can be simplified later, but functionality is essential.

- `PDF_SPLITTER_AND_OCR\ocr_textbook.py`
  - Purpose: Splits and OCRs school textbooks into chapters for study.
  - Status: WORKING and USED A LOT. Keep as a main tool.

---

## 2. Systems to KEEP as building blocks

- `PROGRAMS\drcodept-rag`
  - Role: Original DrCodePT RAG client. Good structure for future local RAG (Ollama / AnythingLLM / Dolphin) over textbooks.
  - Decision: KEEP for framework. Not actively used now, but useful as a base.

- `PROGRAMS\blackboard-agent`
  - Role: PT School assistant using Claude tool use (Blackboard, file management, Microsoft To Do UI automation).
  - Decision: KEEP for now. Heavy and time-consuming, but has useful pieces (e.g., due-date extraction, computer_use tools).
  - Future: Likely mine pieces and/or redesign around newer agents (ChatGPT Agents / AbacusAI).

- `PROGRAMS\dashboard-api`
  - Role: Node/Express dashboard + API. Serves web UI and currently has Microsoft To Do integration via Microsoft Graph.
  - Decision: KEEP the project. Use as future central hub (talk to agent, see tasks, launch tools).
  - Important: Microsoft To Do integration is a dead end (personal account issues). We plan to pivot to **Google Tasks**.

---

## 3. Files already DELETED (safe removals)

These were removed during cleanup:

- `SET-UBUNTU-DEFAULT.bat`
  - Old helper for setting Ubuntu as default WSL distro. Not used anymore.

- `START_DRCODEPT.bat` (root)
  - Thin wrapper that just called `START_MCP_SERVER.bat`. You only use `START_MCP_SERVER.bat` directly.

- `PROGRAMS\fastmcp-server\START_DRCODEPT.bat`
  - Redundant FastMCP launcher. We rely on `START_MCP_SERVER.bat` and the PowerShell script instead.

- `_MASTER_ARCHIVE\_ARCHIVE\phase7_unified_system\.venv\Scripts\activate.bat`
- `_MASTER_ARCHIVE\_ARCHIVE\phase7_unified_system\.venv\Scripts\deactivate.bat`
- `_MASTER_ARCHIVE\_ARCHIVE\phase7_unified_system\.venv\Scripts\Activate.ps1`
  - Auto-generated venv scripts in an archived system. Safe to remove; not used by current tools.

- `AUTHENTICATE_TODO.bat`
  - Microsoft To Do OAuth helper for the old dashboard flow.

- `SETUP_TODO_COMPLETE.bat`
  - One-shot setup + Microsoft To Do auth for the old dashboard.

- `LAUNCH_DRCODEPT_COMPLETE.bat`
  - Combined launcher that depended on a Microsoft To Do token.

None of these were part of your currently used workflows (flashcards, Codex, OCR, etc.).

---

## 4. Systems still present but to rethink

### Dashboard + tasks

- Current state:
  - `PROGRAMS\dashboard-api` still exists and serves a web UI.
  - Microsoft To Do integration is not useful (personal account / API issues).
  - Old To Do batch files have been deleted.
- Future direction:
  - Use the dashboard as your **central hub**:
    - Talk to your agent.
    - Show tasks (migrate to **Google Tasks** or another provider).
    - Launch core tools (flashcards, OCR, PT assistant, etc.).
  - Design it as a thin launcher/view layer over separate, well-defined tools.

### PT assistant (`blackboard-agent`)

- Current state:
  - Works ~80% but is heavy and time-consuming to maintain.
  - Uses Claude + tool use, plus `computer_use` automation (including Microsoft To Do desktop automation).
- Future direction:
  - Decide which parts are actually valuable (e.g., course scraping, due-date extraction).
  - Possibly re-implement behavior using ChatGPT Agents / AbacusAI for more maintainable automation.

---

## 5. Design principle we agreed on

- **1 tool = 1 job = 1 launcher** (at least at first):
  - Flashcards → `START_MCP_SERVER.bat` + FastMCP.
  - Textbook OCR/splitting → `ocr_textbook.py`.
  - PT assistant → `blackboard-agent`.
  - RAG stack → `drcodept-rag` (future).
- Make each tool work standalone and be easy to start/stop.
- Later, build a **thin central dashboard/launcher** that calls into these tools instead of stuffing all logic into one app.

This helps avoid the previous pattern where files and responsibilities got scattered and AI lost context.

---

## 6. Suggested next steps after restart

When you come back:

1. **Confirm core launchers still work**
   - Test `LAUNCH_CODEX.bat` (Codex starts in the right folder).
   - Test `START_MCP_SERVER.bat` (FastMCP server + Anki workflow).
   - Confirm `ocr_textbook.py` still runs for a sample PDF.

2. **Decide which system to refine first**
   - Option A: Flashcard pipeline – simplify config, document how to use it from ChatGPT.
   - Option B: Central dashboard – define what the new Google Tasks-based hub should do.
   - Option C: PT assistant – identify the specific features you actually want to keep.

3. **Gradually separate and then reconnect**
   - Keep each system small and focused.
   - Only after they’re stable, add a central launcher/dashboard that ties them together.

---

## 7. How to resume with the assistant

When you restart and reopen Codex in this folder:

- Open this file: `DOCS\SYSTEM_INVENTORY_NOTES.md`.
- Tell the assistant: “Read `DOCS\SYSTEM_INVENTORY_NOTES.md` and continue the cleanup/plan from there.”

We can then:
- Update this inventory if anything changed.
- Design the new central dashboard and Google Tasks integration.
- Decide what to archive or refactor in `blackboard-agent` and `drcodept-rag`.

