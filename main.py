"""
Main application file
"""

from flask import Flask, redirect, request, session
import urllib.parse
import config

app = Flask(__name__)
app.secret_key = "dev-secret-key"

@app.route('/')
def index():
    return "Welcome to the app!"

@app.route('/oauth/start')
def oauth_start():
    # Start Google OAuth 2.0 flow
    if not config.OAUTH_CLIENT_ID or not config.OAUTH_REDIRECT_URI:
        return "OAuth not configured: missing client ID or redirect URI", 500

    params = {
        "client_id": config.OAUTH_CLIENT_ID,
        "redirect_uri": config.OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(config.GOOGLE_CALENDAR_SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return redirect(auth_url)

@app.route('/oauth/callback')
def oauth_callback():
    # TODO: Handle OAuth callback (exchange code for tokens)
    code = request.args.get("code")
    if not code:
        return "Missing authorization code", 400
    return "OAuth callback received code; token exchange not implemented yet"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
