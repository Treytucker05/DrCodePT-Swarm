# Blackboard File Download Capability — Audit

Date: 2025-11-12
Workspace: C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm

## Summary
- No file download function (e.g., `download_file`) is implemented in the Blackboard handler.
- Blackboard automation currently supports: login, course listing, announcements, modules, and due-date extraction.
- Agent integration exists for read-only Blackboard operations (get courses/announcements/modules/due dates) and for download organization, but not for initiating downloads from Blackboard.
- A prior test report indicates Blackboard scraping works for login/courses/announcements/modules and that due-date extraction has been patched to work better. Actual file download from Blackboard is currently missing.

---

## 1) What Exists in `blackboard_handler.py`
- File: `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:1`
- Implemented methods:
  - `login()` — starts Chrome via Selenium, navigates, submits credentials, and detects login state.
  - `get_courses()` — scrapes the Courses page, captures course name/code/status/URL.
    - Ref: `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:153`
  - `get_announcements(course_url)` — navigates to course announcements and scrapes rows.
    - Ref: `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:266`
  - `get_modules(course_url)` — navigates to course outline, finds content “modules” and extracts title/description and, if present, a content link URL.
    - Ref: `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:355`
  - `get_due_dates(course_url)` — expands folder sections via JS and regex-parses due date text.
    - Ref: `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:449`
- Not implemented:
  - No `download_file(...)`, `download_files(...)`, or equivalent. A “file downloads” claim appears in the header docstring, but there is no code to initiate or manage downloads.
  - A download directory is not configured in Chrome options; no logic to click file links and wait for completion.

Practical implication: The handler can discover modules and sometimes link URLs, but cannot download attachments/materials itself.

---

## 2) Agent Integration Check
- Agent entry: `PROGRAMS/blackboard-agent/agent.py:1`
- Claude tool orchestration: `PROGRAMS/blackboard-agent/handlers/claude_handler.py:1`
  - Tools defined for read-only Blackboard actions:
    - `blackboard_get_courses` → `BlackboardHandler.get_courses()`
      - Ref: `PROGRAMS/blackboard-agent/handlers/claude_handler.py:159`, `...:359-364`
    - `blackboard_get_announcements` → `get_announcements()`
      - Ref: `PROGRAMS/blackboard-agent/handlers/claude_handler.py:168`, `...:366-372`
    - `blackboard_get_modules` → `get_modules()`
      - Ref: `PROGRAMS/blackboard-agent/handlers/claude_handler.py:182`, `...:374-380`
    - `blackboard_get_due_dates` → `get_due_dates()`
      - Ref: `PROGRAMS/blackboard-agent/handlers/claude_handler.py:196`, `...:382-391`
  - File organization tools (post-download organization):
    - `file_organize_downloads`, `file_create_course_folder`
      - Ref: `PROGRAMS/blackboard-agent/handlers/claude_handler.py:210`, `...:391-403`
      - Backed by: `PROGRAMS/blackboard-agent/computer_use/file_manager.py:1`
- Missing integration:
  - No Claude tool exists to download Blackboard materials (no `blackboard_download_files`, etc.).

Conclusion: Agent can read Blackboard data and organize files already present in Downloads, but cannot trigger file downloads from Blackboard.

---

## 3) Test (If Exists)
- Download function: Not present → cannot test download.
- Login → get_courses: Supported by handler and previously exercised in local test scripts.
  - Temp harnesses present: `tmp_bb_test.py`, `tmp_bb_test2.py` (login, courses, announcements, modules, due dates).
  - Prior artifact: `BLACKBOARD_AGENT_TEST_REPORT.md:1` documents successful login, 3 courses, announcements/modules scraped, and later due-date extraction improvements.
- Credentials: `PROGRAMS/blackboard-agent/.env` contains real Blackboard credentials and an API key. For security and policy reasons, no live login was executed as part of this audit.

Observed state from code and prior report:
- Login/courses/announcements/modules: Working per previous runs.
- Due dates: The current code uses `driver.execute_async_script(...)` and imports `sys`, addressing the earlier issues cited in the report.
- Downloads: Not implemented; no evidence of a working or partial download flow.

---

## 4) Can It Be Called by the Agent?
- Read-only Blackboard operations: Yes, via Claude tools listed above.
- File download from Blackboard: No; no tool or handler method exists to initiate downloads.
- File organization after manual downloads: Yes, `file_organize_downloads` works with `FileManager` to sort PDFs/PPTs/docs/etc.

