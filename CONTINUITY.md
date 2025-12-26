Goal (incl. success criteria):
- Fix BrokenPipeError by switching _call_codex to non-interactive subprocess.run (stdin input, stdout output) and removing streaming writes.

Constraints/Assumptions:
- Keep changes minimal and scoped; follow existing Python style (4-space indent).
- Avoid destructive actions unless explicitly requested.

Key decisions:
- None yet.

State:
  - Done:
    - Added direct web_search routing for "search for" queries.
    - Added "search for" to execute phrases.
    - Updated _run_web_search to call web_search directly with a temporary RunContext.
    - Added web_fetch follow-up to extract steps from the selected result.
    - Added HTML cleaning, main/article focus, stricter step filtering, and noisy extraction guard.
    - Updated _call_codex to use Codex CLI --non-interactive with subprocess.run and removed streaming stdin writes.
  - Now:
    - Summarize changes.
  - Next:
    - (Optional) Run a quick manual research run if requested.

Open questions (UNCONFIRMED if needed):
- None.

Working set (files/ids/commands):
- `DrCodePT-Swarm/agent/modes/research.py`
- `DrCodePT-Swarm/CONTINUITY.md`
