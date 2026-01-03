# Fix Google OAuth 403 Error: "App is currently being tested"

## The Problem
You're seeing: `Error 403: access_denied` - "The app is currently being tested, and can only be accessed by developer-approved testers."

This happens because your Google Cloud OAuth consent screen is in "Testing" mode and your email (`treytucker05@yahoo.com`) isn't added as a test user.

## The Fix (2 minutes)

### Option 1: Add Yourself as a Test User (Recommended)

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Under "Test users", click **"+ ADD USERS"**
3. Add your email: `treytucker05@yahoo.com`
4. Click **Save**
5. Try authorization again: `python setup_google_calendar.py`

### Option 2: Publish the App (For Personal Use)

If you're the only user:

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Scroll down to "Publishing status"
3. Click **"PUBLISH APP"**
4. Confirm "Make External"
5. You'll see a warning - that's OK for personal use
6. Try authorization again: `python setup_google_calendar.py`

**Note**: For personal apps that only you use, publishing is safe. Google just warns you because it could be used by others.

## Quick Steps

The fastest way:

```bash
# 1. Open Google Cloud Console
start https://console.cloud.google.com/apis/credentials/consent

# 2. Add yourself as test user OR publish the app (see above)

# 3. Try setup again
python setup_google_calendar.py
```

## What This Does

- **Testing mode**: Only emails you explicitly add can authorize
- **Published mode**: Anyone with the link can authorize (but only you will have the link)
- Either works for personal use!

## After Fixing

Once you've added yourself as a test user or published the app:

1. Run: `python setup_google_calendar.py`
2. Browser will open for authorization
3. You might see "Google hasn't verified this app" - click **"Advanced" → "Go to Treys Agent (unsafe)"**
4. Click **"Allow"** to grant permissions
5. Done! Token will be saved

Then test:
```bash
python -m agent.cli "show my google tasks"
```

Should work instantly! 🚀
