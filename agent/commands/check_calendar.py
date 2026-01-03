"""
End-to-end Google Calendar check command.

Handles:
1. Checking for credentials
2. Creating OAuth client via Google Console if needed
3. Running OAuth flow to get token
4. Listing calendar events
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Paths
DRCODEPT_DIR = Path.home() / ".drcodept_swarm"
GOOGLE_DIR = DRCODEPT_DIR / "google_calendar"
CREDENTIALS_PATH = GOOGLE_DIR / "credentials.json"
TOKEN_PATH = GOOGLE_DIR / "token.json"


def check_credentials() -> Tuple[bool, str]:
    """Check if OAuth credentials exist."""
    if not CREDENTIALS_PATH.exists():
        return False, f"Credentials not found: {CREDENTIALS_PATH}"

    try:
        with CREDENTIALS_PATH.open('r') as f:
            data = json.load(f)

        # Verify structure
        if "installed" not in data and "web" not in data:
            return False, "Invalid credentials.json structure"

        return True, "Credentials found"
    except Exception as e:
        return False, f"Failed to read credentials: {e}"


def check_token() -> Tuple[bool, str]:
    """Check if OAuth token exists and is valid."""
    if not TOKEN_PATH.exists():
        return False, f"Token not found: {TOKEN_PATH}"

    try:
        with TOKEN_PATH.open('r') as f:
            data = json.load(f)

        # Check for required fields
        if "token" not in data and "access_token" not in data:
            return False, "Invalid token.json structure"

        return True, "Token found"
    except Exception as e:
        return False, f"Failed to read token: {e}"


def create_credentials_via_console(on_step: Optional[callable] = None) -> Tuple[bool, str]:
    """Create OAuth credentials through Google Console automation."""
    logger.info("Creating OAuth credentials via Google Console...")

    try:
        from agent.autonomous.google_console_flow import create_oauth_credentials

        # Ensure directory exists
        GOOGLE_DIR.mkdir(parents=True, exist_ok=True)

        # Run the flow
        success, message = create_oauth_credentials(
            destination_path=CREDENTIALS_PATH,
            on_step=on_step
        )

        if success:
            logger.info(f"✓ {message}")
        else:
            logger.error(f"✗ {message}")

        return success, message

    except Exception as e:
        return False, f"OAuth creation failed: {e}"


def run_oauth_flow() -> Tuple[bool, str]:
    """Run OAuth local server flow to create token."""
    logger.info("Running OAuth flow to get token...")

    try:
        # Import Google auth libraries
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

        creds = None

        # Check if token exists
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired token...")
                creds.refresh(Request())
            else:
                logger.info("Starting OAuth flow (browser will open)...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_PATH),
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials
            with TOKEN_PATH.open('w') as f:
                f.write(creds.to_json())
            logger.info(f"✓ Token saved to {TOKEN_PATH}")

        return True, "OAuth flow completed successfully"

    except ImportError as e:
        return False, f"Missing required library: {e}. Run: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    except Exception as e:
        return False, f"OAuth flow failed: {e}"


def list_calendar_events(max_results: int = 10) -> Tuple[bool, str]:
    """List upcoming calendar events."""
    logger.info("Fetching calendar events...")

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from datetime import datetime, timezone

        # Load credentials
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_PATH),
            ['https://www.googleapis.com/auth/calendar.readonly']
        )

        # Build service
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.now(timezone.utc).isoformat()
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            return True, "No upcoming events found"

        # Format events
        output = [f"Upcoming events ({len(events)}):"]
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No title')
            output.append(f"  • {start}: {summary}")

        return True, "\n".join(output)

    except ImportError as e:
        return False, f"Missing required library: {e}"
    except Exception as e:
        return False, f"Failed to list events: {e}"


def check_calendar(
    auto_setup: bool = True,
    on_step: Optional[callable] = None
) -> Tuple[bool, str]:
    """
    Main entrypoint: check Google Calendar with automatic setup if needed.

    Args:
        auto_setup: If True, automatically create credentials and token if missing
        on_step: Optional callback for progress updates

    Returns:
        (success, message)
    """
    # Step 1: Check credentials
    has_creds, creds_msg = check_credentials()
    logger.info(f"Credentials check: {creds_msg}")

    if not has_creds:
        if not auto_setup:
            return False, "Credentials missing and auto_setup=False"

        # Create credentials via console automation
        success, msg = create_credentials_via_console(on_step=on_step)
        if not success:
            return False, f"Failed to create credentials: {msg}"

    # Step 2: Check token
    has_token, token_msg = check_token()
    logger.info(f"Token check: {token_msg}")

    if not has_token:
        if not auto_setup:
            return False, "Token missing and auto_setup=False"

        # Run OAuth flow
        success, msg = run_oauth_flow()
        if not success:
            return False, f"Failed to get token: {msg}"

    # Step 3: List events
    success, events_msg = list_calendar_events()
    if not success:
        return False, f"Failed to list events: {events_msg}"

    return True, events_msg


def main():
    """CLI entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )

    print("=" * 60)
    print("  Google Calendar Check")
    print("=" * 60)
    print()

    success, message = check_calendar(auto_setup=True)

    print()
    if success:
        print("✓ SUCCESS")
        print()
        print(message)
    else:
        print("✗ FAILED")
        print()
        print(message)
        sys.exit(1)


if __name__ == "__main__":
    main()


__all__ = [
    "check_calendar",
    "check_credentials",
    "check_token",
    "create_credentials_via_console",
    "run_oauth_flow",
    "list_calendar_events",
]
