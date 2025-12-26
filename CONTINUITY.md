Goal (incl. success criteria):
- Fix smart_orchestrator research routing so "Search for Google OAuth docs" triggers research mode: ensure "search" and "docs" keywords trigger, research auto-executes without confirmation, and research bypasses playbook matching; verify with routing test.

Constraints/Assumptions:
- Keep changes minimal and scoped; follow existing Python style (4-space indent).
- Avoid destructive actions unless explicitly requested.
- Test routing with: "Search for Google OAuth docs".

Key decisions:
- None yet.

State:
  - Done:
    - Read existing continuity ledger.
    - Added "search"/"docs" research triggers and moved research routing ahead of playbook matching.
    - Ran routing check for "Search for Google OAuth docs" -> research mode.
    - Ran `pytest -q`; fails during collection: ImportError for `list_profiles` in `tests/test_profiles.py`.
  - Now:
    - Review changes and report results.
  - Next:
    - None.

Open questions (UNCONFIRMED if needed):
- None.

Working set (files/ids/commands):
- `DrCodePT-Swarm/agent/treys_agent.py`
- `DrCodePT-Swarm/CONTINUITY.md`
