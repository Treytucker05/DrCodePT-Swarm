"""
Google API Setup Tool - Autonomous OAuth setup with learning.

This tool handles the full flow of setting up Google API access:
1. Checks if credentials already exist
2. Researches setup steps if needed (using web_search)
3. Guides user through OAuth flow via browser
4. Stores OAuth tokens securely
5. Learns from failures via reflexion

The agent can use this to self-configure when asked about calendar, tasks, etc.
"""
from __future__ import annotations

import json
import logging
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Paths for OAuth credentials
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_PATH = REPO_ROOT / "agent" / "integrations" / "google_credentials.json"
TOKEN_PATH = REPO_ROOT / "agent" / "memory" / "google_token.json"

# Google OAuth scopes we need
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/gmail.readonly',
]


class SetupGoogleArgs(BaseModel):
    """Arguments for setting up Google API access."""
    force_reauth: bool = Field(
        default=False,
        description="Force re-authentication even if credentials exist"
    )
    scopes: Optional[List[str]] = Field(
        default=None,
        description="Specific scopes to request (defaults to calendar, tasks, gmail)"
    )


class CheckGoogleStatusArgs(BaseModel):
    """Arguments for checking Google API status."""
    pass


def _check_google_libs() -> tuple[bool, str]:
    """Check if Google API libraries are installed."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        return True, "OK"
    except ImportError as e:
        return False, str(e)


def _get_existing_credentials():
    """Get existing OAuth credentials if they exist and are valid."""
    if not TOKEN_PATH.exists():
        return None, "No token file found"

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), GOOGLE_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed token
                    TOKEN_PATH.write_text(creds.to_json())
                    return creds, "Credentials refreshed"
                except Exception as e:
                    return None, f"Failed to refresh: {e}"
            return None, "Credentials invalid or expired"

        return creds, "Credentials valid"
    except Exception as e:
        return None, f"Error loading credentials: {e}"


def _save_credentials(creds) -> bool:
    """Save OAuth credentials to token file."""
    try:
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
        return True
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        return False


def _run_oauth_flow(scopes: List[str]) -> tuple[Any, str]:
    """Run the OAuth flow to get new credentials."""
    if not CREDENTIALS_PATH.exists():
        return None, (
            f"OAuth client credentials not found at {CREDENTIALS_PATH}. "
            "You need to create a Google Cloud project and download OAuth client credentials. "
            "Would you like me to guide you through this process?"
        )

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH),
            scopes
        )

        # Run local server flow (opens browser)
        creds = flow.run_local_server(port=0)

        # Save the credentials
        if _save_credentials(creds):
            return creds, "OAuth flow completed successfully"
        else:
            return creds, "OAuth succeeded but failed to save token"

    except Exception as e:
        return None, f"OAuth flow failed: {e}"


def _log_to_reflexion(action: str, success: bool, details: str) -> None:
    """Log setup attempts to reflexion for learning."""
    try:
        from agent.autonomous.memory.reflexion import ReflexionEntry, write_reflexion
        from uuid import uuid4

        entry = ReflexionEntry(
            id=f"google_setup_{uuid4().hex[:8]}",
            timestamp=datetime.utcnow().isoformat() + "Z",
            objective="Setup Google API OAuth credentials",
            context_fingerprint="google_apis_setup",
            phase=action,
            tool_calls=[{"tool": "setup_google_apis", "action": action}],
            errors=[] if success else [details],
            reflection=f"Google API setup {'succeeded' if success else 'failed'}: {details}",
            fix=action if success else f"Need to: {details}",
            outcome="success" if success else "failure",
            tags=["google", "oauth", "setup", "calendar"],
        )
        write_reflexion(entry)
    except Exception as e:
        logger.debug(f"Could not write to reflexion: {e}")


def check_google_status(ctx, args: CheckGoogleStatusArgs):
    """
    Check if Google APIs are set up and working.

    Returns status info about:
    - Required libraries installed
    - OAuth credentials present
    - Token valid/expired
    """
    from agent.autonomous.models import ToolResult

    status = {
        "libraries_installed": False,
        "oauth_credentials_file": False,
        "token_file": False,
        "token_valid": False,
        "needs_setup": True,
        "setup_steps": [],
    }

    # Check libraries
    libs_ok, libs_msg = _check_google_libs()
    status["libraries_installed"] = libs_ok
    if not libs_ok:
        status["setup_steps"].append(
            "Install Google API libraries: pip install google-auth google-auth-oauthlib google-api-python-client"
        )

    # Check OAuth credentials file
    status["oauth_credentials_file"] = CREDENTIALS_PATH.exists()
    if not CREDENTIALS_PATH.exists():
        status["setup_steps"].append(
            f"Create Google Cloud OAuth credentials and save to {CREDENTIALS_PATH}"
        )

    # Check token file
    status["token_file"] = TOKEN_PATH.exists()

    # Check if token is valid
    if libs_ok and TOKEN_PATH.exists():
        creds, msg = _get_existing_credentials()
        status["token_valid"] = creds is not None
        status["token_status"] = msg
    else:
        status["token_status"] = "No token file"

    # Determine if setup is needed
    status["needs_setup"] = not (
        status["libraries_installed"] and
        status["oauth_credentials_file"] and
        status["token_valid"]
    )

    if not status["needs_setup"]:
        status["setup_steps"] = ["Setup complete - Google APIs are ready to use"]

    return ToolResult(
        success=True,
        output=status,
    )


def setup_google_apis(ctx, args: SetupGoogleArgs):
    """
    Set up Google API access with OAuth.

    This tool handles the complete setup flow:
    1. Checks if libraries are installed
    2. Checks if OAuth credentials file exists
    3. Runs OAuth flow if needed
    4. Stores tokens securely

    If OAuth credentials file is missing, it will guide you through creating one.
    """
    from agent.autonomous.models import ToolResult

    scopes = args.scopes or GOOGLE_SCOPES

    # Step 1: Check libraries
    libs_ok, libs_msg = _check_google_libs()
    if not libs_ok:
        _log_to_reflexion("check_libs", False, libs_msg)
        return ToolResult(
            success=False,
            error=(
                "Google API libraries not installed. Please run:\n"
                "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            ),
            retryable=True,
            metadata={"step": "check_libs"},
        )

    # Step 2: Check existing credentials (unless force_reauth)
    if not args.force_reauth:
        creds, msg = _get_existing_credentials()
        if creds:
            _log_to_reflexion("use_existing", True, msg)
            return ToolResult(
                success=True,
                output={
                    "status": "already_configured",
                    "message": "Google API access is already configured and working",
                    "token_status": msg,
                },
            )

    # Step 3: Check for OAuth credentials file
    if not CREDENTIALS_PATH.exists():
        _log_to_reflexion("check_oauth_file", False, "OAuth credentials file not found")

        guide = """
