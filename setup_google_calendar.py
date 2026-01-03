"""
Quick Google Calendar/Tasks Setup

This will authorize the agent to access your Google Calendar and Tasks.
It only needs to be run once.
"""
import json
from pathlib import Path

# Paths
CREDS_FILE = Path.home() / ".drcodept_swarm" / "google_calendar" / "credentials.json"
TOKEN_FILE = Path.home() / ".drcodept_swarm" / "google_calendar" / "token.json"

print("=" * 70)
print("  GOOGLE CALENDAR/TASKS SETUP")
print("=" * 70)

# Check if credentials exist
if not CREDS_FILE.exists():
    print(f"\nError: credentials.json not found at: {CREDS_FILE}")
    print("\nPlease download OAuth credentials from Google Cloud Console first.")
    print("See: manual_oauth_setup.py")
    exit(1)

print(f"\n✓ Found credentials.json at: {CREDS_FILE}")

# Authorize
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("\nError: Google API libraries not installed")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

creds = None

# Check if we already have a token
if TOKEN_FILE.exists():
    print(f"✓ Found existing token at: {TOKEN_FILE}")
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

# If there are no (valid) credentials, let the user log in
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        print("\n→ Refreshing expired token...")
        creds.refresh(Request())
    else:
        print("\n→ Starting OAuth authorization flow...")
        print("   A browser window will open for you to authorize access.")
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
        creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f"✓ Token saved to: {TOKEN_FILE}")

# Test the connection
print("\n→ Testing connection to Google Calendar...")
try:
    service = build('calendar', 'v3', credentials=creds)
    events_result = service.events().list(calendarId='primary', maxResults=5).execute()
    events = events_result.get('items', [])
    print(f"✓ Successfully connected! Found {len(events)} upcoming events.")
except Exception as e:
    print(f"✗ Error testing connection: {e}")

print("\n→ Testing connection to Google Tasks...")
try:
    service = build('tasks', 'v1', credentials=creds)
    results = service.tasks().list(tasklist='@default', maxResults=5).execute()
    tasks = results.get('items', [])
    print(f"✓ Successfully connected! Found {len(tasks)} tasks.")
except Exception as e:
    print(f"✗ Error testing connection: {e}")

print("\n" + "=" * 70)
print("  SETUP COMPLETE!")
print("=" * 70)
print(f"\nYou can now use:")
print(f"  python -m agent.cli 'check my google calendar'")
print(f"  python -m agent.cli 'show my google tasks'")
print("=" * 70)
