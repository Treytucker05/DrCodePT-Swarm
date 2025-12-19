# Current Anki Integration State

## Observations (11 Nov 2025)
- `Invoke-WebRequest http://127.0.0.1:8765` returned "AnkiConnect NOT running", so no live Anki desktop bridge is available right now.
- The only automation currently triggered by StudyMCP is the local disk write performed by `addCardToDeck` in `PROGRAMS/fastmcp-server/server.py:250-420` (card appended to `C:\Users\treyt\OneDrive\Desktop\PT School\courses\<Course>\<Module>\deck.json` and indexed via `_decks-index.json`).
- Dashboard/API (`IN_DEVELOPMENT/dashboard-api`) has no direct knowledge of Anki; it simply surfaces whatever is already on disk.

## Existing Code Assets
- `_ARCHIVE/phase7_unified_system/backend/anki_handler.py` still contains two production-ready adapters: `AnkiConnectHandler` (localhost:8765, auto-creates decks and adds notes) and `AnkiWebHandler` (email/password based). They already handle deck creation, note payload construction, and error messaging.
- `DIRECTORY_STRUCTURE.md:244-246` documents the Anki credentials (`<YOUR_ANKI_EMAIL>` / `<YOUR_ANKI_PASSWORD>`, stored locally). No `.env` in the current repo exposes them.
- There is no shared utility module that current code imports, so HALF B will need to either resurrect the archived handler or create a thin wrapper that encapsulates both connection types.

## Credential & Config Inventory
| Item | Location | Status |
| --- | --- | --- |
| Anki email/password | `DIRECTORY_STRUCTURE.md` & `_ARCHIVE/phase7_unified_system/ANKI_SETUP.md` | Documented, not yet loaded into env vars |
| AnkiConnect endpoint | Default `http://127.0.0.1:8765` | Offline (desktop app closed) |
| Anki deck storage | `C:\Users\treyt\OneDrive\Desktop\PT School\courses\...\deck.json` | Healthy; used by dashboard |
| Logging target | _Not configured_ | Needs `PT School\logs\anki_bridge.log` per spec |

## Gaps & Next Steps
1. Add `.env` entries (ANKI_CONNECT_URL, ANKI_EMAIL, ANKI_PASSWORD) and wire them into StudyMCP so we can switch between AnkiConnect and AnkiWeb at runtime.
2. Implement a heartbeat inside `addCardToDeck` (ping `/version`) before deciding whether to call AnkiConnect or fall back to disk-only save.
3. Stand up minimal error telemetry (JSONL log) so we can prove cards were attempted even when Anki is offline.
4. Once AnkiConnect is online, run a manual `curl`/Postman call to verify the addon is reachable before exposing the tool back to ChatGPT.