Google OAuth credentials file not found. To set up:

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable APIs: Calendar, Tasks, Gmail
4. Go to "APIs & Services" > "Credentials"
5. Click "Create Credentials" > "OAuth client ID"
6. Choose "Desktop app" as application type
7. Download the JSON file
8. Save it to: {path}

Would you like me to open the Google Cloud Console in your browser?
""".format(path=CREDENTIALS_PATH)

        return ToolResult(
            success=False,
            error=guide,
            retryable=True,
            metadata={
                "step": "need_oauth_file",
                "credentials_path": str(CREDENTIALS_PATH),
                "action_needed": "download_oauth_credentials",
            },
        )

    # Step 4: Run OAuth flow
    try:
        creds, msg = _run_oauth_flow(scopes)

        if creds:
            _log_to_reflexion("oauth_flow", True, msg)
            return ToolResult(
                success=True,
                output={
                    "status": "setup_complete",
                    "message": "Google API access configured successfully!",
                    "scopes": scopes,
                    "token_saved": str(TOKEN_PATH),
                },
            )
        else:
            _log_to_reflexion("oauth_flow", False, msg)
            return ToolResult(
                success=False,
                error=msg,
                retryable=True,
                metadata={"step": "oauth_flow"},
            )

    except Exception as e:
        _log_to_reflexion("oauth_flow", False, str(e))
        return ToolResult(
            success=False,
            error=f"OAuth flow failed: {e}",
            retryable=True,
            metadata={"step": "oauth_flow", "exception": str(e)},
        )


def open_google_console(ctx, args):
    """Open Google Cloud Console in the default browser."""
    from agent.autonomous.models import ToolResult

    try:
        webbrowser.open("https://console.cloud.google.com/apis/credentials")
        return ToolResult(
            success=True,
            output={"message": "Opened Google Cloud Console in browser"},
        )
    except Exception as e:
        return ToolResult(
            success=False,
            error=f"Failed to open browser: {e}",
        )


# Tool specs for registry
GOOGLE_SETUP_TOOL_SPECS = [
    {
        "name": "check_google_status",
        "args_model": CheckGoogleStatusArgs,
        "fn": check_google_status,
        "description": "Check if Google APIs (Calendar, Tasks, Gmail) are set up and working",
    },
    {
        "name": "setup_google_apis",
        "args_model": SetupGoogleArgs,
        "fn": setup_google_apis,
        "description": "Set up Google API access with OAuth (calendar, tasks, gmail)",
    },
]


def register_google_setup_tools(registry) -> None:
    """Register Google setup tools with a ToolRegistry."""
    from agent.autonomous.tools.registry import ToolSpec

    for spec in GOOGLE_SETUP_TOOL_SPECS:
        registry.register(ToolSpec(
            name=spec["name"],
            args_model=spec["args_model"],
            fn=spec["fn"],
            description=spec["description"],
        ))


__all__ = [
    "SetupGoogleArgs",
    "CheckGoogleStatusArgs",
    "check_google_status",
    "setup_google_apis",
    "register_google_setup_tools",
    "GOOGLE_SETUP_TOOL_SPECS",
    "CREDENTIALS_PATH",
    "TOKEN_PATH",
]
