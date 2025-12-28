# Configuration file for the application

import os

# Database settings
DATABASE_URL = "sqlite:///app.db"

# OAuth settings (read from environment)
# Set environment variables: GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, OAUTH_REDIRECT_URI
OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:5000/oauth/callback")

# Google Calendar API scopes
GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]
