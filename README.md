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

## Execution defaults
- LLM calls use `codex exec` with `--dangerously-bypass-approvals-and-sandbox` and `--search` (mandatory flags for this repo); prompts enforce JSON-only structured outputs.
- Memory uses embeddings with FAISS acceleration when available (falls back gracefully if disabled).
- Built-in tools include `web_search`, `web_fetch` with HTML stripping, and `delegate_task` for sub-agent handoffs.

## Run artifacts and concurrency safety
- The agent no longer uses `os.chdir()` in concurrent code paths; all subprocesses run with explicit `cwd=` and absolute paths.
- Each run writes `trace.jsonl` and `result.json` in its run folder.
- Codex CLI stdout/stderr are captured into `stdout.log` and `stderr.log` when a run directory is available.
- Swarm runs store per-subagent artifacts under `runs/swarm/<run_id>/<subtask_id_*>/`.

## Concurrency & Execution Invariants
These are contractual guarantees (not suggestions):
- Threaded code paths MUST NOT mutate process-global state (cwd, env vars, event loops).
- Every subprocess call MUST pass an explicit `cwd`.
- Every agent/subagent run MUST emit structured artifacts (`trace.jsonl`, and `result.json` when present).
- Swarm correctness depends on artifacts, not terminal output.

## Key paths
- `agent/run.py` - autonomous agent CLI entrypoint.
- `agent/autonomous/` - orchestrator + planning + reflection + memory + tools.
- `agent/llm/codex_cli_client.py` - Codex CLI-backed inference (no API keys).
- `agent/llm/schemas/` - JSON Schemas passed to `codex exec --output-schema ...`.

## Dev checks
- Schema lint: `python scripts/check_codex_schemas.py`
- Concurrency guard: `rg -n "os\\.chdir\\(" agent/`

## Legacy
The older YAML supervisor and launcher scripts remain under `agent/` and `launchers/`.

- Run a YAML task: `python -m agent.supervisor.supervisor agent/tasks/example_browser_task.yaml`
- Generate a YAML plan (planner only): `python agent/agent_planner.py "your goal here" > agent/temp_plan.yaml`
