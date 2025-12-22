"""
Google OAuth Setup - Uses your regular Chrome browser (not Playwright)

This script authenticates with Google APIs and saves the token.
It opens your default browser for login, which Google won't block.

Usage:
1. First, get OAuth credentials from Google Cloud Console:
   - Go to https://console.cloud.google.com/apis/credentials
   - Create OAuth 2.0 Client ID (Desktop app type)
   - Download the JSON file
   - Save it as: agent/memory/google_client_secret.json

2. Run this script:
   python setup_google_auth.py
"""

import json
import os
import sys
import webbrowser
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing Google libraries. Installing...")
    os.system(f'"{sys.executable}" -m pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client')
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

CLIENT_SECRET_FILE = REPO_ROOT / "agent" / "memory" / "google_client_secret.json"
TOKEN_FILE = REPO_ROOT / "agent" / "memory" / "google_token.json"


def main():
    print("\n" + "="*50)
    print("  GOOGLE OAUTH SETUP")
    print("  Uses your regular browser (not Playwright)")
    print("="*50 + "\n")

    # Check for client secret file
    if not CLIENT_SECRET_FILE.exists():
        print(f"ERROR: Client secret file not found at:")
        print(f"  {CLIENT_SECRET_FILE}\n")
        print("To get this file:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create a project (if needed)")
        print("3. Enable APIs: Tasks, Gmail, Calendar")
        print("4. Create OAuth 2.0 Client ID (Desktop app)")
        print("5. Download JSON and save to:")
        print(f"   {CLIENT_SECRET_FILE}")
        print("\nOpening Google Cloud Console in your browser...")
        webbrowser.open("https://console.cloud.google.com/apis/credentials")
        return False

    creds = None
    
    # Check for existing token
    if TOKEN_FILE.exists():
        print(f"Found existing token at {TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"Could not load token: {e}")
            creds = None

    # If no valid creds, do the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Could not refresh token: {e}")
                creds = None

        if not creds:
            print("\nStarting OAuth flow...")
            print("Your DEFAULT BROWSER will open (Chrome, Edge, etc.)")
            print("Google won't block this like it blocks Playwright.\n")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE), SCOPES
            )
            
            # This opens the SYSTEM DEFAULT browser, not Playwright
            creds = flow.run_local_server(
                port=8080,
                prompt='consent',
                open_browser=True
            )

        # Save the token
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        print(f"\n✅ Token saved to: {TOKEN_FILE}")

    # Also save to credential store for the agent
    try:
        from agent.memory.credentials import save_credential
        save_credential('google_apis', 'token', creds.to_json())
        print("✅ Token also saved to agent credential store")
    except Exception as e:
        print(f"⚠️ Could not save to credential store: {e}")

    print("\n✅ Google OAuth setup complete!")
    print("You can now use Google Tasks, Gmail, and Calendar in the agent.")
    return True


if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
