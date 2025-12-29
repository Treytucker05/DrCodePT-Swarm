"""
Google APIs Integration for Tasks, Gmail, and Calendar.

This module provides OAuth2-based access to Google APIs:
- Google Tasks API
- Gmail API
- Google Calendar API

Setup:
1. Run playbook: setup google apis
2. Authenticate via browser (OAuth2)
3. Credentials saved to agent/memory/credential_store.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Google API libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCOPES = [
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

def get_credentials() -> Optional[Credentials]:
    """Get or refresh Google API credentials."""
    from agent.memory.credentials import get_credential
    
    creds_data = get_credential('google_apis')
    if not creds_data:
        return None
    
    token_data = (
        creds_data.get('token')
        or creds_data.get('password')  # token is stored in password for google_apis
    )
    if not token_data:
        return None

    try:
        token_payload = json.loads(token_data)
    except Exception:
        return None

    creds = Credentials.from_authorized_user_info(token_payload, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        from agent.memory.credentials import save_credential
        save_credential('google_apis', 'token', json.dumps({
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }))
    
    return creds

def list_tasks(tasklist_id: str = '@default', max_results: int = 10) -> List[Dict[str, Any]]:
    """List tasks from Google Tasks."""
    creds = get_credentials()
    if not creds:
        raise ValueError("No Google API credentials found. Run: setup google apis")
    
    try:
        service = build('tasks', 'v1', credentials=creds)
        results = service.tasks().list(tasklist=tasklist_id, maxResults=max_results).execute()
        items = results.get('items', [])
        return items
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def create_task(title: str, notes: str = '', due: str = '', tasklist_id: str = '@default') -> Dict[str, Any]:
    """Create a new task in Google Tasks."""
    creds = get_credentials()
    if not creds:
        raise ValueError("No Google API credentials found. Run: setup google apis")
    
    task = {'title': title}
    if notes:
        task['notes'] = notes
    if due:
        task['due'] = due
    
    try:
        service = build('tasks', 'v1', credentials=creds)
        result = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
        return result
    except HttpError as error:
        print(f'An error occurred: {error}')
        return {}

def update_task(task_id: str, title: str = None, notes: str = None, status: str = None, tasklist_id: str = '@default') -> Dict[str, Any]:
    """Update an existing task in Google Tasks."""
    creds = get_credentials()
    if not creds:
        raise ValueError("No Google API credentials found. Run: setup google apis")
    
    task = {}
    if title:
        task['title'] = title
    if notes:
        task['notes'] = notes
    if status:
        task['status'] = status
    
    try:
        service = build('tasks', 'v1', credentials=creds)
        result = service.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
        return result
    except HttpError as error:
        print(f'An error occurred: {error}')
        return {}

def list_gmail_messages(query: str = '', max_results: int = 10) -> List[Dict[str, Any]]:
    """List Gmail messages matching query."""
    creds = get_credentials()
    if not creds:
        raise ValueError("No Google API credentials found. Run: setup google apis")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        detailed_messages = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            detailed_messages.append(msg_data)
        
        return detailed_messages
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def list_calendar_events(calendar_id: str = 'primary', max_results: int = 10) -> List[Dict[str, Any]]:
    """List upcoming calendar events."""
    creds = get_credentials()
    if not creds:
        raise ValueError("No Google API credentials found. Run: setup google apis")
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        from datetime import datetime
        now = datetime.utcnow().isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return events
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def create_calendar_event(summary: str, start_time: str, end_time: str, description: str = '', calendar_id: str = 'primary') -> Dict[str, Any]:
    """Create a new calendar event."""
    creds = get_credentials()
    if not creds:
        raise ValueError("No Google API credentials found. Run: setup google apis")
    
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'America/New_York'},
        'end': {'dateTime': end_time, 'timeZone': 'America/New_York'},
    }
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return event
    except HttpError as error:
        print(f'An error occurred: {error}')
        return {}

__all__ = [
    'get_credentials',
    'list_tasks',
    'create_task',
    'update_task',
    'list_gmail_messages',
    'list_calendar_events',
    'create_calendar_event'
]
