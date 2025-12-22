# Continuity Ledger

- Goal (incl. success criteria): Fix `swarm` mode crash in `treys_agent.py` caused by missing exports in `agent.autonomous.isolation` / `agent.autonomous.qa`, and help user with a high-efficiency plan-execution approach.
- Constraints/Assumptions: Follow AGENTS.md (minimal scoped changes; keep ASCII; run relevant pytest). approval_policy=never.
- Key decisions: Export the helpers expected by `agent.modes.swarm` from `agent/autonomous/isolation/__init__.py` and `agent/autonomous/qa/__init__.py`.
- State:
  - Done: Phase 0.5 Smart Conversational Startup Flow implemented and committed.
  - Now: Swarm imports fixed and verified locally; pending commit.
  - Next: Commit the fix, then re-run `treys_agent.py` and choose `swarm` again.
- Open questions (UNCONFIRMED if needed): None.
- Working set (files/ids/commands): agent/autonomous/isolation/__init__.py; agent/autonomous/qa/__init__.py; tests/test_isolation_exports.py; agent/modes/swarm.py; `python -c "from agent.modes.swarm import mode_swarm; print('ok')"`; `PYTHONIOENCODING=utf-8`
