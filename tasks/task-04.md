# task-04 — Reliability & retry semantics (resilience)

## Objective
Make swarm resilient to partial worker failure and ensure retries/failures are explicit and do not corrupt aggregation.

## Files in Scope
- agent/autonomous/runner.py
- agent/autonomous/task_orchestrator.py
- agent/modes/swarm.py (only if resilience logic is there)
- tests/test_swarm_resilience.py

## Constraints
- Do not add new features; only tighten correctness.
- No test weakening.

## Commands to Run
- python -m pytest -q tests/test_swarm_resilience.py -vv

## Acceptance Criteria
- Resilience test passes.
- Failure modes are explicit and aggregation remains valid.
