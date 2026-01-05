#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test performance fixes applied to the agent."""
import asyncio
import time
import sys
from datetime import datetime, timedelta

import pytest

from agent.integrations.calendar_helper import CalendarHelper
from agent.integrations.tasks_helper import TasksHelper

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

pytestmark = pytest.mark.integration


def _calendar_caching() -> bool:
    """Test that calendar caching works."""
    print("Testing calendar caching...")
    helper = CalendarHelper()
    tomorrow = datetime.now() + timedelta(days=1)
    time_min = tomorrow.replace(hour=12, minute=0).isoformat() + "Z"
    time_max = tomorrow.replace(hour=15, minute=0).isoformat() + "Z"

    # First call - should hit API
    print("  First call (hitting API)...")
    start = time.time()
    events1 = asyncio.run(helper.list_events(time_min, time_max))
    elapsed1 = time.time() - start
    print(f"    Found {len(events1)} events in {elapsed1:.3f}s")

    # Second call - should use cache
    print("  Second call (from cache)...")
    start = time.time()
    events2 = asyncio.run(helper.list_events(time_min, time_max))
    elapsed2 = time.time() - start
    print(f"    Found {len(events2)} events in {elapsed2:.3f}s")

    if elapsed2 < 0.1:
        print("  âœ“ PASS: Caching works (second call near-instant)")
        return True
    print(f"  âœ— FAIL: Second call took {elapsed2:.3f}s (expected <0.1s)")
    return False


def test_calendar_caching():
    assert _calendar_caching()


def _tasks_caching() -> bool:
    """Test that tasks caching works."""
    print("\nTesting tasks caching...")
    helper = TasksHelper()

    # First call - should hit API
    print("  First call (hitting API)...")
    start = time.time()
    tasks1 = asyncio.run(helper.list_tasks())
    elapsed1 = time.time() - start
    print(f"    Found {len(tasks1)} tasks in {elapsed1:.3f}s")

    # Second call - should use cache
    print("  Second call (from cache)...")
    start = time.time()
    tasks2 = asyncio.run(helper.list_tasks())
    elapsed2 = time.time() - start
    print(f"    Found {len(tasks2)} tasks in {elapsed2:.3f}s")

    if elapsed2 < 0.1:
        print("  âœ“ PASS: Caching works (second call near-instant)")
        return True
    print(f"  âœ— FAIL: Second call took {elapsed2:.3f}s (expected <0.1s)")
    return False


def test_tasks_caching():
    assert _tasks_caching()


if __name__ == "__main__":
    print("=" * 60)
    print("PERFORMANCE FIXES TEST SUITE")
    print("=" * 60)

    results = []

    try:
        results.append(("Calendar caching", _calendar_caching()))
    except Exception as e:
        print(f"  âœ— FAIL: {e}")
        results.append(("Calendar caching", False))

    try:
        results.append(("Tasks caching", _tasks_caching()))
    except Exception as e:
        print(f"  âœ— FAIL: {e}")
        results.append(("Tasks caching", False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "âœ“ PASS" if passed else "âœ— FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)
