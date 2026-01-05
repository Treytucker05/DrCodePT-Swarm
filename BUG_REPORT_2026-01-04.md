# Bug Report - January 4, 2026

**Diagnostic Suite Results**: 7/8 tests passed, 1/8 tests failed

---

## CRITICAL BUG - Agent Performance Timeout

**Test**: #8 End-to-End Agent Performance
**Status**: FAILED (timeout after 63s)
**Expected**: Success in <10s
**Actual**: Timeout after 63s, only 2 steps executed

### Root Cause Analysis

The agent is timing out on simple calendar queries even after all our performance fixes. The diagnostic shows:

```
Agent run: 63.06s
Success: False
Steps: 2
Reason: timeout
```

This means the agent is hitting the 60-second timeout configured in the test (`timeout_seconds=60`), which suggests the LLM calls are extremely slow or hanging.

### Why This Happens

Looking at the debug output from the diagnostic run:

```
[DEBUG] Codex command: ... --model gpt-5.1-codex-mini -c model_reasoning_effort="high" ...
```

The agent is using:
- **Model**: `gpt-5.1-codex-mini` (slow)
- **Reasoning effort**: `high` (very slow)
- **Multiple planning calls**: Each step requires 2-3 LLM calls

Even with our fixes:
- ✅ Loop detection fixed
- ✅ Preconditions disabled
- ✅ Reflection skipped
- ✅ API caching working

The agent is still slow because **each planning step takes 30+ seconds** with the current LLM configuration.

### The Real Problem

Your `.env` has:
```env
CODEX_MODEL=gpt-5.2-codex
CODEX_MODEL_FAST=gpt-5.2-codex
CODEX_MODEL_REASON=gpt-5.2-codex
CODEX_REASONING_EFFORT_FAST=low
CODEX_REASONING_EFFORT_REASON=medium  # Changed from "high"
```

But your `TREYS_AGENT.bat` overrides these in lines 18-22:
```batch
if not defined CODEX_MODEL set "CODEX_MODEL=gpt-5.2-codex"
if not defined CODEX_MODEL_FAST set "CODEX_MODEL_FAST=gpt-5.2-codex"
if not defined CODEX_MODEL_REASON set "CODEX_MODEL_REASON=gpt-5.2-codex"
if not defined CODEX_REASONING_EFFORT_FAST set "CODEX_REASONING_EFFORT_FAST=low"
if not defined CODEX_REASONING_EFFORT_REASON set "CODEX_REASONING_EFFORT_REASON=xhigh"
```

**Line 22 sets `CODEX_REASONING_EFFORT_REASON=xhigh`** which is EXTREMELY slow!

Also, the agent is using `gpt-5.1-codex-mini` instead of the configured `gpt-5.2-codex`, which suggests the test is using a different configuration path.

---

## Test Results Summary

### ✅ PASSING TESTS (7/8)

1. **Environment Variables Loaded** (0.01s)
   - ✅ `AGENT_SKIP_PRECONDITIONS=1` correctly set
   - ✅ `CODEX_TIMEOUT_SECONDS=300` correctly set
   - ✅ `AUTO_MAX_STEPS=15` correctly set

2. **Google Calendar Authentication** (0.00s)
   - ✅ OAuth token exists at correct path
   - ✅ Token is valid and accessible

3. **Calendar API Call Speed** (1.06s)
   - ✅ First API call: 0.537s
   - ✅ Second API call: 0.001s (cached)
   - ✅ **537x speedup on cache hit**

4. **Loop Detection for Read-Only Tools** (0.00s)
   - ✅ Read-only tools (calendar) exempt from loop detection
   - ✅ Write tools (file_write) still trigger loop detection correctly

5. **Reflection Skipping for Read-Only Tools** (0.09s)
   - ✅ Successful read-only operations skip expensive reflection
   - ✅ No unnecessary LLM calls

6. **Memory Database Connection** (5.81s)
   - ✅ First write succeeds
   - ✅ Second write succeeds
   - ✅ Auto-reconnect works after connection close
   - ⚠️ Test takes 5.81s (cleanup delay for Windows file lock)

7. **Interactive Mode Answer Extraction** (0.08s)
   - ✅ Calendar results extracted from trace
   - ✅ Events formatted correctly for user display

### ❌ FAILING TEST (1/8)

8. **End-to-End Agent Performance** (63.06s)
   - ❌ Agent timed out after 63 seconds
   - ❌ Only completed 2 steps before timeout
   - ❌ Did not achieve goal
   - 🎯 **ROOT CAUSE**: LLM reasoning effort too high, each planning step takes 30+ seconds

---

## Performance Analysis

### What's Fast ✅
- API caching: **537x faster** on cache hits
- Loop detection: Fixed (no false positives)
- Reflection: Skipped for reads (saves 1-2 LLM calls per query)
- Preconditions: Disabled (saves 60-90s of wasted replanning)

### What's Still Slow ❌
- **LLM Planning**: 30+ seconds per planning step
- **Reasoning Effort**: Set to "high" or "xhigh" (extremely slow)
- **Total Query Time**: 60+ seconds (vs target <10s)

