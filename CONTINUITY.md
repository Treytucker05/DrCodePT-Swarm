Goal (incl. success criteria):
- Implement smart orchestrator auto-routing in `agent/treys_agent.py`, replacing manual mode selection prompts.

Constraints/Assumptions:
- Keep changes minimal and scoped; follow existing Python style (4-space indent).
- Avoid destructive actions unless explicitly requested.
- Update imports as needed; retain existing behavior except for routing changes.
- Tests: run `pytest -q` if relevant and feasible.

Key decisions:
- Follow user-specified smart_orchestrator logic and routing flow.
- Route ambiguous tasks through smart_orchestrator; keep explicit `collab:` override.

State:
  - Done:
    - Added `smart_orchestrator` and wired it into main routing to replace manual mode prompts.
    - Updated imports to support playbook matching in the orchestrator.
    - Updated help text to reflect auto-routing.
    - Limited collaborative auto-detect to smart_orchestrator (explicit `collab:` still supported).
    - Ran `pytest -q` (failed: missing `list_profiles` import in tests).
  - Now:
    - Await user review; decide on next steps for test failure.
  - Next:
    - (Optional) Fix or skip failing tests if requested.

Open questions (UNCONFIRMED if needed):
- None.

Working set (files/ids/commands):
- `agent/treys_agent.py`
- `CONTINUITY.md`
