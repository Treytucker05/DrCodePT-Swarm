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
- Speak naturally; you don't need tool names.
- I will ask before running actions and confirm when something is destructive.
- Use Team for execution, Think for planning, Mail for email workflows, Research for sources.

## Continuity Ledger (OPTIONAL - for complex multi-session tasks)
CONTINUITY.md is designed for long-running, complex tasks. For simple autonomous tasks (like OAuth setup), use memory + reflection instead.

**When to use CONTINUITY.md:**
- Complex tasks spanning multiple sessions  
- Multi-step projects with many dependencies
- Swarm/Team mode operations

**When NOT to use:**
- Simple one-session tasks
- Quick autonomous operations  
- Straightforward goals with <20 steps

### How it works (when using it)
- At the start of turns (for complex tasks): read CONTINUITY.md, update goal/constraints/decisions/state, then proceed.
- Update when things change: goal, constraints, key decisions, progress state, or important outcomes.
- Keep it short: facts only, no transcripts. Mark uncertainty as UNCONFIRMED.
- If missing recall: refresh ledger from context, mark gaps UNCONFIRMED, ask targeted questions, continue.

### `functions.update_plan` vs the Ledger
- `functions.update_plan` is for short-term execution scaffolding while you work (a small 3-7 step plan with pending/in_progress/completed).
- `CONTINUITY.md` is for long-running continuity across compaction (the "what/why/current state"), not a step-by-step task list.
- Keep them consistent: when the plan or state changes, update the ledger at the intent/progress level (not every micro-step).

### In replies
- Begin with a brief "Ledger Snapshot" (Goal + Now/Next + Open Questions). Print the full ledger only when it materially changes or when the user asks.

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
