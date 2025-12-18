# DrCodePT-Swarm Overview (Trey's Agent)

This repo hosts Trey's Agent — a Codex + Ollama, self-healing, context-aware automation agent for Windows. Use the single terminal launcher for interactive planning, execution, and post-run guidance.

## Quick start
1) Install deps: `pip install -r requirements.txt` (Python 3.11+).  
2) Install Playwright browsers if needed: `npx -y playwright install chromium`.  
3) Ensure Ollama is running with models `qwen2.5:7b-instruct` (primary) and `gemma3:4b` (fallback).  
4) Launch the agent: `launchers\TREYS_AGENT.bat`.  
5) Follow the interactive prompts: Codex asks clarifying questions, shows the YAML plan, executes, then offers post-run options.

## Features
- Interactive Codex planning with clarifying Qs, YAML generation, and post-exec conversations.
- Local LLM (Ollama) for self-heal, pattern extraction, code review, research.
- Context loader surfaces saved credentials, playbooks, tools, recent tasks into every Codex turn.
- Supervisor executes YAML plans, logs runs, and can self-heal with confidence gating.
- Live status spinners/timing; artifacts surfaced after runs.

## Key paths
- `agent/unified_cli.py` — main CLI loop.  
- `agent/context_loader.py` — builds/prints context and injects it into Codex.  
- `agent/supervisor/supervisor.py` — executor with self-heal/learning/session memory.  
- `agent/learning/ollama_client.py` — Ollama bridge.  
- `agent/prompts/` — system/interactive/post-exec prompts.  
- `agent/runs/` — run artifacts (`summary.md`, `events.jsonl`, evidence, self_heal).  
- `agent/learning/playbooks/` — learned playbooks.  
- `agent/logs/conversations.log` — planning/post-run chat transcripts.

## Tools available
browser, shell, python, fs, api, desktop, screen_recorder, vision, notify, code_review, research.

## Testing
- Full smoke: `python agent/test_system.py` (checks Ollama + Codex + self-heal path).  
- Ollama ping: see agent/README.md.  
- Manual: run `launchers\TREYS_AGENT.bat` and try “Create a Python calculator program.”

## Troubleshooting
- Codex errors show as `[codex error …]`; ensure `codex --version` works in repo.  
- Ollama: confirm service and models; retry pulls if missing.  
- Self-heal skips if confidence < 0.7 or attempts exceeded; check `runs/.../healing_log.jsonl`.

## Legacy launchers
- Older two-terminal and Claude launchers remain, but the recommended path is `TREYS_AGENT.bat`.
