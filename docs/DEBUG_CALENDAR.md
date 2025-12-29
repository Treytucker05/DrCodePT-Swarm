# DEBUG_CALENDAR.md

## Repro Steps
1. Launch the interactive CLI (example: `python -m agent --interactive`).
2. Enter: `Check my google calendar and tell me what I have tomorrow`.
3. Observe: Codex auth mismatch, OpenRouter fallback, plan tries to open Google Cloud Console, browser UI automation fails, then action parser throws "No JSON found".

## Failing Control Flow (Before Fix)
- `agent/cli.py` -> `_run_learning_agent()` -> `LearningAgent.run()`
- `_get_llm()` -> `CodexCliClient.reason_json()` -> auth error ("Codex CLI is not authenticated")
- `_call_llm_json()` falls back to `OpenRouterClient.reason_json()`
- `_build_plan_with_llm()` returns steps that include `open_browser` and `vision_guided`
- `_execute_plan()` -> `_open_browser()` -> `HybridExecutor.run_task()`
- `HybridExecutor.decide_next_action()` uses UIA for browser, UIA returns only top-level pane
- `_parse_action_response()` receives non-JSON text -> "No JSON found"

## Minimal Fix Set
1. Provider/auth handling
   - Use the same Codex CLI invocation for auth checks as runtime calls.
   - Prefer OpenRouter when configured; disable Codex for a run if auth fails.
   - Log provider/model per LLM call.
2. JSON enforcement
   - Validate LLM JSON with strict Pydantic models.
   - Add repair retries with "Return ONLY valid JSON matching this schema. No prose."
   - Return structured error actions instead of crashing on parse failures.
3. Calendar path
   - Implement Google Calendar skill using official API client + OAuth.
   - If credentials.json missing, print setup guide and stop (no UI automation).
   - Map "check my google calendar ... tomorrow" to `calendar.list_events` with local-time tomorrow range.
4. Plan generation
   - Use `plan_type=SETUP_GUIDE` for missing auth; do not open Google Cloud Console.
   - Skip UI automation for setup guides.

## Assumptions
- User has (or will create) a Google Cloud OAuth Desktop client and can save `credentials.json`.
- OAuth flow is allowed to open the system browser.
- Default credentials path: `~/.drcodept_swarm/google_calendar/credentials.json`.