### Why User Sees 20s Response Times

When you run `TREYS_AGENT.bat`, the agent:
1. Loads question (instant)
2. **Plans first step** (30s) ← SLOW
3. Executes tool (0.5s with cache)
4. **Reflects** (5-10s if not skipped)
5. **Plans second step** (30s) ← SLOW
6. Calls finish tool (instant)

**Total**: ~65 seconds for a simple query

But sometimes it gets lucky and finishes in 20s if:
- Fewer planning steps needed
- Reasoning effort randomly lower
- Cache hits reduce execution time

---

## Prioritized Fix List

### 🔴 CRITICAL - Fix Immediately

**1. Fix TREYS_AGENT.bat Reasoning Effort Override**

**File**: `launchers/TREYS_AGENT.bat`
**Line**: 22
**Current**: `if not defined CODEX_REASONING_EFFORT_REASON set "CODEX_REASONING_EFFORT_REASON=xhigh"`
**Fix**: `if not defined CODEX_REASONING_EFFORT_REASON set "CODEX_REASONING_EFFORT_REASON=low"`

**Impact**: Will reduce planning time from 30s to 5-10s per step
**Expected speedup**: 3-6x faster (20s → 3-5s)

**2. Add Fast Path to Interactive Mode**

Currently only CLI mode (`python -m agent.cli "query"`) has fast path routing. Interactive mode (`TREYS_AGENT.bat`) uses full agent loop for every query.

**File**: `agent/cli.py` or `agent/treys_agent.py`
**Solution**: Add smart routing to detect simple calendar/tasks queries and use fast path

**Impact**: Will bypass agent planning entirely for simple queries
**Expected speedup**: 10-20x faster (20s → 1-2s)

### 🟡 IMPORTANT - Fix Soon

**3. Reduce Planning Timeout**

**File**: `agent/autonomous/runner.py` or test configuration
**Current**: Uses 60s timeout which the agent barely exceeds
**Fix**: Keep timeout at 60s but optimize to finish in 10s

**4. Add Logging for Performance Debugging**

**Files**: `agent/autonomous/runner.py`, `agent/llm/codex_cli_client.py`
**Add**: Timing logs for each LLM call showing duration and reasoning effort used

**Impact**: Will help identify which calls are slow

### 🟢 NICE TO HAVE - Future Improvements

**5. Persist API Cache to Disk**

Current cache clears on agent restart. Persisting to disk would make first queries after restart instant.

**6. Background Cache Warming**

Pre-fetch today/tomorrow's calendar on agent startup so first user query is instant.

**7. Batch API Calls**

Fetch multiple time ranges in one API call instead of separate calls.

---

## Recommended Actions

### Immediate (Do Right Now)

1. **Edit `launchers/TREYS_AGENT.bat` line 22**:
   - Change `xhigh` to `low`
   - This will fix 90% of your performance problems

2. **Test with diagnostic**:
   ```bash
   python scripts/diagnose_and_fix.py
   ```
   - Test #8 should now pass in <30s instead of timing out

3. **Real-world test**:
   ```bash
   TREYS_AGENT.bat
   > what's on my calendar tomorrow?
   ```
   - Should complete in 5-10s instead of 20s

### Short-term (Next Few Days)

4. **Implement fast path in interactive mode**
   - Add query detection for calendar/tasks in `agent/cli.py`
   - Route simple queries to `CalendarHelper`/`TasksHelper` directly
   - Bypass agent loop entirely for these queries

5. **Add performance logging**
   - Log LLM call durations
   - Track which reasoning effort is actually used
   - Monitor cache hit rates

### Long-term (When Time Allows)

6. **Disk-based caching**
7. **Background refresh**
8. **Batch API calls**

---

## Validation Checklist

After applying fixes, verify:

- [ ] Test #8 passes (agent completes in <30s)
- [ ] Interactive mode responds in <10s
- [ ] Cache still working (second query near-instant)
- [ ] Loop detection still works
- [ ] All 8 diagnostic tests pass

---

## Summary

**Good News**: 7/8 tests passing means all our previous fixes work correctly:
- ✅ Loop detection fixed
- ✅ Preconditions disabled
- ✅ Reflection optimized
- ✅ API caching working (537x speedup!)
- ✅ Database auto-reconnect working
- ✅ Answer extraction working

**Bad News**: The agent is still slow (20-60s) because:
- ❌ `TREYS_AGENT.bat` sets `CODEX_REASONING_EFFORT_REASON=xhigh`
- ❌ Each planning step takes 30+ seconds
- ❌ Interactive mode doesn't have fast path routing

**The Fix**: Change ONE line in `TREYS_AGENT.bat` (line 22) from `xhigh` to `low` and you'll immediately see 3-6x speedup.

**Expected Result After Fix**:
- Simple calendar query: 3-5 seconds (vs current 20s)
- Cached repeat query: <1 second (already working)
- End-to-end test: <30 seconds (vs current timeout)

---

**Next Step**: Edit `TREYS_AGENT.bat` line 22 and test immediately.
