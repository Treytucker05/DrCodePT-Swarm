# HALF A Status Update (Nov 12, 2025)

## What Works Today
- **Blackboard agent** continues to deliver 48 due dates across the 5 PT courses (ref. `MASTER_DUE_DATES.txt`, `GAMEPLAN.md:70-74`).
- **StudyMCP core tools** (`list_modules`, `ingest_module`, `search_facts`, `export_module`) operate locally and via the existing ngrok tunnel; manifests and SQLite stores are intact.
- **Dashboard/API** stack is code-complete for Phase 2C (11 endpoints, working deck persistence) and already reads the same PT School filesystem used by StudyMCP.
- **Filesystem organization** (`PT School/courses` + `_decks-index.json`) is stable; card creation via dashboard proves write permissions.

## What’s Missing
- `addCardToDeck` still writes only to disk, so ChatGPT cannot fulfill the “cards show up in Anki automatically” promise.
- AnkiConnect is not running, `.env` lacks credentials, and there is no retry/logging mechanism if Anki is offline.
- No consolidated observability: we cannot tell which cards came from ChatGPT vs manual entry, nor whether they synced.
- Documentation for restarting StudyMCP + ngrok is tribal knowledge; redeploying the updated tool would be risky without a runbook.

## Blockers / Risks
1. **Environment drift:** The StudyMCP instance ChatGPT currently hits may not be this laptop; we must confirm before editing production code.
2. **Credential handling:** Storing Anki passwords securely is mandatory before HALB B ships; leaking them via logs or repo history would be a critical failure.
3. **OneDrive conflicts:** Deck files live in a synced folder; simultaneous writes (dashboard + StudyMCP) could cause sync duplicates unless we implement atomic writes.

## Immediate Next Steps
1. Implement the finalized `addCardToDeck` specification (see `HALF_A_FINDINGS/5_ADDCARDTODECK_SPEC.md`) and wire in the hybrid Anki bridge.
2. Stand up telemetry (`PT School\logs\anki_bridge.log`) and expose summarized status back to ChatGPT/dashboard.
3. Document and test the AnkiConnect heartbeat + ngrok restart flow so Trey can confidently redeploy after code changes.
4. Refresh `MASTER_DUE_DATES.txt` from the latest Blackboard scrape to keep course audits in sync with what the dashboard displays.

HALF A is complete: the planning artifacts now cover architecture, dependencies, and explicit marching orders for HALF B.
