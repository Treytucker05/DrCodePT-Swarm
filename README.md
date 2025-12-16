DrCodePT Swarm (Autonomous, Keyless)
====================================

What it is
- Task-driven agent with deterministic Playwright browser steps (no LLM, no OpenAI key).
- Desktop control, screen recording, notifications, persistent memory, recorder/session capture.
- Handoff workflow when human input is needed (WAITING.yaml / CONTINUE.flag).

Install prerequisites
- Python 3.11+ on Windows.
- Playwright browsers: `playwright install chromium` (already present in ms-playwright cache).
- FFmpeg in PATH (required for screen recorder).
- Python deps: `pip install -r requirements.txt` (or the installed environment).

Doctor self-check
- From repo root: `python -m agent.doctor`
  - Verifies tool imports, Playwright launch, PyAutoGUI, ffmpeg, and required folders.

Run the sample deterministic browser task
- `python -m agent.supervisor.supervisor agent/tasks/test_browser_steps.yaml`
- Creates a run folder under `agent/runs/…` with events.jsonl, summary.md, and screenshot evidence.

Handoff flow
- When a tool returns `requires human input` (e.g., vision describe/find), supervisor writes `handoff/WAITING.yaml`.
- To resume: place an empty `handoff/CONTINUE.flag` (the WAITING file is removed and run continues).

No secrets / no keys
- OPENAI_API_KEY is not required; browser tool is deterministic; vision reasoning is escalated to handoff.
- If you need credentials, inject via environment variables and reference with `${ENV_VAR}` in tasks. Do not store secrets in YAML.

Menu entry point
- `python main.py` launches the terminal menu (run tasks, create tasks, view runs/failures/playbooks, etc.).
