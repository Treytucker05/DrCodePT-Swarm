# task-02 — Enforce isolation invariants (cwd/worktree/sandbox)

## Objective
Ensure swarm workers cannot escape sandbox/cwd and isolation is consistent across runs.

## Files in Scope
- agent/autonomous/isolation/*
- agent/autonomous/isolation.py (if used)
- agent/autonomous/security/filesystem_sandbox.py (if relevant)
- tests/test_swarm_cwd.py
- tests/test_swarm_isolation.py
- tests/test_worktree_isolation.py

## Constraints
- Minimal targeted changes only.
- No test weakening.

## Commands to Run
- python -m pytest -q tests/test_swarm_cwd.py -vv
- python -m pytest -q tests/test_swarm_isolation.py -vv
- python -m pytest -q tests/test_worktree_isolation.py -vv

## Acceptance Criteria
- All above tests pass consistently.
- Worker cwd and filesystem access are explicitly constrained.
