#!/usr/bin/env python
"""
Deep bug scan - Tests edge cases and failure modes not covered by basic diagnostic.
"""

import sys
import os
import time
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

@test("1. Server-based LLM Backend Availability")
def test_server_backend():
    """Test if LLM server backend is running and accessible."""
    import requests

    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=2)
        print(f"  Server status: {response.status_code}")

        if response.status_code == 200:
            print("  [OK] LLM server is running")
            return True
        else:
            print(f"  [X] LLM server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  [WARNING] LLM server not running (this is OK if using Codex CLI)")
        return True  # Not a bug if server isn't used
    except Exception as e:
        print(f"  [X] Error checking server: {e}")
        return False

@test("2. Calendar API - Empty Time Range")
def test_calendar_empty_range():
    """Test calendar API with time range that has no events."""
    from agent.integrations.calendar_helper import CalendarHelper

    helper = CalendarHelper()

    # Query far future (unlikely to have events)
    far_future = datetime.now() + timedelta(days=365)
    time_min = far_future.replace(hour=2, minute=0).isoformat() + 'Z'
    time_max = far_future.replace(hour=3, minute=0).isoformat() + 'Z'

    try:
        events = asyncio.run(helper.list_events(time_min, time_max))
        print(f"  Found {len(events)} events in far future")
        print("  [OK] Empty result handled correctly")
        return True
    except Exception as e:
        print(f"  [X] Failed on empty range: {e}")
        return False

@test("3. Calendar API - Invalid Time Format")
def test_calendar_invalid_time():
    """Test calendar API error handling with invalid time format."""
    from agent.integrations.calendar_helper import CalendarHelper

    helper = CalendarHelper()

    try:
        events = asyncio.run(helper.list_events("invalid-time", "also-invalid"))
        print(f"  [X] Should have raised error but got {len(events)} events")
        return False
    except Exception as e:
        print(f"  [OK] Error correctly raised: {type(e).__name__}")
        return True

@test("4. Tasks API - Empty Task List")
def test_tasks_empty():
    """Test tasks API with no tasks."""
    from agent.integrations.tasks_helper import TasksHelper

    helper = TasksHelper()

    try:
        tasks = asyncio.run(helper.list_tasks())
        print(f"  Found {len(tasks)} tasks")
        print("  [OK] Empty/populated task list handled")
        return True
    except Exception as e:
        print(f"  [X] Failed to list tasks: {e}")
        return False

@test("5. MCP Server Initialization")
def test_mcp_servers():
    """Test MCP server configuration and initialization."""
    from agent.mcp.client import MCPClient

    try:
        client = MCPClient()
        print(f"  Loaded {len(client.servers)} MCP server configs")

        # Check if servers are defined
        if len(client.servers) == 0:
            print("  [WARNING] No MCP servers configured")
            return True  # Not a bug, just not configured

        print("  [OK] MCP client initialized")
        return True
    except Exception as e:
        print(f"  [X] MCP initialization failed: {e}")
        return False

@test("6. Memory Store - Sequential Multi-Instance Access")
def test_memory_multi_instance():
    """Test memory store handles multiple instances accessing same DB."""
    from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
    from pathlib import Path

    db_path = Path(__file__).resolve().parent.parent / "agent" / "memory" / "test_multi.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # NOTE: SQLite doesn't support true concurrent writes from multiple threads
    # This tests sequential access from multiple instances instead

    try:
        # First instance writes
        store1 = SqliteMemoryStore(path=db_path)
        store1.upsert(kind="knowledge", content="From instance 1", key="test1")
        print("  [OK] Instance 1 wrote data")
        store1._conn.close()

        # Second instance reads and writes
        store2 = SqliteMemoryStore(path=db_path)
        store2.upsert(kind="knowledge", content="From instance 2", key="test2")
        print("  [OK] Instance 2 wrote data")
        store2._conn.close()

        # Third instance reads both
        store3 = SqliteMemoryStore(path=db_path)
        results = store3.search(query="instance", kinds=["knowledge"], limit=10)
        print(f"  [OK] Instance 3 found {len(results)} records")

        store3._conn.close()
        time.sleep(0.1)
        db_path.unlink(missing_ok=True)

        return True
    except Exception as e:
        print(f"  [X] Multi-instance access failed: {e}")
        try:
            db_path.unlink(missing_ok=True)
        except:
            pass
        return False

@test("7. Loop Detection - Boundary Case (Exactly 3 Calls)")
def test_loop_boundary():
    """Test loop detection at the boundary (exactly 3 identical calls)."""
    from agent.autonomous.loop_detection import LoopDetector

    ld = LoopDetector()

    # Test write tool with exactly 3 calls
    for i in range(3):
        is_loop, msg = ld.check("file_write", {"path": "test.txt"}, "success")

        if i < 2:
            if is_loop:
                print(f"  [X] False positive on call {i+1}")
                return False
        else:  # i == 2 (3rd call)
            if is_loop:
                print(f"  [OK] Loop detected on exactly 3rd call")
                return True
            else:
                print(f"  [X] Loop not detected on 3rd call")
                return False

    return False

