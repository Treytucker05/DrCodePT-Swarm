# DrCodePT-Swarm Agent Guide

## Coding Standards
- Python: follow existing style (4-space indent, no broad reformatting).
- Keep changes minimal and scoped; avoid touching unrelated files.
- Tests: run `pytest -q` for relevant changes.

## Safety Defaults
- Safe-by-default: avoid destructive actions unless explicitly requested.
- Dangerous tools require user confirmation (human_ask or explicit approval).
- Prefer read-only checks before write operations.

## When to Ask vs Proceed
- Ask the user when requirements, preferences, or constraints are missing.
- Ask before irreversible actions (delete, overwrite, submit, purchase).
- Proceed without asking for low-risk, reversible steps (list, read, plan).

## Phase Machine Rules (Supervisor Team Mode)
- Phases: OBSERVE → RESEARCH → PLAN → EXECUTE → VERIFY → REFLECT → repeat.
- Explicit phase banners must be logged.
- ASK_USER blocks progress until answers are provided.
- Loop detection should trigger RESEARCH, ASK_USER, or a pivot.
- Bounded retries: max 2 per step before ABORT.

## Q&A Gating
- Never proceed past ASK_USER without answers.
- Summarize captured answers before resuming PLAN.

## User Interaction Model
- Speak naturally; you don’t need tool names.
- I will ask before running actions and confirm when something is destructive.
- Use Team for execution, Think for planning, Mail for email workflows, Research for sources.

## Continuity Ledger (compaction-safe)
Maintain a single Continuity Ledger for this workspace in `CONTINUITY.md`. The ledger is the canonical session briefing designed to survive context compaction; do not rely on earlier chat text unless it’s reflected in the ledger.

### How it works
- At the start of every assistant turn: read `CONTINUITY.md`, update it to reflect the latest goal/constraints/decisions/state, then proceed with the work.
- Update `CONTINUITY.md` again whenever any of these change: goal, constraints/assumptions, key decisions, progress state (Done/Now/Next), or important tool outcomes.
- Keep it short and stable: facts only, no transcripts. Prefer bullets. Mark uncertainty as `UNCONFIRMED` (never guess).
- If you notice missing recall or a compaction/summary event: refresh/rebuild the ledger from visible context, mark gaps `UNCONFIRMED`, ask up to 1–3 targeted questions, then continue.

### `functions.update_plan` vs the Ledger
- `functions.update_plan` is for short-term execution scaffolding while you work (a small 3–7 step plan with pending/in_progress/completed).
- `CONTINUITY.md` is for long-running continuity across compaction (the “what/why/current state”), not a step-by-step task list.
- Keep them consistent: when the plan or state changes, update the ledger at the intent/progress level (not every micro-step).

### In replies
- Begin with a brief “Ledger Snapshot” (Goal + Now/Next + Open Questions). Print the full ledger only when it materially changes or when the user asks.

### `CONTINUITY.md` format (keep headings)
- Goal (incl. success criteria):
- Constraints/Assumptions:
- Key decisions:
- State:
  - Done:
  - Now:
  - Next:
- Open questions (UNCONFIRMED if needed):
- Working set (files/ids/commands):
