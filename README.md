DrCodePT-Swarm – Comprehensive Guide
====================================

Overview
- Autonomous, task-driven agent for Windows with Playwright desktop/browser automation, file/system tools, and structured YAML plans.
- Supports Codex (one-terminal or two-terminal flow) and Claude-based planner (advanced launcher).
- 10/10 upgrade adds self-healing, active learning (playbooks), and session memory.
- Keyless by default; credentials stored encrypted in `agent/memory/credential_store.json`.

Prerequisites
- Windows, Python 3.11+.
- Playwright browsers installed (`npx -y playwright install chromium`).
- FFmpeg on PATH (for screen recording if used).
- Python deps: `pip install -r requirements.txt`.

Launchers (pick one)
- Single terminal (Codex): `launchers\run_agent.bat` – prompts for goal, runs Codex exec → supervisor.
- Claude advanced planner: `launchers\run_agent_advanced.bat` – uses `CLAUDE_API_KEY` and optional `CLAUDE_MODEL`.
- Two-terminal flow: `START_TWO_TERMINAL_AGENT.bat`
  - Terminal 1: `terminal1_planner.bat` generates `agent\temp_plan.yaml`.
  - Terminal 2: `terminal2_executor.bat` executes that plan.

Planner prompt
- File: `agent\planner_system_prompt.txt` (backed up as `planner_system_prompt_backup.txt`).
- Includes browser-action guidance (“BROWSER TASK ACTIONS”) from Browser Automation Fix package.

Supervisor and learning
- Main supervisor: `agent\supervisor\supervisor.py` (enhanced version installed; backup at `supervisor_backup.py`).
- Features: self-healing (writes `self_heal_payload_*.yaml`), active learning (writes playbooks), session memory.
- Playbooks directory: `agent\learning\playbooks\`
- Sessions directory: `agent\sessions\`

Credential storage
- Encryption key via `AGENT_CREDENTIAL_KEY` env var (Fernet key). Do not store the key on disk.
- Save a credential: `from agent.memory.credentials import save_credential; save_credential("yahoo", "user", "app_password")`
- Browser tasks can set `login_site: <site>` to pull stored creds and site playbook (e.g., `agent/memory/site_playbooks/yahoo.yaml`).

Running tasks directly (deterministic)
- Example: `python -m agent.supervisor.supervisor agent/tasks/test_browser_steps.yaml`
- Yahoo spam cleanup: `python -m agent.supervisor.supervisor agent/tasks/yahoo_clear_spam.yaml`

Typical workflow (Codex one-terminal)
1) Run `launchers\run_agent.bat`.
2) Enter a goal (e.g., “Create hello.py that prints Hello Agent”).
3) Plan is generated and piped to supervisor; output and logs go to `agent\runs\TIMESTAMP_task-...`.

Typical workflow (two-terminal)
1) Run `START_TWO_TERMINAL_AGENT.bat`.
2) Terminal 1: enter goal; YAML saved to `agent\temp_plan.yaml`.
3) Terminal 2: press Enter to execute; run artifacts in `agent\runs\...`.

Artifacts and logs
- Runs: `agent\runs\TIMESTAMP_task-*` with `events.jsonl`, `summary.md`, `evidence/` (screenshots/HTML), `self_heal/`.
- Executed plans archive: `agent\tasks\executed_plan_*.yaml`.
- Playbooks (learned): `agent\learning\playbooks\`.
- Session data: `agent\sessions\`.

Self-healing usage
- On failure, supervisor writes `self_heal_payload_*.yaml` under the run’s `self_heal/`.
- To retry: feed that payload to the planner (Terminal 1) to generate a corrected plan, then re-run in Terminal 2.

Browser automation notes
- Uses Playwright MCP. Make sure it’s running (launchers start it automatically).
- Google search often triggers CAPTCHA; prefer DuckDuckGo/Bing for unattended tests.
- Add verifiers (e.g., `output_contains`, `file_exists`, `screenshot_saved`) to avoid false “success.”

Maintenance / cleanup
- Temp extraction dirs can be removed; runs accumulate under `agent\runs\`.
- Backups present: `agent\supervisor\supervisor_backup.py`, `agent\planner_system_prompt_backup.txt`.

Doctor self-check
- `python -m agent.doctor` to verify imports, Playwright launch, ffmpeg, required folders.

Menu entry (legacy)
- `python main.py` opens the terminal menu for browsing tasks, runs, failures, playbooks.

Quick smoke tests
- FS: “Create a text file notes.txt with ‘test 123’.”
- Python: “Create hello.py that prints Hello Agent.”
- Browser (captcha-safe): “Search DuckDuckGo for Python programming and take a screenshot.”

If something fails
- Check the run folder’s `summary.md` and `events.jsonl`.
- Look for `self_heal_payload_*.yaml` to repair the plan.
