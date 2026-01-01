# DrCodePT-Swarm - Agent Alignment Plan (Implementation Tracks)

This file is an implementation plan that must align to `AGENT_BEHAVIOR.md`.
Source of truth for behavior: `AGENT_BEHAVIOR.md` (repo root). If anything conflicts, update the behavior spec first.


## Core Goal
Enable a single, unified assistant that:
- Executes simple tasks immediately.
- For complex tasks: asks the minimum clarifying questions, researches if needed, plans, executes, fixes errors, and completes the task.
- Verifies results, scores accuracy, and retries if below threshold.
- Learns from successes and failures (short-term + long-term memory).

## Non-Negotiable Behaviors
1) Unified loop (no visible modes)
   Observe -> Think -> (Optional Research) -> Plan -> Execute -> Recover -> Verify -> Score -> Answer.

2) Simple tasks execute fast
   - If low risk and fully specified, act immediately without extra questions.

3) Complex tasks ask only what's missing
   - Ask for missing credentials, permissions, ambiguous requirements.

4) Error recovery and self-healing
   - On error: stop -> diagnose -> research -> attempt fix -> log lesson -> resume.
   - Do not abandon the original plan unless the fix fails.

5) Verification + scoring gate
   - Always verify outputs when possible.
   - Score 0-100. If below threshold, retry or improve until threshold or a safe stop.

6) Memory and learning
   - Short-term: current run context + error traces.
   - Long-term: saved lessons, procedures, and user preferences.

7) Credential handling
   - Secure storage for passwords/tokens.
   - Ask for 2FA codes only when needed.

8) Multi-agent support
   - Spawn helpers for parallel research or subtasks only when beneficial.
   - Respect a token/cost budget.

9) UI automation must be reasoned (no scripted flows)
   - Observe -> Think -> Act -> Verify -> Recover at each step.
   - If the UI deviates (wrong page/dialog/download blocked), the agent must
     reason about the current state and choose corrective actions.
   - Do not use fixed click scripts or rigid step lists for OAuth/setup flows.

10) Research must be real and authoritative
   - Use web_search -> web_fetch; do not rely on snippets alone.
   - Prefer official docs and vendor console pages.
   - Produce steps + success checks grounded in sources.

11) Human correction channel (when stuck)
   - If confidence drops or progress stalls, pause and ask for a direct user
     instruction (click/type/open URL).
   - Store the correction as a reusable UI lesson.
   - Do not require manual config toggles for normal operation.
   - Prefer auto-detection of state (current project, login status, downloads).

## Implementation Tracks

### Track 1 - Unified Behavior (Highest Priority)
- Enforce the single loop in the runtime path.
- Remove or bypass visible mode routing.
- Ensure fast-path for trivial tasks.

### Track 2 - Error Recovery + Memory
- Persist error signatures + fixes.
- Auto-retry safe failures.
- Resume original plan after fixes.

### Track 3 - Verification + Scoring
- Add explicit verification for tool results.
- Score and retry below threshold.

### Track 4 - Credential Management
- Secure storage for passwords/tokens.
- OAuth flows for Google Calendar/Tasks.
- OAuth/UI setup must use the reasoned UI loop (no scripted click flows).

### Track 5 - Multi-Agent Coordination
- Allow delegate workers.
- Control max workers + cost limits.

### Track 6 - Research Quality + Human Correction
- Fetch and summarize authoritative sources (no snippet-only plans).
- Build step-by-step plans with verification checkpoints.
- Add a user correction prompt when stuck; store UI lessons.

## Success Criteria (Examples)
- Simple task: "Create test.txt with ‘hello world' and open it."
  - Completes in < 10 seconds.
  - File exists, content verified, opens successfully.

- Complex task: "Check Google Calendar for tomorrow's clients."
  - If not configured, agent guides OAuth setup and stores credentials.
  - Uses reasoned UI loop (observe/think/act) to handle UI variance.
  - Research/plan uses authoritative sources + explicit verification steps.
  - Returns correct events with times.

## Anti-Drift Rule
- Any new feature must map to one of the Tracks above.
- If it doesn't, it's out of scope.
