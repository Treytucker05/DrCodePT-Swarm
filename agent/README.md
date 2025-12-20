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

Add `--unsafe-mode` only if you explicitly want to enable destructive actions (writes outside the run workspace, shell commands, etc.).
LLM inference uses `codex exec` under the hood (with `--dangerously-bypass-approvals-and-sandbox` + `--search`) and always requests structured JSON outputs via `--output-schema`.

## Key modules
- `agent/run.py` - CLI entrypoint.
- `agent/autonomous/runner.py` - orchestrator loop + stop conditions + tracing.
- `agent/autonomous/tools/registry.py` - tool registry (safe-by-default).
- `agent/autonomous/memory/sqlite_store.py` - long-term memory store.
- `agent/llm/codex_cli_client.py` - Codex CLI-backed inference (no API keys).
- `agent/llm/schemas/` - JSON Schemas for structured outputs.

## Legacy
The older YAML supervisor and interactive launcher scripts remain in this package.

- Run a YAML task: `python -m agent.supervisor.supervisor agent/tasks/example_browser_task.yaml --unsafe-mode`
- Generate a YAML plan: `python agent/agent_planner.py "your goal here" > agent/temp_plan.yaml`
