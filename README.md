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
- Credentials for logins should live in the encrypted credential store under `agent/memory/credential_store.json`.
  - Generate an encryption key with: `python - <<'PY'\nfrom cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\nPY`
  - Export it as `AGENT_CREDENTIAL_KEY` (preferred) or be ready to enter it interactively; do **not** write the key to disk.
  - Save site credentials via `from agent.memory.credentials import save_credential; save_credential("blackboard", "user", "pass")`.
  - Browser tasks can set `login_site: <site>` to automatically build login steps from the site playbook and stored credentials.

Yahoo Mail spam cleanup
- Store your Yahoo login once: `from agent.memory.credentials import save_credential; save_credential("yahoo", "you@example.com", "app_or_account_password")`.
- Run the deterministic task: `python -m agent.supervisor.supervisor agent/tasks/yahoo_clear_spam.yaml`.
- The task uses the `agent/memory/site_playbooks/yahoo.yaml` login flow (username step, then password step) and then empties the Spam folder via the "Empty Spam" control. Update the playbook selectors if your layout differs.

Menu entry point
- `python main.py` launches the terminal menu (run tasks, create tasks, view runs/failures/playbooks, etc.).
