# Blackboard Scraper — Status Update

Date: 2025-11-12
Repo: C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm

## Completed / Fixed
- Course discovery
  - Added scroll preload in `get_courses()` to force lazy cards to load (PROGRAMS\blackboard-agent\handlers\blackboard_handler.py:192).
  - Relaxed title selector; added anchor discovery and click-through fallback to derive course outline URLs (same file).
- Due-date extraction
  - Converted folder expansion to BFS over any `button[id][aria-controls]` toggles, using `execute_async_script` and re-queuing newly visible toggles (PROGRAMS\blackboard-agent\handlers\blackboard_handler.py:~470+).
  - Auto-click common "Show more/Expand" buttons between passes to surface hidden content (same area).
  - Final page-text scan to capture additional date patterns that aren’t inside toggles.
  - Result: All nested modules expand; additional dates captured across courses.
- Utilities
  - `PROGRAMS\blackboard-agent\tmp_list_courses.py` — quick listing of discovered courses.
  - `PROGRAMS\blackboard-agent\interactive_track_courses.py` — assisted capture; you click courses, it records outline URLs to `COURSE_URLS.txt`.
  - `PROGRAMS\blackboard-agent\extract_course_urls.py` — attempts automated collection of course URLs with view toggles.
  - `PROGRAMS\blackboard-agent\extract_due_dates_from_list.py` — extracts due dates for URLs in `COURSE_URLS.txt`; also outputs normalized report `COURSE_DUE_DATES_NORMALIZED.txt` (deduped/standardized).

## Current Outputs
- Captured outline URLs: `PROGRAMS\blackboard-agent\COURSE_URLS.txt`
- Raw due dates per course: `PROGRAMS\blackboard-agent\COURSE_DUE_DATES.txt`
- Normalized due dates per course: `PROGRAMS\blackboard-agent\COURSE_DUE_DATES_NORMALIZED.txt`
- Scroll-fix smoke result: `TEST_RESULTS_SCROLL_FIX.txt`

Latest normalized counts (from 5 courses): 34 total
- Legal & Ethics: 7
- Lifespan Dev: 2
- Clinical Pathology: 9
- Anatomy: 11
- PT Exam Skills: 5

## Remaining / Next
- File download capability (missing)
  - Implement `download_file()` and `download_course_materials()` with Chrome download prefs and completion wait.
  - Add corresponding Claude tool(s) and compose with `FileManager`.
- Course view robustness
  - Programmatically toggle Courses view to "All Courses" / relevant term for consistent discovery.
  - Improve course code extraction (avoid duplicating the same code across multiple courses).
- Due-date completeness
  - Add explicit parsing of assignment/quiz list items outside folder toggles (we already added page-text scan; can add targeted DOM queries).
  - Normalize/merge duplicates across sections and timezones.
- Security
  - Remove hard-coded credential fallbacks in handler; rely only on env vars; rotate any committed secrets.

## How To Run
- Capture course URLs interactively:
  - `python PROGRAMS\blackboard-agent\interactive_track_courses.py`
  - Click each course; wait for idle auto-stop; see `COURSE_URLS.txt`.
- Extract due dates from saved list:
  - `python PROGRAMS\blackboard-agent\extract_due_dates_from_list.py`
  - Check `COURSE_DUE_DATES.txt` and `COURSE_DUE_DATES_NORMALIZED.txt`.

