# Task 00 — Baseline: reproduce swarm repo-audit failure

## Primary goal
Restore **Swarm mode for repo audits** (tests + real run).

## Steps
1) Reproduce failing case(s)
   - Run targeted tests: `python -m pytest -q tests/test_swarm_*.py`
   - Run a minimal swarm repo-audit invocation (the smallest command that triggers the failure)
2) Capture evidence
   - Exact command lines + timestamps
   - Stack traces, stdout/stderr logs
   - Generated run folder artifacts (or note which are missing)
3) Triage
   - Categorize failure: isolation/cwd, artifact validation, worker lifecycle, schema/JSON enforcement, tool sandbox/allowed roots

## Deliverables
- Short note: failing tests + first failure site (file:line)
- Minimal reproduction command for swarm repo-audit
- Pointers to any missing/incorrect artifacts

## Done when
- Failures reproduced deterministically (same failure twice)
- Root-cause category selected (with concrete evidence)