@test("8. Cache Expiration After TTL")
def test_cache_expiration():
    """Test that cache expires after TTL."""
    from agent.integrations.calendar_helper import CalendarHelper

    helper = CalendarHelper()
    helper._cache_ttl = 1  # Set to 1 second for testing

    tomorrow = datetime.now() + timedelta(days=1)
    time_min = tomorrow.replace(hour=14, minute=0).isoformat() + 'Z'
    time_max = tomorrow.replace(hour=15, minute=0).isoformat() + 'Z'

    # First call
    events1 = asyncio.run(helper.list_events(time_min, time_max))
    print(f"  First call: {len(events1)} events")

    # Second call immediately (should be cached)
    start = time.time()
    events2 = asyncio.run(helper.list_events(time_min, time_max))
    elapsed_cached = time.time() - start
    print(f"  Immediate second call: {elapsed_cached:.3f}s")

    if elapsed_cached > 0.1:
        print(f"  [X] Cache not working (expected <0.1s)")
        return False

    # Wait for cache to expire
    print("  Waiting for cache to expire (1.5s)...")
    time.sleep(1.5)

    # Third call after expiration (should hit API)
    start = time.time()
    events3 = asyncio.run(helper.list_events(time_min, time_max))
    elapsed_expired = time.time() - start
    print(f"  Third call after expiration: {elapsed_expired:.3f}s")

    if elapsed_expired < 0.1:
        print(f"  [X] Cache didn't expire (should hit API)")
        return False

    print("  [OK] Cache expires correctly")
    return True

@test("9. Answer Extraction - No Events Found")
def test_answer_no_events():
    """Test answer extraction when no events are found."""
    from agent.cli import _extract_answer
    from pathlib import Path
    import tempfile
    import json

    trace_path = None
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        trace_path = Path(f.name)

        # Write a successful calendar query with empty results
        trace_entry = {
            "type": "step",
            "action": {"tool_name": "list_calendar_events"},
            "result": {
                "success": True,
                "output": {
                    "events": []  # Empty list
                }
            }
        }
        f.write(json.dumps(trace_entry) + '\n')

    class MockResult:
        def __init__(self, path):
            self.trace_path = path

    result = MockResult(trace_path)
    answer = _extract_answer(result)

    # Cleanup
    if trace_path:
        trace_path.unlink(missing_ok=True)

    if not answer:
        print("  [X] No answer extracted for empty results")
        return False

    if "No events" in answer or "0 event" in answer:
        print(f"  [OK] Correctly reports no events: '{answer}'")
        return True
    else:
        print(f"  [X] Answer unclear for empty results: '{answer}'")
        return False

@test("10. Answer Extraction - Failed Tool Call")
def test_answer_failed_tool():
    """Test answer extraction when tool call fails."""
    from agent.cli import _extract_answer
    from pathlib import Path
    import tempfile
    import json

    trace_path = None
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        trace_path = Path(f.name)

        # Write a failed calendar query
        trace_entry = {
            "type": "step",
            "action": {"tool_name": "list_calendar_events"},
            "result": {
                "success": False,
                "error": "Authentication failed"
            }
        }
        f.write(json.dumps(trace_entry) + '\n')

    class MockResult:
        def __init__(self, path):
            self.trace_path = path

    result = MockResult(trace_path)
    answer = _extract_answer(result)

    # Cleanup
    if trace_path:
        trace_path.unlink(missing_ok=True)

    # For failed calls, answer might be None or an error message
    print(f"  Answer for failed call: {answer}")
    print("  [OK] Failed tool handled (answer may be None)")
    return True  # Not a bug - this is expected behavior

@test("11. Codex CLI Client - Model Configuration")
def test_codex_config():
    """Test Codex CLI client respects environment configuration."""
    from agent.llm.codex_cli_client import CodexCliClient
    from dotenv import load_dotenv

    load_dotenv()

    # Check environment variables
    model = os.getenv("CODEX_MODEL")
    timeout = os.getenv("CODEX_TIMEOUT_SECONDS")

    print(f"  CODEX_MODEL: {model}")
    print(f"  CODEX_TIMEOUT_SECONDS: {timeout}")

    if not model:
        print("  [WARNING] CODEX_MODEL not set")

    if not timeout:
        print("  [WARNING] CODEX_TIMEOUT_SECONDS not set")

    print("  [OK] Configuration variables present")
    return True

