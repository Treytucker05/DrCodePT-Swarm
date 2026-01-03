# Quick Test Guide - Agent Fixes

## Verify Fixes Were Applied

Run these commands to verify the fixes are working:

### 1. Check Google Console Flow
```bash
python -c "from agent.autonomous.google_console_flow import GoogleConsoleStateMachine; from agent.autonomous.computer_use import get_computer_use_router; router = get_computer_use_router(); sm = GoogleConsoleStateMachine(router); print('✓ GoogleConsoleStateMachine initialized'); print(f'✓ Precondition check: {hasattr(sm, \"_check_precondition\")}'); print(f'✓ State verification: {hasattr(sm, \"_verify_state_changed\")}'); print(f'✓ Reflection: {hasattr(sm, \"_reflect_on_action_failure\")}')"
```

Expected output:
```
✓ GoogleConsoleStateMachine initialized
✓ Precondition check: True
✓ State verification: True
✓ Reflection: True
```

### 2. Check Hybrid Executor
```bash
python -c "from agent.autonomous.hybrid_executor import HybridExecutor; exec = HybridExecutor(); print('✓ HybridExecutor initialized'); print(f'✓ Has Reflector: {exec.reflector is not None}'); print(f'✓ Reflector type: {type(exec.reflector).__name__ if exec.reflector else \"None\"}')"
```

Expected output:
```
✓ HybridExecutor initialized
✓ Has Reflector: True
✓ Reflector type: Reflector
```

## Test Google Calendar OAuth Flow

### Option 1: Interactive Mode
```bash
python -m agent.cli
```

Then type:
```
help me access my google calendar
```

### Option 2: Direct Command
```bash
python -m agent.cli "help me access my google calendar"
```

## What to Watch For

### ✅ Good Signs (Fixes Working)
1. **Precondition checks**: Look for `[PRECONDITION]` logs
   - Should see "Target 'X' is visible" or "not visible"

2. **State transitions**: Look for `[PROGRESS]` logs
   - Should see "State transition: X → Y" after successful clicks
   - Should see warnings if state doesn't change

3. **Reflection on failures**: Look for `[REFLECTION]` logs
   - Should see "LIKELY CAUSE" and "ALTERNATIVE" suggestions
   - Should provide helpful context about what went wrong

4. **Fast escalation**: Should ask user for help after **2 failures** (not 3+)
   - Look for `[ESCALATE]` messages
   - Should include reflection in escalation message

5. **No infinite loops**: Agent should stop and ask for help instead of repeating same action 10+ times

### ❌ Bad Signs (Fixes Not Working)
1. Agent loops through same action 5+ times without asking for help
2. No `[PRECONDITION]`, `[PROGRESS]`, or `[REFLECTION]` logs
3. Same errors repeated without any analysis or adaptation
4. Agent continues after clicks that don't change state

## Debug Logs

To see detailed logs, set verbose mode:

```bash
python -m agent.cli -v "help me access my google calendar"
```

Or check the run logs:
```bash
# Find latest run
ls -lt runs/

# View trace
cat runs/LATEST_RUN_ID/trace.jsonl
```

## Check Reflexion Memory

After running the agent, check if failures are being saved:

```bash
# View reflexion entries
cat runs/reflexion.jsonl | tail -10

# Or pretty print
python -c "import json; [print(json.dumps(json.loads(line), indent=2)) for line in open('runs/reflexion.jsonl').readlines()[-3:]]"
```

Expected: Should see entries with:
- `objective`: The task being attempted
- `errors`: List of errors encountered
- `reflection`: Analysis of what went wrong
- `fix`: Suggested alternative approach
- `outcome`: "failure" or "success"

## Troubleshooting

### Issue: No precondition checks appearing
**Solution**: Make sure `pytesseract` is installed:
```bash
pip install pytesseract
# Also install Tesseract OCR binary
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
```

### Issue: Reflector not initializing
**Solution**: Check if reflection.py is properly imported:
```bash
python -c "from agent.autonomous.reflection import Reflector; print('Reflector imported successfully')"
```

### Issue: Agent still looping
**Solution**:
1. Check if `_action_failures` is being tracked
2. Verify escalation threshold is set to 2 (not 3)
3. Look for state transition verification logs

## Expected Improvement

**Before fixes**:
- Agent would loop 10+ times on same failed click
- No understanding of WHY actions failed
- Escalation after 3+ failures
- Separate stall detection causing conflicts

**After fixes**:
- Agent stops after 2 failures and asks for help
- Provides reflection explaining what went wrong
- Verifies state changes after each action
- Single unified progress tracking system

## Success Criteria

The agent should:
1. ✅ Check preconditions before clicking
2. ✅ Verify state changed after clicking
3. ✅ Reflect on failures with specific analysis
4. ✅ Escalate to user after 2 failures (max)
5. ✅ Save reflexion entries for learning
6. ✅ Provide helpful error messages with reflection

If all 6 criteria pass, the fixes are working correctly!
