# Decision Matrix – Phase 2C

| Decision | Options Considered | Criteria | Recommendation | Rationale |
| --- | --- | --- | --- | --- |
| Primary Anki bridge | A) AnkiConnect only; B) AnkiWeb only; C) Hybrid (AnkiConnect first, fall back to AnkiWeb; always save deck.json) | Reliability offline, implementation effort, latency, credential exposure | **C) Hybrid** | Provides instant sync when desktop app is open, but never blocks Claude because deck.json save always succeeds; leverages archived handlers for AnkiWeb as tertiary path. |
| Deployment priority (ChatGPT vs Dashboard) | A) Finish Dashboard smoke tests; B) Deliver ChatGPT→Anki bridge first; C) Parallelize | Speed to value, dependency order, owner availability | **B) ChatGPT→Anki first** | Once addCardToDeck works end-to-end, Dashboard simply reads richer metadata. Dashboard polish can wait; Trey wants ChatGPT-driven studying immediately. |
| StudyMCP hosting | A) Keep on Trey’s laptop via ngrok; B) Move to dedicated VM; C) Hybrid | Cost, effort, need for local filesystem access | **A short-term, B long-term** | Phase 2C requires PT School filesystem + Anki desktop, so laptop hosting stays for now. Document path to B once automation no longer depends on local Anki. |
| Card validation | A) Accept any payload; B) Strict schema with length/duplicate checks; C) Add AI quality gate first | Developer time, risk of corrupt decks, user trust | **B) Strict schema** | Already scaffolded in `server.py`; ensures idempotency and prevents runaway duplicates before automation scales. |
| Observability | A) Rely on console logs; B) Structured JSON logs only; C) Structured logs + dashboard surfacing | Debuggability, implementation effort | **C)** | Minimal extra work (json line file) unlocks Dashboard transparency and simplifies support when ChatGPT says “card added” but user can’t see it. |

## Additional Notes
- **Security posture:** keep Anki credentials in `.env` + Windows Credential Manager; avoid hard-coding into repo.
- **Failure policy:** ChatGPT must receive deterministic messages so it knows whether to retry; therefore the spec emphasizes explicit `anki_status` enums.
- **Human review:** Dashboard will surface a per-course queue so Trey can spot-check cards before they hit Anki (optional toggle in HALF B scope if time permits).
