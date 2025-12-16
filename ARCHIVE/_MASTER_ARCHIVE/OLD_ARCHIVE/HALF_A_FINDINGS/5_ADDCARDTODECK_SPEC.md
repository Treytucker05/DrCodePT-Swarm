# addCardToDeck Technical Specification

## Purpose
Expose a single MCP tool that lets ChatGPT (and eventually the dashboard API) persist a flashcard into both the PT School filesystem and Anki, returning structured status metadata so Claude can confirm success or retry intelligently.

## Inputs
| Field | Type | Details |
| --- | --- | --- |
| `course` | string | Human-readable PT course name; maps directly to `C:\Users\treyt\OneDrive\Desktop\PT School\courses\<course>` |
| `module` | string | Folder-safe module/week identifier inside the course directory |
| `deck` | string | Deck display name; persisted to deck metadata and used when creating Anki decks |
| `front` | string | 1–10k chars; sanitized of control chars, normalized whitespace |
| `back` | string | 1–10k chars; sanitized like `front` |
| `tags` | string[] | Optional taxonomy; default `[]` |
| `difficulty` | enum | `easy|medium|hard` (default `medium`) |
| `source` | string | `chatgpt|dashboard|api|manual` – stored for audit |

## Outputs
```
{
  success: bool,
  cardId: uuid4,
  deckPath: string,
  anki_status: "added_to_anki" | "saved_local" | "skipped_duplicate" | "error",
  message: string,
  course: string,
  module: string,
  deck: string,
  cardCount: int,
  timestamp: ISO 8601,
  retriesRemaining?: int,
  error_detail?: string
}
```

## Processing Steps
1. Validate payload (non-empty strings, tag array, difficulty enum). Reject with aggregated message if invalid.
2. Build and ensure directories under PT School, then load or initialize `deck.json` (Anki import schema: deck metadata + `cards` array).
3. Compute a deterministic hash (`sha256(f"{course}|{module}|{deck}|{front}|{back}")`). If the hash exists inside deck metadata, short-circuit with `anki_status="skipped_duplicate"`.
4. Append the sanitized card (including tags, difficulty, hash, source) and persist `deck.json` + `_decks-index.json` (course-level summary already implemented in `server.py:567-640`).
5. **Anki bridge:**
   - Ping `AnkiConnect /version` (timeout 2s). If OK, call `createDeck` (idempotent) and `addNotes`, capturing returned note IDs → respond with `anki_status="added_to_anki"`.
   - If AnkiConnect offline and `.env` exposes `ANKI_EMAIL`/`ANKI_PASSWORD`, fall back to `AnkiWebHandler` (archived implementation).
   - If both paths fail, keep `deck.json` save, log the payload + error to `PT School\logs\anki_bridge.log`, and return `anki_status="saved_local"` (success) or `"error"` (if disk write failed).
6. Emit a structured log line `{timestamp, source, course, module, cardId, anki_status, message}` for observability.

## Non-Functional Requirements
- Execution time < 2s when AnkiConnect online, < 300ms when offline fallback triggered.
- No secrets in logs; redact `ANKI_PASSWORD`.
- Tool must be idempotent and safe for concurrent calls (use file locks or write-temp-then-rename pattern for deck files).
