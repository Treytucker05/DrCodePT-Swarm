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
Codex access is provided through ChatGPT Pro, so `codex login` will prompt for your ChatGPT account instead of an API key.

## Documentation map (source of truth)
This README is a high-level entrypoint. The authoritative docs live in:
- `START_HERE.md` - onboarding and first-run flow.
- `ARCHITECTURE.md` - how the system works end-to-end.
- `ENHANCEMENT_SUMMARY.md` - full feature inventory.
- `USAGE_EXAMPLES.md` - real workflows and patterns.
- `QUICK_REFERENCE.md` - command cheat sheet.
- `TROUBLESHOOTING.md` - common issues + fixes.
- `AGENT_SETUP_GUIDE.md` - environment setup and prerequisites.

## Codex operating rules (must read)
When Codex is working in this repo, these files are the required rules:
- `AGENTS.md` - operating constraints and workflow rules.
- `CONTINUITY.md` - the continuity ledger Codex must maintain.

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
- Concurrent execution paths (swarm/subagents) MUST pass an explicit `cwd` to subprocesses.
- Codex CLI subprocess calls always pass an explicit `cwd`.
- Every agent/subagent run MUST emit structured artifacts (`trace.jsonl`, and `result.json` when present).
- Swarm correctness depends on artifacts, not terminal output.
- Task execution uses the backend seam (LLMBackend.run). Internal helper calls may use CodexCliClient convenience methods directly.

## Execution profiles
Profiles tune budgets without ever disabling timeouts (all profiles remain finite):
- fast (default): bounded, quick, low-risk
- deep: higher budgets for staged repo reviews
- audit: maximum rigor with checkpoints, still finite

Use `--profile fast|deep|audit` on `python -m agent.run`. Swarm reads `SWARM_PROFILE`/`AUTO_PROFILE`/`AGENT_PROFILE`.
Swarm workers are non-interactive; if a question is required they return `interaction_required` instead of prompting.
Repo review tasks generate `repo_index.json` and `repo_map.json` artifacts to bound scanning.
Filesystem tools enforce safety gates using allowed roots; set `AUTO_FS_ALLOWED_ROOTS`/`SWARM_FS_ALLOWED_ROOTS` or `*_FS_ANYWHERE`.

## Key paths
- `agent/run.py` - autonomous agent CLI entrypoint.
- `agent/autonomous/` - orchestrator + planning + reflection + memory + tools.
- `agent/llm/codex_cli_client.py` - Codex CLI-backed inference (no API keys).
- `agent/llm/schemas/` - JSON Schemas passed to `codex exec --output-schema ...`.

## Dev checks
- Schema lint: `python scripts/check_codex_schemas.py`
- Concurrency guard: `rg -n "os\\.chdir\\(" agent/`

## Verification
- Swarm cwd smoke test: `tests/test_swarm_cwd.py` blocks `os.chdir`, asserts `subprocess.run` receives explicit `cwd`, and requires ≥2 calls with workers=2.
- Run tests: `python -m pytest -q`
- Static guard: `rg -n "os\\.chdir\\(" agent/`

## Pre-commit
1) Install: `python -m pip install pre-commit`
2) Enable: `pre-commit install`
3) Run on all files: `pre-commit run -a`

## CI
- GitHub Actions runs pytest + mypy on push/PR (see `.github/workflows/ci.yml`).

## Legacy
The older YAML supervisor and launcher scripts remain under `agent/` and `launchers/`.

- Run a YAML task: `python -m agent.supervisor.supervisor agent/tasks/example_browser_task.yaml`
- Generate a YAML plan (planner only): `python agent/agent_planner.py "your goal here" > agent/temp_plan.yaml`
