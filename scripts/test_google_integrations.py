"""
Test script for Google Calendar and Tasks integration.
Verifies MCP servers are configured and credentials exist.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = REPO_ROOT / "credentials" / "gcp-oauth-credentials.json"
MCP_CONFIG_PATH = REPO_ROOT / "agent" / "mcp" / "servers.json"

pytestmark = pytest.mark.integration


def check_credentials():
    """Check if OAuth credentials file exists."""
    print("\n[1/4] Checking OAuth credentials file...")
    if CREDENTIALS_PATH.exists():
        print(f"[OK] Credentials file found: {CREDENTIALS_PATH}")
        try:
            with open(CREDENTIALS_PATH) as f:
                data = json.load(f)
            if "client_id" in data and "client_secret" in data:
                print("[OK] Credentials file contains valid OAuth client data")
                return True
            else:
                print("[WARN] Credentials file exists but may be missing required fields")
                return False
        except json.JSONDecodeError:
            print("[FAIL] Credentials file is not valid JSON")
            return False
    else:
        print(f"[FAIL] Credentials file not found: {CREDENTIALS_PATH}")
        print("\nTo set up Google OAuth credentials:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create/select a project")
        print("3. Enable Google Calendar API and Google Tasks API")
        print("4. Create OAuth 2.0 credentials (Desktop app type)")
        print(f"5. Download and save as: {CREDENTIALS_PATH}")
        return False


def check_mcp_config():
    """Check MCP server configuration."""
    print("\n[2/4] Checking MCP server configuration...")
    if not MCP_CONFIG_PATH.exists():
        print(f"[FAIL] MCP config file not found: {MCP_CONFIG_PATH}")
        return False

    try:
        with open(MCP_CONFIG_PATH) as f:
            config = json.load(f)

        has_calendar = "google-calendar" in config
        has_tasks = "google-tasks" in config

        if has_calendar:
            print("[OK] Google Calendar MCP server configured")
        else:
            print("[FAIL] Google Calendar MCP server not configured")

        if has_tasks:
            print("[OK] Google Tasks MCP server configured")
        else:
            print("[FAIL] Google Tasks MCP server not configured")

        return has_calendar and has_tasks

    except json.JSONDecodeError:
        print("[FAIL] MCP config file is not valid JSON")
        return False
    except Exception as e:
        print(f"[FAIL] Error reading MCP config: {e}")
        return False


def check_modules():
    """Check if required Python modules exist."""
    print("\n[3/4] Checking Python modules...")
    modules = [
        ("agent.mcp.client", "MCP client"),
        ("agent.integrations.calendar_helper", "Calendar helper"),
        ("agent.integrations.tasks_helper", "Tasks helper"),
    ]

    all_found = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"[OK] {display_name} module found")
        except ImportError:
            print(f"[FAIL] {display_name} module not found: {module_name}")
            all_found = False

    return all_found


async def test_mcp_connectivity():
    """Test MCP server connectivity (if credentials exist)."""
    print("\n[4/4] Testing MCP server connectivity...")
    
    if not CREDENTIALS_PATH.exists():
        print("[SKIP] Skipping connectivity test (credentials file not found)")
        return False

    try:
        from agent.mcp.client import MCPClient

        client = MCPClient()
        await client.initialize(["google-calendar", "google-tasks"])

        tools = client.list_tools()
        print(f"[OK] MCP servers initialized successfully")
        print(f"[OK] Found {len(tools)} available tools")

        calendar_tools = [t for t in tools if t.startswith("google-calendar")]
        tasks_tools = [t for t in tools if t.startswith("google-tasks")]

        if calendar_tools:
            print(f"[OK] Google Calendar tools available: {len(calendar_tools)}")
        else:
            print("[WARN] No Google Calendar tools found")

        if tasks_tools:
            print(f"[OK] Google Tasks tools available: {len(tasks_tools)}")
        else:
            print("[WARN] No Google Tasks tools found")

        await client.shutdown()
        return len(calendar_tools) > 0 and len(tasks_tools) > 0

    except Exception as e:
        print(f"[WARN] MCP connectivity test failed: {e}")
        print("  (This is normal if OAuth authentication is not complete)")
        return False


async def main():
    """Run all checks."""
    print("=" * 60)
    print("Google Calendar & Tasks Integration Test")
    print("=" * 60)

    results = {
        "credentials": check_credentials(),
        "mcp_config": check_mcp_config(),
        "modules": check_modules(),
    }

    if all([results["credentials"], results["mcp_config"], results["modules"]]):
        results["connectivity"] = await test_mcp_connectivity()
    else:
        results["connectivity"] = False

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for check, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {check}")

    all_passed = all(results.values())
    if all_passed:
        print("\n[SUCCESS] All checks passed! Google Calendar/Tasks integration is ready.")
        return 0
    else:
        print("\n[WARN] Some checks failed. Please address the issues above.")
        if not results["credentials"]:
            print("\nNext step: Set up OAuth credentials (see instructions above)")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

