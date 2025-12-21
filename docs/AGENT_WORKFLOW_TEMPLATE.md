# Agent Workflow Template (Mail)

This template captures the end-to-end workflow used in the Mail automation slice so it can be reused for other domains.

## 1) Procedure schema (memory)
- Source of truth: `agent/memory/procedures/mail_yahoo.py`
- Data file: `agent/memory/procedures/mail_yahoo_folders.json`
- Core fields per rule:
  - `name`
  - `from_contains` / `subject_contains` (search tokens)
  - `to_folder`
  - `search_folders` (ordered list, default [`INBOX`])
  - `max_messages`
- Guardrails:
  - never delete
  - never move into/out of protected folders
  - skip moves where `source_folder == to_folder`

## 2) Deterministic executor
- Implementation: `agent/autonomous/tools/mail_yahoo_imap_executor.py`
- Reads procedure via `load_procedure()`
- Modes:
  - `--dry-run` (default): plan only, write artifacts
  - `--execute`: perform IMAP MOVE for planned UIDs
  - `--scan-all-folders`: readonly scan, counts only, no planning/moves
- Artifacts per run:
  - `runs/<run_id>/mail_plan.json`
  - `runs/<run_id>/mail_report.md`
  - `runs/<run_id>/mail_scan.json` (scan mode)

## 3) Guided mode (interactive)
- Implementation: `agent/autonomous/modes/mail_guided.py`
- Flow:
  1. Scan folders first and summarize
  2. Questioner -> Planner -> Critic (Codex calls)
  3. Save procedure changes
  4. Run dry-run executor
  5. If planned_moves == 0: do NOT prompt for EXECUTE
  6. If planned_moves > 0: require user to type `EXECUTE`
- Auto-recovery:
  - If zero planned moves but objective implies moves, run scan mode
  - Prompt user to choose folders, update `search_folders`, rerun dry-run

## 4) Approval gate
- The only execution gate is the literal `EXECUTE` input in guided mode.
- Do not execute if planned_moves == 0 or if session is planning-only.

## 5) Tests (offline)
- Planning logic tests: `tests/test_mail_executor_planning.py`
  - Verifies planning uses `search_folders`
  - Verifies protected folder guardrails
  - Verifies skip when source == target

## 6) Example command sequence
1. Seed or update procedure:
   - `python -c "from agent.memory.procedures.mail_yahoo import load_procedure, save_procedure; ..."`
2. Scan:
   - `python -m agent.autonomous.tools.mail_yahoo_imap_executor --scan-all-folders`
3. Dry-run:
   - `python -m agent.autonomous.tools.mail_yahoo_imap_executor --dry-run --max-per-rule 5`
4. Execute:
   - `python -m agent.autonomous.tools.mail_yahoo_imap_executor --execute --max-per-rule 5`
5. Guided:
   - `python -m agent.autonomous.modes.mail_guided`

## 7) Reuse for other domains
Apply the same pattern:
- procedure schema -> deterministic executor -> guided mode -> dry-run -> approval gate -> execute -> artifacts -> tests.
