# Trey's Agent (Codex + Ollama)

Unified single-terminal workflow that pairs Codex planning with local Ollama models for self‑healing, learning, and tooling.

## Components
- **unified_cli.py**: Prompts for a goal, asks Codex to draft YAML, lets you review/edit, then runs `python -m agent.supervisor.supervisor <plan>`.
- **supervisor/supervisor.py**: Executes plans, verifies outcomes, calls self‑healing, logs runs in `agent/runs/`.
- **learning/ollama_client.py**: Wrapper for `http://127.0.0.1:11434` (primary `qwen2.5:7b-instruct`, fallback `gemma3:4b`).
- **learning/self_healing_llm.py**: Uses Ollama to analyze failures, write corrected plans, and log attempts.
- **learning/active_learning.py**: Builds playbooks from successful runs.
- **learning/session_memory.py**: Tracks recent context across tasks.
- **tools/**: Execution adapters, now including `code_review` (Ollama-powered polishing) and `research` (multi-source gather + summarize).
- **launchers/TREYS_AGENT.bat**: Start the unified flow from anywhere.

## Ollama setup
- Service expected at `http://127.0.0.1:11434`.
- Models: `qwen2.5:7b-instruct` (primary), `gemma3:4b` (fallback). Logs at `agent/logging/ollama_calls.log`.
- API shape used: `POST /api/generate {"model": "...", "prompt": "...", "stream": false}` with retries and 30s timeout.

## Workflow
1. Run `launchers\TREYS_AGENT.bat`.
2. Enter a goal (e.g., “Create a Python calculator program”).
3. Codex drafts `temp_plan.yaml` (uses `planner_system_prompt.txt`).
4. Review/optionally edit (Notepad). Execute to hand off to supervisor.
5. Supervisor runs tools, verifies, logs to `runs/<timestamp>_<task_id>/`.
6. On success: patterns extracted via Ollama; playbook generation attempted.
7. On failure: self-healing tries up to 2 times; only auto-retries if confidence ≥ 0.7. Corrected plans stored under `runs/.../self_heal/`.

## Available tools (registry)
browser, shell, python, fs, api, desktop, screen_recorder, vision, notify, **code_review**, **research**.

## Testing
- Quick API check:  
  `python -c "import requests; print(requests.post('http://127.0.0.1:11434/api/generate', json={'model':'qwen2.5:7b-instruct','prompt':'ping','stream':False}).json())"`
- Full smoke: `python agent/test_system.py` (Ollama, Codex, calculator plan, self-heal attempt).
- Manual: `launchers\TREYS_AGENT.bat` then run the sample goal above.

## Troubleshooting
- Ollama not reachable → ensure service is running (`netstat` on 11434), restart Ollama app.
- Model missing → `ollama pull qwen2.5:7b-instruct`.
- Codex CLI errors → check `codex --version` and rerun inside repository root.
- Self-heal skipped → confidence < 0.7 or max 2 retries hit; see `runs/.../healing_log.jsonl`.

## Known gaps
- Self-healing quality depends on local models; complex plans may still need manual edits.
- Research tool uses lightweight HTTP fetching; some sites may block requests.
- Playbook generation is heuristic; review outputs before reuse.
