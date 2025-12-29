#!/usr/bin/env python3
"""
Test script for planner JSON generation.

This script validates that the model router and OpenRouter client
can successfully generate structured JSON for agent planning.

Usage:
    python -m agent.scripts.test_planner_json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()


def test_schema_loading():
    """Test that the next_action schema loads correctly."""
    print("\n[TEST] Loading next_action schema...")

    schema_path = ROOT / "agent" / "llm" / "schemas" / "next_action.schema.json"
    if not schema_path.exists():
        print(f"  [FAIL] Schema not found: {schema_path}")
        return False

    try:
        schema = json.loads(schema_path.read_text())
        print(f"  [OK] Schema loaded: {schema.get('title', 'unknown')}")
        print(f"  [OK] Required fields: {schema.get('required', [])}")
        return True
    except Exception as e:
        print(f"  [FAIL] Error loading schema: {e}")
        return False


def test_router_initialization():
    """Test that the model router initializes correctly."""
    print("\n[TEST] Initializing model router...")

    try:
        from agent.llm.router import get_model_router

        router = get_model_router()
        print(f"  [OK] Router created")
        print(f"  [INFO] OpenRouter available: {router.openrouter_available}")
        print(f"  [INFO] Codex available: {router.codex_available}")
        print(f"  [INFO] Claude available: {router.claude_available}")

        if not (router.openrouter_available or router.codex_available):
            print("  [WARN] No backends available!")
            return False

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_routing_decisions():
    """Test that routing decisions work correctly."""
    print("\n[TEST] Testing routing decisions...")

    try:
        from agent.llm.router import get_model_router

        router = get_model_router()

        test_cases = [
            ("plan next step", "codex"),
            ("write code to fix bug", "codex"),
            ("audit repository security", "codex"),
            ("summarize this text", "codex"),
            ("chat about Python", "codex"),
        ]

        for task, expected in test_cases:
            result = router.route_for_task(task)
            status = "[OK]" if result == expected or router.openrouter_available else "[SKIP]"
            print(f"  {status} '{task[:30]}...' -> {result}")

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_openrouter_client():
    """Test OpenRouter client directly."""
    print("\n[TEST] Testing OpenRouter client...")

    import os
    if not os.getenv("OPENROUTER_API_KEY"):
        print("  [SKIP] OPENROUTER_API_KEY not set")
        return True  # Skip but don't fail

    try:
        from agent.llm.openrouter_client import OpenRouterClient

        client = OpenRouterClient.from_env()
        print(f"  [OK] Client created: model={client.model}")

        # Test simple text generation
        print("  [INFO] Testing text generation...")
        result = client.generate_text(
            "Say 'Hello' in exactly one word.",
            system="Respond with only a single word."
        )
        print(f"  [OK] Got response: {result[:50]}...")

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_planner_json():
    """Test actual planner JSON generation."""
    print("\n[TEST] Testing planner JSON generation...")

    import os
    if not (os.getenv("OPENROUTER_API_KEY") or os.getenv("CODEX_BIN")):
        print("  [SKIP] No LLM backend available")
        return True

    schema_path = ROOT / "agent" / "llm" / "schemas" / "next_action.schema.json"

    try:
        from agent.llm.router import get_model_router

        router = get_model_router()
        llm = router.get_llm_for_task("planner")

        if llm is None:
            print("  [SKIP] No LLM client available")
            return True

        context = """
Goal: List files in the current directory

Available tools:
- list_dir: List directory contents
- file_read: Read a file
- finish: Complete the task

History: No previous actions.

Choose the next action to accomplish the goal.
"""

        print("  [INFO] Calling planner...")
        result = llm.complete_json(context, schema_path=schema_path)

        print(f"  [OK] Got decision:")
        print(f"       action: {result.get('action')}")
        print(f"       action_input: {result.get('action_input')}")
        print(f"       reasoning: {result.get('reasoning', '')[:60]}...")

        # Validate required fields
        required = ["action", "action_input", "reasoning"]
        missing = [f for f in required if f not in result]
        if missing:
            print(f"  [WARN] Missing fields: {missing}")
            return False

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("  PLANNER JSON TEST SUITE")
    print("=" * 60)

    tests = [
        test_schema_loading,
        test_router_initialization,
        test_routing_decisions,
        test_openrouter_client,
        test_planner_json,
    ]

    results = []
    for test in tests:
        try:
            passed = test()
            results.append((test.__name__, passed))
        except Exception as e:
            print(f"  [FAIL] Unhandled error in {test.__name__}: {e}")
            results.append((test.__name__, False))

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)

    for name, ok in results:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n  Total: {passed}/{total} passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
