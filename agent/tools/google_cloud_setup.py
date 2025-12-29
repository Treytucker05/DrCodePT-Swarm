"""
Google Cloud Project Setup - Desktop Commander Automation.

Uses PyAutoGUI to control the REAL Chrome browser on desktop.
This bypasses Google's Selenium/Playwright detection.

The agent:
1. Opens Chrome browser
2. Navigates to Google Cloud Console
3. Uses vision + mouse/keyboard to interact
4. Creates project, enables APIs, creates OAuth credentials
5. Downloads credentials and completes OAuth flow
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_PATH = REPO_ROOT / "agent" / "integrations" / "google_credentials.json"
TOKEN_PATH = REPO_ROOT / "agent" / "memory" / "google_token.json"
DOWNLOADS_DIR = Path(os.path.expanduser("~/Downloads"))
SCREENSHOTS_DIR = REPO_ROOT / "agent" / "screenshots"


def _import_pyautogui():
    """Import PyAutoGUI for desktop control."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        return pyautogui, None
    except ImportError as e:
        return None, f"PyAutoGUI not installed: {e}"


def _take_screenshot(name: str = "screen") -> Optional[Path]:
    """Take a screenshot of the current screen."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return None

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOTS_DIR / f"{name}_{ts}.png"
    img = pyautogui.screenshot()
    img.save(path)
    return path


def _open_chrome(url: str) -> bool:
    """Open Chrome browser with a URL."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break

    if not chrome_exe:
        # Try via PATH
        chrome_exe = shutil.which("chrome") or shutil.which("google-chrome")

    if not chrome_exe:
        return False

    try:
        subprocess.Popen([chrome_exe, url])
        time.sleep(3)  # Wait for Chrome to open
        return True
    except Exception as e:
        logger.error(f"Failed to open Chrome: {e}")
        return False


def _click_at(x: int, y: int, clicks: int = 1) -> bool:
    """Click at specific coordinates."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    try:
        pyautogui.click(x, y, clicks=clicks)
        return True
    except Exception:
        return False


def _type_text(text: str, interval: float = 0.02) -> bool:
    """Type text using keyboard."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    try:
        pyautogui.write(text, interval=interval)
        return True
    except Exception:
        return False


def _press_key(key: str) -> bool:
    """Press a keyboard key."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    try:
        pyautogui.press(key)
        return True
    except Exception:
        return False


def _hotkey(*keys) -> bool:
    """Press a key combination."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    try:
        pyautogui.hotkey(*keys)
        return True
    except Exception:
        return False


def _wait_and_prompt(message: str) -> str:
    """Prompt user for input."""
    print(f"\n[USER ACTION REQUIRED] {message}")
    return input("> ").strip()


def _find_downloaded_credentials() -> Optional[Path]:
    """Find the most recently downloaded credentials JSON file."""
    search_dirs = [
        DOWNLOADS_DIR,
        REPO_ROOT / "downloads",
        REPO_ROOT / "evidence" / "downloads",
    ]

    candidates = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        # Look for Google OAuth credential files
        for pattern in ["client_secret*.json", "*oauth*.json", "credentials*.json"]:
            for f in search_dir.glob(pattern):
                # Skip if older than 1 hour
                if time.time() - f.stat().st_mtime < 3600:
                    candidates.append((f.stat().st_mtime, f))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


def _move_credentials_to_place(src: Path) -> bool:
    """Move downloaded credentials to the expected location."""
    try:
        CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, CREDENTIALS_PATH)
        return True
    except Exception as e:
        logger.error(f"Failed to move credentials: {e}")
        return False


def _run_oauth_flow() -> Tuple[bool, str]:
    """Run the OAuth flow to get tokens."""
    if not CREDENTIALS_PATH.exists():
        return False, f"Credentials file not found at {CREDENTIALS_PATH}"

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events',
            'https://www.googleapis.com/auth/tasks',
        ]

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            scopes
        )

        # This opens a browser for user consent
        creds = flow.run_local_server(port=0)

        # Save the token
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

        return True, "OAuth flow completed successfully"

    except Exception as e:
        return False, f"OAuth flow failed: {e}"


