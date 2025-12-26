# Continuity Ledger
- Goal (incl. success criteria): Add collaborative planning mode (Q&A, plan, approval) with LLM schema, CLI routing, and help text in DrCodePT-Swarm.
- Constraints/Assumptions: Follow AGENTS.md (minimal scoped changes, safe-by-default, run pytest -q for relevant changes). Keep ASCII. approval_policy=never. Do not touch unrelated files.
- Key decisions: None yet.
- State:
  - Done: Read AGENTS.md and CONTINUITY.md; identified target files and requirements.
  - Now: Implement collaborative planning module + schema and integrate into CLI.
  - Next: Update help text and verify behavior path; consider tests if needed.
- Open questions (UNCONFIRMED if needed): None.
- Working set (files/ids/commands): agent/modes/collaborative.py; agent/llm/schemas/collaborative_plan.json; agent/treys_agent.py
