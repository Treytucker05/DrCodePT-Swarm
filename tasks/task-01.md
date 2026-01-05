# Task 01 — Swarm artifacts contract (workers + aggregation)

## Goal
Ensure every swarm worker run emits **required structured artifacts** and the aggregator validates/merges them correctly.

## Likely touchpoints
- `agent/modes/swarm.py` (worker execution + aggregation)
- `agent/autonomous/qa.py` (artifact validation)
- `agent/autonomous/manifest.py` (run metadata)
- `agent/autonomous/models.py` (result models)
- `tests/test_swarm_aggregation.py`, `tests/test_qa*.py`

## Steps
1) Enumerate required artifacts for swarm repo audits (per docs/tests)
2) Verify worker run directory structure + filenames
3) Fix missing/incorrect artifact writes (trace/result/manifest)
4) Fix aggregation logic (merge ordering, partial failures, retries)

## Done when
- Swarm worker artifacts pass validation (`validate_artifacts`) for a repo-audit task
- Aggregated swarm result is complete and deterministic

