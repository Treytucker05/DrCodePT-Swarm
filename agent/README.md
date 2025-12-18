# Trey's Agent (Codex + Ollama)

Unified single-terminal workflow that pairs Codex planning with local Ollama models for self-healing, learning, and tooling. Context is loaded at startup (credentials, playbooks, tools, recent tasks) and injected into every Codex conversation.

## Components
- **unified_cli.py** — interactive planning + post-run chat, YAML validation, execution, artifact discovery, spinners with timing, and context injection.
- **context_loader.py** — gathers saved credentials, playbooks, tools, recent tasks, and session info; feeds them to Codex via system context.
- **supervisor/supervisor.py** — executes plans, verifies outcomes, logs runs in `agent/runs/`, triggers self-heal/learning/session memory.
- **learning/ollama_client.py** — local LLM wrapper (`qwen2.5:7b-instruct` primary, `gemma3:4b` fallback) with retries and logging.
- **learning/self_healing_llm.py** — uses Ollama to analyze failures, write corrected plans, log attempts; retries only when confidence ≥ 0.7 (max 2).
- **learning/active_learning.py** — builds playbooks from successful runs.
- **learning/session_memory.py** — tracks recent context across tasks.
- **tools/** — execution adapters, including **code_review** (Ollama) and **research** (multi-source + summarize).
- **prompts/** — system/interactive/post-exec prompts for Codex conversations.
- **launchers/TREYS_AGENT.bat** — start the unified flow from anywhere.

## Ollama setup
- Service: `http://127.0.0.1:11434`
- Models: `qwen2.5:7b-instruct` (primary), `gemma3:4b` (fallback)
- Logs: `agent/logging/ollama_calls.log`
- Endpoint: `POST /api/generate {"model": "...", "prompt": "...", "stream": false}` (30s timeout, 3 retries)

## Workflow
1. Run `launchers\TREYS_AGENT.bat`.
2. Enter a goal; Codex asks 2–4 clarifying questions (with context awareness: credentials, playbooks, tools).
3. Codex generates YAML; CLI shows the plan plus a plain-English summary. Approve with `y` or edit in Notepad.
4. Execution (`python -m agent.supervisor.supervisor temp_plan.yaml`) with live status tags (spinners labeled “Planning”, “Post-run”, `[EXEC] Running plan...`).
5. Post-run Codex chat: summarizes results, lists artifacts, offers actions (open/run files, show code, explain, improve, new task). Improvements feed into the next goal automatically.
6. Runs stored under `agent/runs/<timestamp>_<task_id>/` with `summary.md`, `events.jsonl`, evidence, self_heal, patterns.

## Context awareness
- Saved credentials: detected from `agent/memory/credentials.json`, `agent/memory/site_playbooks`, and `agent/browser_state`.
- Playbooks: discovered from `agent/learning/playbooks/index.json`.
- Recent tasks: from `agent/tasks/executed_plan_*.yaml`.
- Session info: latest session in `agent/sessions`.
- All of the above are injected into Codex via `system_context.txt` + `context_loader.py`.

## Available tools
browser, shell, python, fs, api, desktop, screen_recorder, vision, notify, **code_review**, **research**.

## Testing
- Quick Ollama ping:  
  `python - <<'PY'\nimport requests\nprint(requests.post('http://127.0.0.1:11434/api/generate', json={'model':'qwen2.5:7b-instruct','prompt':'ping','stream':False}, timeout=15).json())\nPY`
- Full smoke: `python agent/test_system.py` (Ollama, Codex CLI, calculator plan, self-heal attempt).
- Manual: `launchers\TREYS_AGENT.bat` then run a goal (e.g., “Create a Python calculator program”).

## Troubleshooting
- Codex errors: spinner will print `[codex error …]`; ensure `codex --version` works in this repo.
- Ollama unreachable: check service/model pulls (`ollama pull qwen2.5:7b-instruct`, `ollama pull gemma3:4b`).
- Self-heal skipped: confidence < 0.7 or 2 attempts used; see `runs/.../healing_log.jsonl`.
- Artifacts missing: inspect `agent/runs/<timestamp>_<task_id>/output` and `events.jsonl`.

## Known gaps
- Self-heal quality is bounded by local models.
- Research tool uses basic HTTP fetch; some sites may block.
- Playbook reuse is heuristic; review before critical use.
