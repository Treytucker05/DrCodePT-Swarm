# CONTINUITY.md

Goal (incl. success criteria):
- Synthesize provided agent gap findings into prioritized lists and output JSON with high/medium/low/flagged/discarded arrays.

Constraints/Assumptions:
- Provided findings payload is empty for Static/Dynamic/Research; only Critic summary notes missing findings.
- Response must be JSON-only per user schema and kept under ~800 tokens.

Key decisions:
- Treat missing findings as no scorable gaps; return empty arrays.

State:
  - Done: Read prior ledger content.
  - Now: Update ledger and prepare JSON output.
  - Next: Respond with JSON containing empty lists.

Open questions (UNCONFIRMED if needed):
- None.

Working set (files/ids/commands):
- CONTINUITY.md
