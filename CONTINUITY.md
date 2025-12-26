Goal (incl. success criteria):
- Organize Downloads folder by date (MM/YYYY) using shortcut target; move files only.

Constraints/Assumptions:
- Use shortcut target path from user; no deletions.
- Minimal, scoped changes; avoid unrelated files.
- Tests: run pytest -q for relevant changes (likely N/A).

Key decisions:
- Date-based organization in MM/YYYY folders using file modified date.

State:
  - Done:
    - Read existing ledger.
  - Now:
    - Produce deterministic playbook JSON for organizing Downloads.
  - Next:
    - Return JSON response only.

Open questions (UNCONFIRMED if needed):
- None.

Working set (files/ids/commands):
- CONTINUITY.md