---

## 5) Gaps
- Missing download capability in `BlackboardHandler` (no method to click or programmatically fetch attachments/materials).
- Chrome driver options do not configure download behavior (no default directory, no “auto-open PDF externally”, no automatic download handling).
- No Claude tool surface for “download course materials”.
- Security: `BlackboardHandler.__init__` falls back to hard-coded credentials; `.env` contains secrets inside the repo.

Refs:
- `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py:1` (docstring claims “file downloads”) — but no download code present.
- `PROGRAMS/blackboard-agent/.env:1` (contains secrets; should be removed from VCS and rotated).

---

## 6) Next Steps (Implementation Plan)
1) Add download support in `BlackboardHandler`:
   - Configure Chrome options for downloads:
     - `download.default_directory` to a known folder (e.g., a temp or course/week folder).
     - `download.prompt_for_download = False`, `safebrowsing.enabled = True`, `plugins.always_open_pdf_externally = True`.
   - Implement `download_file(file_url: str, dest_dir: str) -> dict` that:
     - Navigates or clicks the file link.
     - Waits for the partial `.crdownload` to disappear.
     - Returns the final file path and metadata.
   - Implement `download_course_materials(course_url: str, filters: dict) -> list[dict]` that:
     - Uses `get_modules()` to enumerate content items with links.
     - Applies filters (e.g., by week/folder/title/extension).
     - Initiates downloads and returns a list of saved files.
   - Alternative approach: use `requests` with Selenium session cookies for direct HTTP GET on file links (more reliable vs. UI clicks, if URLs are stable and not JS-gated).

2) Expose downloads to the agent:
   - Add Claude tools in `claude_handler.py`:
     - `blackboard_download_files` with inputs: `course_url`, optional `folder_or_keyword`, `file_types`, `max_files`, `dest`.
   - Compose with `FileManager`:
     - Create course/week folder (`file_create_course_folder`).
     - After each download, call `file_organize_downloads` to sort by type.

3) Reliability and UX:
   - Prefer Selenium Manager over `webdriver-manager` where possible.
   - Replace `time.sleep` with `WebDriverWait` for navigation and download completion.
   - Add robust logging (start/finish per file) and error capture.

4) Security Hardening:
   - Remove hard-coded credential fallbacks in `BlackboardHandler.__init__`.
   - Move secrets out of the repo; rely on environment variables or OS keyring.
   - Rotate any committed credentials/API keys.

5) Testing:
   - Add a non-interactive smoke test (credentials via environment):
     - login → get_courses → get_modules → download one small file into a temp folder → verify file exists and is non-empty.
   - Add a one-shot CLI entry (e.g., `python -m programs.blackboard-agent.download_once --course "Clinical Pathology" --types pdf pptx --max 2`).

---

## 7) Bottom Line
- What exists: Scraping for courses, announcements, modules, due dates. No download function.
- Does it work? Yes for scraping (per prior report and code); downloads are missing, so cannot work yet.
- Can it be called by the agent? Read-only Blackboard tools and file organization are available; no download tool yet.
- Next steps: Implement download functions in the handler, wire new Claude tools, configure Chrome download preferences, and add a small E2E test path.

---

## Update — Scroll + BFS Fix Applied (Nov 12)
- Handler improvements in `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py`:
  - `get_courses()` now pre-scrolls to load all cards and uses broader selectors plus a fallback click-through to derive course URLs.
  - `get_due_dates()` now performs a full breadth-first expansion of nested toggles, clicks common “show more/expand” buttons, and finishes with a page-text scan for additional due-date patterns.
- New helper scripts added in `PROGRAMS/blackboard-agent/`:
  - `tmp_list_courses.py` (quick course listing)
  - `extract_course_urls.py` (collect outline URLs)
  - `interactive_track_courses.py` (you click courses; it records outline URLs)
  - `extract_due_dates_from_list.py` (visit saved URLs, extract due dates; outputs normalized and raw reports)
- Results (latest normalized extraction from 5 captured course URLs):
  - Legal & Ethics: 7 | Lifespan Dev: 2 | Clinical Pathology: 9 | Anatomy: 11 | PT Exam Skills: 5 | Total: 34
- Download capability status: unchanged — still not implemented; recommendations in sections 6 and 7 remain the same.
