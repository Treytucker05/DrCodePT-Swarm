# Workflow Analysis – Current vs Target

## Present-Day Flow (Without addCardToDeck)
1. **Blackboard Agent** (`PROGRAMS/blackboard-agent`) scrapes due dates + pulls down slide decks/transcripts, saving artifacts under `C:\Users\treyt\OneDrive\Desktop\PT School\courses\<Course>\...`.
2. **Study materials** are curated manually inside PT School folders; `study-materials/` mirrors the same hierarchy for static references.
3. **Card creation** happens through the dashboard API/UI (IN_DEVELOPMENT/dashboard-api) or the standalone card generator. Both persist to `deck.json` but stop short of Anki.
4. **ChatGPT** connects to StudyMCP via ngrok, but only uses `list_modules`/`ingest_module`/`search_facts`/`export_module`. When Trey asks for cards, ChatGPT exports JSON/CSV and Trey imports them manually into Anki.

Result: Blackboard → PT School disk → Dashboard/ChatGPT → manual Anki import. No closed loop exists, and there is no audit log tying ChatGPT requests to final Anki notes.

## Target Phase 2C Flow (After HALF B)
```
Blackboard Agent ─┐
                   ├─> PT School corpus ──> StudyMCP (facts.db)
Manual uploads ───┘                           │
                                              ├─ list/search/export
ChatGPT card request ──> addCardToDeck tool ──┼─ write deck.json (always)
                                              ├─ call AnkiConnect (when online)
                                              └─ log + respond back to ChatGPT
Dashboard API/UI <────── reads PT School decks + status metadata
Anki Desktop <────────── receives cards via AnkiConnect or manual import fallback
```

## Missing Links
- The **bridge from StudyMCP to Anki** is only half-built (local JSON write). Without AnkiConnect, ChatGPT cannot immediately validate that cards exist in the spaced-repetition system.
- **State propagation**: Dashboard has no idea whether a card came from ChatGPT, whether it reached Anki, or whether a retry is required.

## Implications for HALF B
- `addCardToDeck` must become the single ingestion point for all card requests, tagging each card with provenance (`source: chatgpt|dashboard|api`).
- After the tool logs success/failure, Dashboard can surface true end-to-end status (e.g., total cards, pending sync, error queue), eliminating manual spreadsheets.
- Once this loop is in place, Trey only needs to open Anki + ChatGPT; everything else is orchestrated automatically.