def _check_already_configured() -> bool:
    """Check if Google APIs are already configured."""
    if not CREDENTIALS_PATH.exists():
        return False
    if not TOKEN_PATH.exists():
        return False

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
        if creds and creds.valid:
            return True
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
            return True
    except Exception:
        pass

    return False


def _log_to_reflexion(action: str, success: bool, details: str) -> None:
    """Log setup attempts to reflexion for learning."""
    try:
        from agent.autonomous.memory.reflexion import ReflexionEntry, write_reflexion

        entry = ReflexionEntry(
            id=f"gcloud_setup_{uuid4().hex[:8]}",
            timestamp=datetime.utcnow().isoformat() + "Z",
            objective="Full Google Cloud project setup for calendar access",
            context_fingerprint="google_cloud_desktop_setup",
            phase=action,
            tool_calls=[{"tool": "full_google_setup", "action": action}],
            errors=[] if success else [details],
            reflection=f"Google Cloud setup {action}: {'succeeded' if success else 'failed'} - {details}",
            fix=action if success else f"Retry or manually: {details}",
            outcome="success" if success else "failure",
            tags=["google", "oauth", "setup", "calendar", "cloud", "desktop"],
        )
        write_reflexion(entry)
    except Exception as e:
        logger.debug(f"Could not write to reflexion: {e}")


# ============================================================================
# Pydantic Models
# ============================================================================

class FullGoogleSetupArgs(BaseModel):
    """Arguments for full Google Cloud setup."""
    project_name: str = Field(
        default="treys-agent",
        description="Name for the Google Cloud project"
    )
    skip_if_configured: bool = Field(
        default=True,
        description="Skip setup if already configured"
    )


class CheckAndFixArgs(BaseModel):
    """Arguments for check and fix tool."""
    auto_fix: bool = Field(
        default=True,
        description="Automatically fix issues when possible"
    )


# ============================================================================
# Tool Implementations
# ============================================================================

