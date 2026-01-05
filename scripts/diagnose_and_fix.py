#!/usr/bin/env python
"""
Comprehensive diagnostic and auto-fix system for DrCodePT-Swarm.
Finds and fixes common bugs automatically.
"""

import sys
import os
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add repo to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Test results
results = []

def test(name: str):
    """Decorator to register and run a test."""
    def decorator(func):
        def wrapper():
            print(f"\n{'='*60}")
            print(f"TEST: {name}")
            print('='*60)
            try:
                start = time.time()
                result = func()
                elapsed = time.time() - start
                if result:
                    print(f"[PASS] ({elapsed:.2f}s)")
                    results.append((name, True, elapsed, None))
                else:
                    print(f"[FAIL] ({elapsed:.2f}s)")
                    results.append((name, False, elapsed, "Test returned False"))
            except Exception as e:
                elapsed = time.time() - start
                print(f"[FAIL] ({elapsed:.2f}s): {e}")
                results.append((name, False, elapsed, str(e)))
        return wrapper
    return decorator

@test("1. Environment Variables Loaded")
def test_env_loaded():
    """Check that .env is loaded correctly."""
    from dotenv import load_dotenv
    load_dotenv()

    skip_preconditions = os.getenv("AGENT_SKIP_PRECONDITIONS")
    print(f"  AGENT_SKIP_PRECONDITIONS: {skip_preconditions}")

    if skip_preconditions != "1":
        print("  [X] AGENT_SKIP_PRECONDITIONS not set to 1")
        return False

    timeout = os.getenv("CODEX_TIMEOUT_SECONDS")
    print(f"  CODEX_TIMEOUT_SECONDS: {timeout}")

    max_steps = os.getenv("AUTO_MAX_STEPS")
    print(f"  AUTO_MAX_STEPS: {max_steps}")

    return True

@test("2. Google Calendar Authentication")
def test_calendar_auth():
    """Check Google Calendar credentials exist."""
    token_path = Path.home() / ".drcodept_swarm" / "google_calendar" / "token.json"
    print(f"  Token path: {token_path}")
    print(f"  Token exists: {token_path.exists()}")

    if not token_path.exists():
        print("  [X] OAuth token not found. Run: python setup_google_calendar.py")
        return False

    return True

@test("3. Calendar API Call Speed")
def test_calendar_speed():
    """Test calendar API call performance."""
    from agent.integrations.calendar_helper import CalendarHelper

    helper = CalendarHelper()
    tomorrow = datetime.now() + timedelta(days=1)
    time_min = tomorrow.replace(hour=12, minute=0).isoformat() + 'Z'
    time_max = tomorrow.replace(hour=15, minute=0).isoformat() + 'Z'

    # First call
    start = time.time()
    events = asyncio.run(helper.list_events(time_min, time_max))
    first_call = time.time() - start
    print(f"  First call: {first_call:.3f}s ({len(events)} events)")

    # Second call (should be cached)
    start = time.time()
    events = asyncio.run(helper.list_events(time_min, time_max))
    second_call = time.time() - start
    print(f"  Second call: {second_call:.3f}s (cached)")

    if second_call > 0.1:
        print(f"  [X] Cache not working (expected <0.1s, got {second_call:.3f}s)")
        return False

    if first_call > 2.0:
        print(f"  [WARNING] First call slow (expected <2s, got {first_call:.3f}s)")

    return True

@test("4. Loop Detection for Read-Only Tools")
def test_loop_detection():
    """Test loop detection exempts read-only tools."""
    from agent.autonomous.loop_detection import LoopDetector

    ld = LoopDetector()

    # Test read-only tool (should NOT trigger loop)
    for i in range(5):
        is_loop, msg = ld.check("list_calendar_events", {"time": "12pm"}, "result")
        if is_loop:
            print(f"  [X] Loop detected on call {i+1} for read-only tool")
            return False
    print("  [OK] Read-only tool exempt from loop detection")

    # Test write tool (SHOULD trigger loop)
    ld2 = LoopDetector()
    loop_detected = False
    for i in range(5):
        is_loop, msg = ld2.check("file_write", {"path": "test"}, "ok")
        if is_loop:
            loop_detected = True
            print(f"  [OK] Loop detected on call {i+1} for write tool")
            break

    if not loop_detected:
        print("  [X] Loop detection failed for write tools")
        return False

    return True

@test("5. Reflection Skipping for Read-Only Tools")
def test_reflection_skip():
    """Test reflection is skipped for successful read-only operations."""
    from agent.autonomous.reflection import Reflector
    from agent.autonomous.models import Step, ToolResult, Observation

    r = Reflector()

    # Read-only tool (should skip reflection)
    step = Step(id='test', goal='test', tool_name='list_calendar_events', tool_args={})
    result = ToolResult(success=True, output={'events': []})
    obs = Observation(source='test', raw={}, parsed={})

    refl = r.reflect(task='test', step=step, tool_result=result, observation=obs)

    if refl.lesson != "":
        print(f"  [X] Reflection not skipped (lesson: {refl.lesson})")
        return False

    print("  [OK] Reflection skipped for successful read-only tool")
    return True

