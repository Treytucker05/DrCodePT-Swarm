import os
import json
from pathlib import Path
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

def get_google_creds() -> Optional[Credentials]:
    """Get or refresh Google OAuth2 credentials."""
    token_path = Path.home() / ".drcodept_swarm" / "google_calendar" / "token.json"
    creds = None
    
    if token_path.exists():
        try:
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception:
            pass
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(token_path, 'w') as f:
                    f.write(creds.to_json())
            except Exception:
                return None
        else:
            # Cannot automatically authorize in a headless agent
            # User must run setup_google_calendar.py manually
            return None
            
    return creds