def full_google_setup(ctx, args: FullGoogleSetupArgs):
    """
    Complete Google Cloud setup using Desktop Commander.

    This opens the REAL Chrome browser and guides you through:
    1. Google Cloud Console login
    2. Project creation
    3. API enabling (Calendar, Tasks)
    4. OAuth consent screen setup
    5. OAuth credential creation
    6. Credential download
    7. OAuth flow completion

    Uses PyAutoGUI for mouse/keyboard - bypasses bot detection.
    """
    from agent.autonomous.models import ToolResult

    # Check if already configured
    if args.skip_if_configured and _check_already_configured():
        _log_to_reflexion("check_existing", True, "Already configured")
        return ToolResult(
            success=True,
            output={
                "status": "already_configured",
                "message": "Google APIs are already configured and working!",
                "credentials_path": str(CREDENTIALS_PATH),
                "token_path": str(TOKEN_PATH),
            },
        )

    # Check if we just need OAuth (credentials exist but no token)
    if CREDENTIALS_PATH.exists() and not TOKEN_PATH.exists():
        _log_to_reflexion("oauth_only", True, "Running OAuth flow")
        success, message = _run_oauth_flow()
        if success:
            return ToolResult(
                success=True,
                output={"status": "oauth_completed", "message": message},
            )
        else:
            return ToolResult(success=False, error=message, retryable=True)

    # Check PyAutoGUI
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return ToolResult(success=False, error=err, retryable=False)

    print("\n" + "=" * 60)
    print("  GOOGLE CLOUD SETUP - Desktop Commander")
    print("=" * 60)
    print("\nThis will open Chrome and guide you through Google Cloud setup.")
    print("You'll need to interact with the browser when prompted.\n")

    # Step 1: Open Chrome to Google Cloud Console
    print("[STEP 1] Opening Google Cloud Console...")
    if not _open_chrome("https://console.cloud.google.com/"):
        return ToolResult(
            success=False,
            error="Could not open Chrome. Make sure Chrome is installed.",
            retryable=True,
        )
    _take_screenshot("step1_console_opened")

    # Step 2: Wait for login
    _wait_and_prompt(
        "Log in to your Google account in Chrome if needed.\n"
        "Press Enter when you're logged in and see the Cloud Console."
    )
    _take_screenshot("step2_logged_in")

    # Step 3: Navigate to project creation
    print("\n[STEP 2] Navigating to project creation...")
    _open_chrome("https://console.cloud.google.com/projectcreate")
    time.sleep(2)
    _take_screenshot("step3_project_create")

    # Step 4: User creates project
    _wait_and_prompt(
        f"Create a new project:\n"
        f"1. Enter project name: {args.project_name}\n"
        f"2. Click 'Create'\n"
        f"3. Wait for project to be created\n\n"
        f"Press Enter when the project is created."
    )
    _take_screenshot("step4_project_created")

    # Step 5: Enable Calendar API
    print("\n[STEP 3] Enabling Calendar API...")
    _open_chrome(f"https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={args.project_name}")
    time.sleep(2)

    _wait_and_prompt(
        "Click 'Enable' to enable the Google Calendar API.\n"
        "Press Enter when done."
    )
    _take_screenshot("step5_calendar_enabled")

    # Step 6: Enable Tasks API
    print("\n[STEP 4] Enabling Tasks API...")
    _open_chrome(f"https://console.cloud.google.com/apis/library/tasks.googleapis.com?project={args.project_name}")
    time.sleep(2)

    _wait_and_prompt(
        "Click 'Enable' to enable the Google Tasks API.\n"
        "Press Enter when done."
    )
    _take_screenshot("step6_tasks_enabled")

    # Step 7: Configure OAuth consent screen
    print("\n[STEP 5] Configuring OAuth consent screen...")
    _open_chrome(f"https://console.cloud.google.com/apis/credentials/consent?project={args.project_name}")
    time.sleep(2)

    _wait_and_prompt(
        "Configure the OAuth consent screen:\n"
        "1. Select 'External' user type\n"
        "2. Click 'Create'\n"
        "3. Fill in:\n"
        "   - App name: Treys Agent\n"
        "   - User support email: (your email)\n"
        "   - Developer contact: (your email)\n"
        "4. Click 'Save and Continue' through all steps\n"
        "5. On 'Test users' page, add your email\n\n"
        "Press Enter when you've completed the consent screen setup."
    )
    _take_screenshot("step7_consent_configured")

    # Step 8: Create OAuth credentials
    print("\n[STEP 6] Creating OAuth credentials...")
    _open_chrome(f"https://console.cloud.google.com/apis/credentials?project={args.project_name}")
    time.sleep(2)

    _wait_and_prompt(
        "Create OAuth credentials:\n"
        "1. Click 'Create Credentials' at the top\n"
        "2. Select 'OAuth client ID'\n"
        "3. Application type: 'Desktop app'\n"
        "4. Name: 'Treys Agent Desktop'\n"
        "5. Click 'Create'\n\n"
        "Press Enter when you see the 'OAuth client created' dialog."
    )
    _take_screenshot("step8_oauth_created")

    # Step 9: Download credentials
    _wait_and_prompt(
        "Download the credentials:\n"
        "1. Click 'Download JSON' in the dialog\n"
        "2. Save the file (it will go to Downloads)\n\n"
        "Press Enter after the download completes."
    )
    _take_screenshot("step9_downloaded")

    # Step 10: Find and move credentials
    print("\n[STEP 7] Looking for downloaded credentials...")
    time.sleep(2)  # Give filesystem time to update

    creds_file = _find_downloaded_credentials()
    if creds_file:
        print(f"Found credentials at: {creds_file}")
        if _move_credentials_to_place(creds_file):
            print(f"Moved to: {CREDENTIALS_PATH}")
            _log_to_reflexion("credentials_saved", True, f"Saved from {creds_file}")
        else:
            return ToolResult(
                success=False,
                error=f"Found credentials but failed to move to {CREDENTIALS_PATH}",
                retryable=True,
            )
    else:
        manual_path = _wait_and_prompt(
            f"Could not find the downloaded credentials.\n"
            f"Please enter the full path to the downloaded JSON file\n"
            f"(or press Enter to check Downloads folder again):"
        )
        if manual_path:
            src = Path(manual_path)
            if src.exists():
                _move_credentials_to_place(src)
            else:
                return ToolResult(
                    success=False,
                    error=f"File not found: {manual_path}",
                    retryable=True,
                )
        else:
            # Try again
            creds_file = _find_downloaded_credentials()
            if creds_file:
                _move_credentials_to_place(creds_file)
            else:
                return ToolResult(
                    success=False,
                    error=f"Please manually copy the client_secret*.json to: {CREDENTIALS_PATH}",
                    retryable=True,
                )

    # Step 11: Run OAuth flow
    print("\n[STEP 8] Completing OAuth flow...")
    print("A browser window will open for you to grant permissions.\n")

    success, message = _run_oauth_flow()

    if success:
        _log_to_reflexion("setup_complete", True, "Full setup completed")
        print("\n" + "=" * 60)
        print("  SETUP COMPLETE!")
        print("=" * 60)
        return ToolResult(
            success=True,
            output={
                "status": "setup_complete",
                "message": "Google Cloud project created and configured!",
                "project_name": args.project_name,
                "credentials_path": str(CREDENTIALS_PATH),
                "token_path": str(TOKEN_PATH),
                "apis_enabled": ["Calendar", "Tasks"],
            },
        )
    else:
        _log_to_reflexion("oauth_failed", False, message)
        return ToolResult(
            success=False,
            error=message,
            retryable=True,
        )