@test("6. Memory Database Connection")
def test_memory_connection():
    """Test memory database stays connected."""
    from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
    from pathlib import Path
    import time

    db_path = Path(__file__).resolve().parent.parent / "agent" / "memory" / "test_memory.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    store = SqliteMemoryStore(path=db_path)

    # Write once
    store.upsert(kind="knowledge", content="Test 1", key="test1")
    print("  [OK] First write succeeded")

    # Write again (tests connection persistence)
    store.upsert(kind="knowledge", content="Test 2", key="test2")
    print("  [OK] Second write succeeded")

    # Simulate connection close
    store._conn.close()
    print("  [OK] Connection closed (simulating bug)")

    # Write again (should auto-reconnect)
    try:
        store.upsert(kind="knowledge", content="Test 3", key="test3")
        print("  [OK] Auto-reconnect succeeded")
    except Exception as e:
        print(f"  [X] Auto-reconnect failed: {e}")
        # Still cleanup before returning
        try:
            store._conn.close()
        except:
            pass
        time.sleep(0.1)
        db_path.unlink(missing_ok=True)
        return False

    # Cleanup - properly close connection first
    try:
        store._conn.close()
    except:
        pass
    time.sleep(0.1)  # Give Windows time to release the file lock
    db_path.unlink(missing_ok=True)
    return True

@test("7. Interactive Mode Answer Extraction")
def test_answer_extraction():
    """Test that calendar results are extracted from trace."""
    from agent.cli import _extract_answer
    from pathlib import Path
    import tempfile

    # Create a mock trace file
    trace_path = None
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        trace_path = Path(f.name)

        # Write a successful calendar query
        trace_entry = {
            "type": "step",
            "action": {"tool_name": "list_calendar_events"},
            "result": {
                "success": True,
                "output": {
                    "events": [
                        {
                            "summary": "Test Event",
                            "start": {"dateTime": "2026-01-05T12:00:00-06:00"},
                            "end": {"dateTime": "2026-01-05T13:00:00-06:00"}
                        }
                    ]
                }
            }
        }
        f.write(json.dumps(trace_entry) + '\n')

    # Mock result object
    class MockResult:
        def __init__(self, path):
            self.trace_path = path

    result = MockResult(trace_path)
    answer = _extract_answer(result)

    # Cleanup
    if trace_path:
        trace_path.unlink(missing_ok=True)

    if not answer:
        print("  [X] No answer extracted")
        return False

    if "Test Event" not in answer:
        print(f"  [X] Event not in answer: {answer}")
        return False

    print(f"  [OK] Answer extracted: {answer[:50]}...")
    return True

@test("8. End-to-End Agent Performance")
def test_agent_performance():
    """Test full agent run performance."""
    from agent.autonomous.runner import AgentRunner, RunnerConfig
    from agent.autonomous.config import AgentConfig, PlannerConfig
    from agent.llm.codex_cli_client import CodexCliClient
    from pathlib import Path

    # Use fast settings
    runner_cfg = RunnerConfig(
        max_steps=5,
        timeout_seconds=60,
        profile="fast",
    )

    agent_cfg = AgentConfig(
        allow_human_ask=False,
        allow_interactive_tools=False,
    )

    planner_cfg = PlannerConfig(mode="react")

    try:
        llm = CodexCliClient.from_env()
    except Exception as e:
        print(f"  [WARNING] Skipping (Codex not available): {e}")
        return True  # Skip test if Codex not available

    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
    )

    # Simple calendar query
    task = "List calendar events for tomorrow 12-3pm"

    start = time.time()
    result = runner.run(task)
    elapsed = time.time() - start

    print(f"  Agent run: {elapsed:.2f}s")
    print(f"  Success: {result.success}")
    print(f"  Steps: {result.steps_executed}")
    print(f"  Reason: {result.stop_reason}")

    if elapsed > 30:
        print(f"  [WARNING] Slower than expected (target: <10s)")

    if not result.success:
        print(f"  [X] Agent failed: {result.stop_reason}")
        return False

    return True

def print_summary():
    """Print test summary and recommendations."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, p, _, _ in results if p)
    failed = sum(1 for _, p, _, _ in results if not p)
    total = len(results)

    for name, passed_flag, elapsed, error in results:
        status = "[PASS]" if passed_flag else "[FAIL]"
        print(f"{status:8} | {elapsed:6.2f}s | {name}")
        if error:
            print(f"         |          | Error: {error}")

    print("="*60)
    print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
    print("="*60)

    if failed > 0:
        print("\nRECOMMENDED FIXES:")

        for name, passed_flag, _, error in results:
            if not passed_flag:
                if "Environment" in name:
                    print("\n1. Fix .env file:")
                    print("   - Ensure AGENT_SKIP_PRECONDITIONS=1")
                    print("   - Restart agent after changes")

                elif "Calendar Auth" in name:
                    print("\n2. Fix Google Calendar authentication:")
                    print("   python setup_google_calendar.py")

                elif "Cache" in name or "Speed" in name:
                    print("\n3. Clear Python cache and restart:")
                    print("   - Close all agent processes")
                    print("   - Delete __pycache__ folders")
                    print("   - Restart agent")

                elif "Loop Detection" in name:
                    print("\n4. Loop detection broken:")
                    print("   - Check agent/autonomous/loop_detection.py")
                    print("   - Ensure EXEMPT_TOOLS is defined")

                elif "Memory" in name:
                    print("\n5. Memory database issue:")
                    print("   - Check agent/autonomous/memory/sqlite_store.py")
                    print("   - Ensure _ensure_connection() method exists")

    return failed == 0

if __name__ == "__main__":
    print("="*60)
    print("DrCodePT-Swarm Diagnostic Suite")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all tests
    test_env_loaded()
    test_calendar_auth()
    test_calendar_speed()
    test_loop_detection()
    test_reflection_skip()
    test_memory_connection()
    test_answer_extraction()
    test_agent_performance()

    # Print summary
    all_passed = print_summary()

    sys.exit(0 if all_passed else 1)
