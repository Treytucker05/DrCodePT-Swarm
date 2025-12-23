# Agent package

This repository contains an autonomous agent skeleton under `agent/autonomous/` with a closed-loop architecture:

Perception -> Planning -> Action -> Feedback -> Reflection -> Memory updates -> Re-plan until stop.

## Run
From the repo root:

`python -m agent.run --task "..."`  

Prereqs:
- `codex --version`
- `codex login`

No `OPENAI_API_KEY` is required; the agent uses your local Codex CLI login.
Codex access is provided through ChatGPT Pro, so `codex login` will prompt for your ChatGPT account instead of an API key.

LLM inference uses `codex exec` under the hood (with `--dangerously-bypass-approvals-and-sandbox` + `--search`) and always requests structured JSON outputs via `--output-schema`.

## Documentation map (source of truth)
This package README is a summary. For full documentation:
- `README.md` (repo root) - overview + entrypoint.
- `ARCHITECTURE.md` - how the system works.
- `ENHANCEMENT_SUMMARY.md` - feature inventory.
- `USAGE_EXAMPLES.md` - workflow examples.
- `TROUBLESHOOTING.md` - common issues.

## Codex operating rules (must read)
- `AGENTS.md` - operating constraints and workflow rules.
- `CONTINUITY.md` - the continuity ledger Codex must maintain.

## Key modules
- `agent/run.py` - CLI entrypoint.
- `agent/autonomous/runner.py` - orchestrator loop + stop conditions + tracing.
- `agent/autonomous/tools/registry.py` - tool registry.
- `agent/autonomous/memory/sqlite_store.py` - long-term memory store (embeddings + FAISS when available).
- `agent/llm/codex_cli_client.py` - Codex CLI-backed inference (no API keys).
- `agent/llm/schemas/` - JSON Schemas for structured outputs.

## Legacy
The older YAML supervisor and interactive launcher scripts remain in this package.

- Run a YAML task: `python -m agent.supervisor.supervisor agent/tasks/example_browser_task.yaml`
- Generate a YAML plan: `python agent/agent_planner.py "your goal here" > agent/temp_plan.yaml`