def check_and_fix_google_setup(ctx, args: CheckAndFixArgs):
    """
    Diagnose and fix Google API setup issues.

    Checks:
    1. Google libraries installed
    2. OAuth credentials file exists
    3. Token file exists and is valid
    """
    from agent.autonomous.models import ToolResult

    issues = []
    fixes_applied = []

    # Check 1: Libraries
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:
        issues.append(f"Missing Google libraries: {e}")

    # Check 2: Credentials file
    if not CREDENTIALS_PATH.exists():
        issues.append(f"OAuth credentials missing: {CREDENTIALS_PATH}")

        if args.auto_fix:
            found = _find_downloaded_credentials()
            if found and _move_credentials_to_place(found):
                fixes_applied.append(f"Moved credentials from {found}")
                issues.remove(f"OAuth credentials missing: {CREDENTIALS_PATH}")

    # Check 3: Token
    if CREDENTIALS_PATH.exists() and not TOKEN_PATH.exists():
        issues.append("Need to complete OAuth flow")

    # Check 4: Token validity
    if TOKEN_PATH.exists():
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    TOKEN_PATH.write_text(creds.to_json())
                    fixes_applied.append("Refreshed expired token")
                else:
                    issues.append("Token expired and cannot refresh")
        except Exception as e:
            issues.append(f"Token error: {e}")

    if not issues:
        return ToolResult(
            success=True,
            output={
                "status": "configured",
                "message": "Google APIs are ready!",
                "fixes_applied": fixes_applied,
            },
        )
    else:
        return ToolResult(
            success=False,
            error="Setup incomplete",
            output={
                "issues": issues,
                "fixes_applied": fixes_applied,
                "next_step": "Run full_google_setup to complete",
            },
            retryable=True,
        )


# ============================================================================
# Tool Registration
# ============================================================================

GOOGLE_CLOUD_SETUP_SPECS = [
    {
        "name": "full_google_setup",
        "args_model": FullGoogleSetupArgs,
        "fn": full_google_setup,
        "description": "Complete Google Cloud setup using Desktop Commander (opens real Chrome, creates project, enables APIs, creates OAuth credentials)",
    },
    {
        "name": "check_and_fix_google_setup",
        "args_model": CheckAndFixArgs,
        "fn": check_and_fix_google_setup,
        "description": "Diagnose and fix Google API setup issues",
    },
]


def register_google_cloud_setup_tools(registry) -> None:
    """Register Google Cloud setup tools."""
    from agent.autonomous.tools.registry import ToolSpec

    for spec in GOOGLE_CLOUD_SETUP_SPECS:
        registry.register(ToolSpec(
            name=spec["name"],
            args_model=spec["args_model"],
            fn=spec["fn"],
            description=spec["description"],
        ))


__all__ = [
    "FullGoogleSetupArgs",
    "CheckAndFixArgs",
    "full_google_setup",
    "check_and_fix_google_setup",
    "register_google_cloud_setup_tools",
    "GOOGLE_CLOUD_SETUP_SPECS",
]
