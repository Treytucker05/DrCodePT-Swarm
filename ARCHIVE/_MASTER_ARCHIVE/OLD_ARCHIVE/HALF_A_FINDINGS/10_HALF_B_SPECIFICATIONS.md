# HALF B Implementation Blueprint

## Objectives
Deliver a production-ready `addCardToDeck` tool that (1) validates card payloads, (2) writes canonically to PT School decks, (3) pushes notes to AnkiConnect with AnkiWeb fallback, and (4) exposes actionable status/telemetry to both ChatGPT and the dashboard.

## Prerequisites
- Activate `PROGRAMS/fastmcp-server/venv` and install requirements.
- Start Anki desktop and confirm AnkiConnect responds on port 8765.
- Create `.env` in `PROGRAMS/fastmcp-server/` containing `ANKI_CONNECT_URL`, `ANKI_EMAIL`, `ANKI_PASSWORD`, `PT_SCHOOL_ROOT`, `LOG_DIR`.
- Document ngrok restart steps (auth token, command) before touching the running server.

## Implementation Steps
1. **Refactor `server.py`:**
   - Extract the filesystem portion of `addCardToDeck` into helper functions (validation, dedupe hash, deck writer, `_decks-index` updater).
   - Import a new `anki_bridge.py` module that wraps both AnkiConnect and AnkiWeb handlers (reuse code from `_ARCHIVE/phase7_unified_system/backend/anki_handler.py`).
2. **Add Heartbeat Logic:** Ping AnkiConnect `/version` with short timeout. If offline, check if AnkiWeb credentials exist; choose the first reachable target.
3. **Telemetry:** Append a JSON object to `PT School\logs\anki_bridge.log` for every attempt `{timestamp, course, module, cardId, source, anki_status, duration_ms, error}`. Use `Pathlib` + `tempfile` to avoid partial writes.
4. **Concurrency Safety:** Write deck changes to `deck.json.tmp` then atomically rename. Use file locking (e.g., `msvcrt.locking` on Windows) if simultaneous dashboard writes become an issue.
5. **Expose Metadata:** Include `cardId`, `anki_status`, `deckPath`, and `cardCount` in the MCP response. When AnkiConnect returns note IDs, include them under `anki_note_ids`.
6. **Deployment:** Restart StudyMCP locally, run `ngrok http 8000`, and update ChatGPT’s custom tool endpoint if the tunnel URL changes.

## Testing Checklist
- Unit-test helpers (validation, dedupe, log writer) via `pytest` or built-in `unittest` (add `tests/test_add_card.py`).
- Manual tests:
  1. AnkiConnect online → send sample card from Claude/`fastmcp` CLI; verify card appears in Anki deck.
  2. AnkiConnect offline → ensure response is `saved_local` and deck.json increments without throwing.
  3. Duplicate submission → expect `skipped_duplicate`.
- Run Dashboard smoke test to confirm deck counts update after StudyMCP writes.

## Definition of Done
- All 10 HALF_A findings incorporated.
- `HALF_A_FINDINGS/9_STATUS_UPDATE.md` gains “HALF B COMPLETE” note (later).
- ChatGPT demo: ask for a card, watch it appear in Anki within 5 seconds, verify dashboard shows updated count + log entry.
