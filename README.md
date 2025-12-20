# DrCodePT-Swarm

Production-grade autonomous agent skeleton (Python) with a true closed-loop architecture:

Perception -> Reasoning/Planning -> Action/Execution -> Feedback -> Reflection -> Memory updates -> Re-plan until stop.

## Quick start
1) Install deps: `pip install -r requirements.txt` (Python 3.11+).  
2) Optional (Web/GUI): install Playwright browsers: `npx -y playwright install chromium`.  
3) Install + authenticate Codex CLI:
   - Verify: `codex --version`
   - Login: `codex login`
4) Run: `python -m agent.run --task "..."`  
5) Traces: `runs/autonomous/<run_id>/trace.jsonl` (printed at end)

No `OPENAI_API_KEY` is required; the agent uses your local Codex CLI login.

## Safety defaults
- Safe-by-default: destructive tools/actions are blocked unless you enable `--unsafe-mode`.
- LLM calls use `codex exec` with `--dangerously-bypass-approvals-and-sandbox` and `--search` (mandatory flags for this repo); prompts enforce JSON-only structured outputs.

## Key paths
- `agent/run.py` - autonomous agent CLI entrypoint.
- `agent/autonomous/` - orchestrator + planning + reflection + memory + tools.
- `agent/llm/codex_cli_client.py` - Codex CLI-backed inference (no API keys).
- `agent/llm/schemas/` - JSON Schemas passed to `codex exec --output-schema ...`.

## Dev checks
- Schema lint: `python scripts/check_codex_schemas.py`

## Legacy
The older YAML supervisor and launcher scripts remain under `agent/` and `launchers/`.

- Run a YAML task: `python -m agent.supervisor.supervisor agent/tasks/example_browser_task.yaml --unsafe-mode`
- Generate a YAML plan (planner only): `python agent/agent_planner.py "your goal here" > agent/temp_plan.yaml`
