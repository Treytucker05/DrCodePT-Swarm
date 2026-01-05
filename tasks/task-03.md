# task-03 — Harden artifact validation + QA determinism

## Objective
Ensure invalid/partial artifacts are rejected early and QA output ordering is deterministic.

## Files in Scope
- agent/autonomous/qa/*
- agent/autonomous/manifest.py (if needed)
- agent/modes/swarm.py (only if artifacts are emitted there)
- tests/test_qa.py
- tests/test_artifact_validator.py

## Constraints
- Minimal changes.
- No schema/validator loosening unless tests demand it.

## Commands to Run
- python -m pytest -q tests/test_artifact_validator.py -vv
- python -m pytest -q tests/test_qa.py -vv

## Acceptance Criteria
- Validators reliably detect missing/invalid artifacts.
- QA summary output is deterministic.
