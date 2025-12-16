# Phase 2C Integration Architecture

## Components
1. **Blackboard Agent** (`PROGRAMS/blackboard-agent`) – Selenium + Claude tools that scrape portal data and drop artifacts into `PT School/courses/` and reference planners.
2. **Study Materials Repository** (`PROGRAMS/study-materials` + `PT School/`) – Source-of-truth filesystem consumed by every downstream service.
3. **StudyMCP** (`PROGRAMS/fastmcp-server`) – FastMCP app exposing structured tools (`list_modules`, `ingest_module`, `search_facts`, `export_module`, `addCardToDeck`). Hosts SQLite fact stores per module and writes decks.
4. **Dashboard/API** (`IN_DEVELOPMENT/dashboard-api`) – Express service + static dashboard that reads/writes `PT School` decks, offers human oversight, and will surface card/Anki sync status once the bridge exists.
5. **ChatGPT + ngrok** – External consumer hitting StudyMCP tools through an ngrok tunnel, currently limited to list/search/export flows.
6. **Anki Desktop / AnkiConnect** – Local spaced-repetition endpoint (port 8765) that must receive cards to finish the workflow.

## Data Flow (Target)
```
Blackboard Agent ──> PT School corpus ──┐
Manual uploads ────────────────────────┘
                                        ▼
                                   StudyMCP
                        ┌───────────┴────────────┐
                        │ list/ingest/search/export │
                        │ addCardToDeck (new)     │
                        └───────────┬────────────┘
                                    ▼
                 Deck JSON + logs in PT School (source-of-truth)
                                    ▼
          ┌──────────────┬──────────┴─────────┬──────────────┐
          │ Dashboard/API│ ChatGPT response  │ AnkiConnect  │
          │ (read/write) │ (status + IDs)    │ (push notes) │
          └──────────────┴────────────────────┴──────────────┘
```

## Integration Touchpoints
- **Filesystem contract:** Every component reads/writes PT School decks, so file structure must stay stable. Implement file locking when StudyMCP and Dashboard can mutate the same deck simultaneously.
- **Identity:** `addCardToDeck` should stamp `card.source`, `requested_by`, `cardId`, and optionally `openai_conversation_id` (passed through from ChatGPT) so Dashboard can trace provenance.
- **Telemetry:** A single log directory (`PT School\logs`) should receive append-only JSON lines from StudyMCP so Dashboard can replay operations and render history.
- **Network:** StudyMCP remains the only service exposed over ngrok. Dashboard stays local; it consumes the same deck files, so no extra tunnel is required.

## Failure Modes & Mitigations
| Failure | Impact | Mitigation |
| --- | --- | --- |
| Anki offline | Cards stuck in deck.json | mark `saved_local`, queue retry job once AnkiConnect heartbeat passes |
| PT School path unavailable (OneDrive locked) | Card creation fails | bubble error to ChatGPT + log; add retry/backoff |
| Duplicate card submissions | Inflated decks | deterministic hash dedup + respond `skipped_duplicate` |
| Ngrok tunnel drops | ChatGPT tools unavailable | Document restart recipe + monitor ngrok status |

With these contracts documented, HALF B only needs to implement the Anki bridge + telemetry to complete the architecture.
