# Computer Use Audit

Date: 2025-11-12
Scope: PROGRAMS\blackboard-agent\computer_use\*.py

## What It Is
- Files reviewed: `computer_automation.py`, `microsoft_integration.py`, `file_manager.py`, `__init__.py`.
- Approach types:
  - Direct GUI control via `pyautogui` (`computer_automation.py`).
  - Windows UI Automation via `pywinauto` (`microsoft_integration.py`).
  - File system organization utilities (`file_manager.py`).
  - No “Claude Computer Use” (screen streaming) APIs are present. The agent uses Claude’s Tool Use API to call Python tools, not OS-level “Computer Use”.

### Module Details
- `computer_automation.py`
  - Purpose: Simple, direct automation of Microsoft To Do using `pyautogui` (Win key, type app name, click, type tasks).
  - Key functions: `add_tasks_to_microsoft_todo()`, `add_events_to_calendar()`.
  - Characteristics: Coordinate-based clicks, timing sleeps; no control discovery or verification; not suitable for precise UI flows.
  - Status: Broken. Contains an invalid print string (`print(f"[AUTOMATION] …" Added {len(tasks)} …)`) that would raise a syntax error on import. Not referenced anywhere by the agent.

- `microsoft_integration.py`
  - Purpose: Robust Microsoft To Do task creation using `pywinauto` (UIA backend). Includes retries, attach/launch logic, and basic verification.
  - Key functions: `microsoft_add_tasks()` (public), `_add_single_task()`, `_get_todo_window()`, `_find_todo_window()`.
  - Extras: SQLite-backed idempotency store (`OpStore`) to avoid duplicates; flexible selectors via `config/todo_selectors.json`.
  - Status: Functional with caveats. In testing, attachment can be flaky; sometimes falls back to “assumed success” (verification timeout). Integrated with the agent via Claude tools.

- `file_manager.py`
  - Purpose: Organize downloaded files into course/week folders; move files by type; helper utilities.
  - Key functions: `create_weekly_folder()`, `organize_downloads()`, `get_download_folder()`.
  - Status: Functional. Integrated with the agent via Claude tools.

## Integration With agent.py
- `agent.py` → `handlers/claude_handler.py` imports:
  - `from computer_use.file_manager import FileManager` (used)
  - `from computer_use.microsoft_integration import microsoft_add_tasks` (used)
- The tool definitions in `ClaudeHandler` expose `microsoft_add_tasks` and file management actions.
- `computer_automation.py` (pyautogui) is not imported or used by the agent.

## Can It Replace Selenium Scrolling?
- Short answer: No, not for Blackboard scraping.
- Reasons:
  - `pyautogui` can scroll the browser window by sending wheel/keys, but it cannot read structured page content. Without OCR/screen parsing (not implemented), it cannot extract due dates or navigate reliably.
  - `pywinauto` integration is tailored to the Microsoft To Do UWP app, not Chrome/Edge. It does not provide DOM-level access or robust control of web content.
  - Selenium (or Playwright) remains the right tool for DOM interaction, querying, and robust timing on Blackboard. Our recent fix to `get_due_dates()` (async JS) demonstrates the correct pattern.

## Pros/Cons vs. Selenium
- `pyautogui` (computer_automation.py)
  - Pros: Simple to script; no app-specific dependencies; can send scroll/keys.
  - Cons: Fragile to window focus, timing, screen resolution, and layout changes; no element discovery; cannot parse page data. Not suitable for Blackboard data extraction.

- `pywinauto` (microsoft_integration.py)
  - Pros: Element-based UI automation; resilient to some layout changes; can verify UI state; idempotent operations via SQLite.
  - Cons: UWP window detection can be flaky; not applicable to web pages/DOM; needs tuning/longer timeouts for reliability.

- Selenium (current Blackboard approach)
  - Pros: Full DOM access, selectors, JS execution, predictable waits; correct tool for structured scraping (courses, modules, due dates).
  - Cons: Requires driver/manager; occasional download/timeouts; site-specific selectors must be maintained.

## State Summary
- `computer_automation.py`: Broken (syntax error); not integrated. Safe to fix or remove to avoid confusion.
- `microsoft_integration.py`: Partially complete and functional; integrated; occasional flakiness.
- `file_manager.py`: Complete/functional; integrated.

## Recommendations
- Keep Selenium for Blackboard; expand selectors for folders and improve waits rather than switching to GUI-level automation.
- If broader OS-level control is desired, consider Playwright for the browser (auto-scrolling, robust waits) rather than `pyautogui`.
- Repair or remove `computer_automation.py` to prevent accidental import errors. Prefer the `pywinauto` path for To Do, or consider Microsoft Graph API for server-side reliability.
- For To Do reliability, increase timeouts and add explicit waits for the “Add a task” edit box; consider additional title/automation IDs from `todo_selectors.json`.

