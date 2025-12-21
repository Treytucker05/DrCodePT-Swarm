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
