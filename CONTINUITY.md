Goal (incl. success criteria):
- Implement smart orchestrator auto-routing in `agent/treys_agent.py`, replacing manual mode selection prompts.

Constraints/Assumptions:
- Keep changes minimal and scoped; follow existing Python style (4-space indent).
- Avoid destructive actions unless explicitly requested.
- Update imports as needed; retain existing behavior except for routing changes.
- Tests: run `pytest -q` if relevant and feasible.

Key decisions:
- Follow user-specified smart_orchestrator logic and routing flow.

State:
  - Done:
    - Read AGENTS.md and existing CONTINUITY.md.
  - Now:
    - Inspect `agent/treys_agent.py` for assess_task_complexity and pending_task flow.
  - Next:
    - Implement `smart_orchestrator`, replace manual prompt flow, update imports.

Open questions (UNCONFIRMED if needed):
- None.

Working set (files/ids/commands):
- `agent/treys_agent.py`
- `CONTINUITY.md`