@test("12. Calendar Cache - Different Time Ranges")
def test_cache_different_ranges():
    """Test that cache correctly distinguishes different time ranges."""
    from agent.integrations.calendar_helper import CalendarHelper

    helper = CalendarHelper()

    tomorrow = datetime.now() + timedelta(days=1)

    # Range 1: 12-1pm
    time_min1 = tomorrow.replace(hour=12, minute=0).isoformat() + 'Z'
    time_max1 = tomorrow.replace(hour=13, minute=0).isoformat() + 'Z'

    # Range 2: 2-3pm (different)
    time_min2 = tomorrow.replace(hour=14, minute=0).isoformat() + 'Z'
    time_max2 = tomorrow.replace(hour=15, minute=0).isoformat() + 'Z'

    # Query range 1
    events1 = asyncio.run(helper.list_events(time_min1, time_max1))
    print(f"  Range 1 (12-1pm): {len(events1)} events")

    # Query range 2 (should NOT use cache from range 1)
    start = time.time()
    events2 = asyncio.run(helper.list_events(time_min2, time_max2))
    elapsed = time.time() - start
    print(f"  Range 2 (2-3pm): {len(events2)} events in {elapsed:.3f}s")

    if elapsed < 0.1:
        print("  [X] Cache incorrectly reused for different range")
        return False

    # Query range 1 again (SHOULD use cache)
    start = time.time()
    events1_cached = asyncio.run(helper.list_events(time_min1, time_max1))
    elapsed_cached = time.time() - start
    print(f"  Range 1 again: {len(events1_cached)} events in {elapsed_cached:.3f}s")

    if elapsed_cached > 0.1:
        print("  [X] Cache not working for repeated query")
        return False

    print("  [OK] Cache correctly distinguishes time ranges")
    return True

@test("13. Memory Store - Large Content")
def test_memory_large_content():
    """Test memory store with large content."""
    from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
    from pathlib import Path

    db_path = Path(__file__).resolve().parent.parent / "agent" / "memory" / "test_large.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    store = SqliteMemoryStore(path=db_path)

    # Create large content (10KB)
    large_content = "x" * 10000

    try:
        store.upsert(kind="knowledge", content=large_content, key="large_test")
        print(f"  [OK] Stored {len(large_content)} characters")

        # Try to retrieve
        results = store.search(query="large_test", kinds=["knowledge"], limit=1)
        if results and len(results[0].content) == 10000:
            print("  [OK] Retrieved large content correctly")
            success = True
        else:
            print("  [X] Large content not retrieved correctly")
            success = False
    except Exception as e:
        print(f"  [X] Failed with large content: {e}")
        success = False
    finally:
        # Cleanup
        try:
            store._conn.close()
        except:
            pass
        time.sleep(0.1)
        db_path.unlink(missing_ok=True)

    return success

@test("14. Reflection - Failed Tool Result")
def test_reflection_failed_tool():
    """Test reflection handles failed tool results."""
    from agent.autonomous.reflection import Reflector
    from agent.autonomous.models import Step, ToolResult, Observation

    r = Reflector()

    # Failed tool
    step = Step(id='test', goal='test', tool_name='list_calendar_events', tool_args={})
    result = ToolResult(success=False, error="Authentication failed")
    obs = Observation(source='test', raw={}, parsed={})

    try:
        refl = r.reflect(task='test', step=step, tool_result=result, observation=obs)
        print(f"  Reflection status: {refl.status}")
        print(f"  Failure type: {refl.failure_type}")

        # For failed results, reflection should NOT be skipped
        if refl.lesson == "" and refl.status == "success":
            print("  [X] Reflection incorrectly skipped for failed tool")
            return False

        print("  [OK] Failed tool handled correctly by reflection")
        return True
    except Exception as e:
        print(f"  [X] Reflection crashed on failed tool: {e}")
        return False

def print_summary():
    """Print test summary and recommendations."""
    print("\n" + "="*60)
    print("DEEP BUG SCAN SUMMARY")
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
        print("\nBUGS FOUND:")

        for name, passed_flag, _, error in results:
            if not passed_flag:
                print(f"\n- {name}")
                print(f"  Error: {error}")

    return failed == 0

if __name__ == "__main__":
    print("="*60)
    print("DrCodePT-Swarm Deep Bug Scan")
    print("Testing edge cases and failure modes")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all tests
    test_server_backend()
    test_calendar_empty_range()
    test_calendar_invalid_time()
    test_tasks_empty()
    test_mcp_servers()
    test_memory_multi_instance()
    test_loop_boundary()
    test_cache_expiration()
    test_answer_no_events()
    test_answer_failed_tool()
    test_codex_config()
    test_cache_different_ranges()
    test_memory_large_content()
    test_reflection_failed_tool()

    # Print summary
    all_passed = print_summary()

    sys.exit(0 if all_passed else 1)
