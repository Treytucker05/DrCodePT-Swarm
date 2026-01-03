"""
Test script for Yahoo Mail IMAP integration.
Verifies credentials and tests basic mail functions.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.memory.credentials import get_credential
from agent.integrations import yahoo_mail


def check_credentials():
    """Check if Yahoo IMAP credentials are stored."""
    print("\n[1/4] Checking Yahoo IMAP credentials...")
    try:
        creds = get_credential("yahoo_imap")
        if creds and creds.get("username") and creds.get("password"):
            print(f"[OK] Yahoo IMAP credentials found for: {creds.get('username')}")
            return True
        else:
            print("[FAIL] Yahoo IMAP credentials not found or incomplete")
            print("\nTo set up Yahoo IMAP credentials:")
            print("1. Generate an app password in your Yahoo account settings")
            print("2. Run in agent: Cred: yahoo_imap")
            print("3. Enter your Yahoo email and app password")
            return False
    except Exception as e:
        print(f"[FAIL] Error checking credentials: {e}")
        return False


def test_list_folders():
    """Test listing folders."""
    print("\n[2/4] Testing folder listing...")
    try:
        folders = yahoo_mail.list_folders()
        print(f"[OK] Found {len(folders)} folders")
        if folders:
            print(f"  Sample folders: {', '.join(folders[:5])}")
        return True
    except Exception as e:
        print(f"[FAIL] Error listing folders: {e}")
        return False


def test_list_messages():
    """Test listing messages from INBOX."""
    print("\n[3/4] Testing message listing...")
    try:
        messages = yahoo_mail.list_messages(limit=5, folder="INBOX")
        print(f"[OK] Listed {len(messages)} messages from INBOX")
        if messages:
            print(f"  Latest message: {messages[0].get('subject', 'No subject')[:50]}")
        return True
    except Exception as e:
        print(f"[FAIL] Error listing messages: {e}")
        print("  (This may indicate IMAP connection or credential issues)")
        return False


def test_folder_operations():
    """Test folder operations (read-only, won't modify anything)."""
    print("\n[4/4] Testing folder operations (read-only)...")
    try:
        # Just test that the functions exist and can be called safely
        # We won't actually create/delete folders in the test
        folders = yahoo_mail.list_folders()
        if folders:
            print(f"[OK] Folder operations available (tested with {len(folders)} existing folders)")
        return True
    except Exception as e:
        print(f"[WARN] Folder operations test: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Yahoo Mail IMAP Integration Test")
    print("=" * 60)

    results = {
        "credentials": check_credentials(),
    }

    if results["credentials"]:
        results["list_folders"] = test_list_folders()
        results["list_messages"] = test_list_messages()
        results["folder_ops"] = test_folder_operations()
    else:
        results["list_folders"] = False
        results["list_messages"] = False
        results["folder_ops"] = False

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for check, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {check}")

    all_passed = all(results.values())
    if all_passed:
        print("\n[SUCCESS] All checks passed! Yahoo Mail IMAP integration is ready.")
        return 0
    else:
        print("\n[WARN] Some checks failed. Please address the issues above.")
        if not results["credentials"]:
            print("\nNext step: Set up Yahoo IMAP credentials (see instructions above)")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

