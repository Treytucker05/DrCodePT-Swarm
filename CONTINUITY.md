Goal (incl. success criteria):
- Set up Google Calendar OAuth for the project; success when OAuth credentials/config and flow are in place and documented.
Constraints/Assumptions:
- Follow existing style; minimal scoped changes; avoid unrelated files.
- Safe-by-default; no destructive actions; approval policy never.
- Run `pytest -q` for relevant changes.
Key decisions:
- None yet.
State:
  - Done:
- Read ledger.
- Observed prior scan_repo action failed postconditions (no candidate OAuth files identified).
  - Now:
 - Locate project files relevant to Google Calendar OAuth setup.
  - Next:
 - Propose next change based on findings.
Open questions (UNCONFIRMED if needed):
- Target app type (web app, desktop, CLI) and callback/redirect URI requirements?
- Where should credentials/config live (env vars, config file) and which Google API project?
Working set (files/ids/commands):
- CONTINUITY.md
