# Integration Setup Guide

This guide documents the core integrations that have been set up for the agent.

## Overview

The agent now has integrations for:
1. **Google Calendar & Tasks** - MCP-based integration
2. **CoachRX** - Browser automation for workout management
3. **Yahoo Mail** - IMAP-based email management
4. **Blackboard** - Browser automation for course materials and assignments

## Google Calendar & Tasks

### Setup Status
- ✅ MCP servers configured in `agent/mcp/servers.json`
- ✅ Helper modules exist: `agent/integrations/calendar_helper.py`, `agent/integrations/tasks_helper.py`
- ⚠️ OAuth credentials needed: `credentials/gcp-oauth-credentials.json`

### Setup Instructions

1. **Create Google Cloud Project:**
   - Go to https://console.cloud.google.com
   - Create a new project (or use existing)
   - Enable "Google Calendar API" and "Google Tasks API"

2. **Create OAuth Credentials:**
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the JSON file
   - Save as: `credentials/gcp-oauth-credentials.json`

3. **Test Integration:**
   ```bash
   python scripts/test_google_integrations.py
   ```

4. **Usage:**
   - Calendar events: The agent can list, create, update, and delete calendar events
   - Tasks: The agent can list, create, update, complete, and search tasks
   - Integration with other services (e.g., Blackboard assignments → Calendar/Tasks)

## CoachRX

### Setup Status
- ✅ Login playbook created: `agent/memory/site_playbooks/coachrx.yaml`
- ✅ Workout checking playbook: `playbooks/coachrx-check-workouts.md`

### Setup Instructions

1. **Save Credentials:**
   ```
   Cred: coachrx
   ```
   Enter your CoachRX username/email and password.

2. **Test Login:**
   The agent can now log into CoachRX using browser automation.

3. **Usage:**
   - Login: Automatic when accessing CoachRX
   - Check workouts: "Auto: check which clients need workouts in CoachRX"
   - Navigation: The agent can navigate the CoachRX dashboard

### Notes
- Uses browser automation (no public API available)
- Login playbook uses generic selectors that should work with common login patterns
- May require 2FA/MFA authentication (agent will pause for user input)

## Yahoo Mail

### Setup Status
- ✅ IMAP integration: `agent/integrations/yahoo_mail.py`
- ✅ Login playbook: `agent/memory/site_playbooks/yahoo.yaml`
- ✅ Cleanup playbooks exist: `agent/playbooks/index.json` (yahoo-clean-spam)
- ✅ Mail tools: `agent/autonomous/tools/mail.py`

### Setup Instructions

1. **Generate App Password:**
   - Log into your Yahoo account
   - Go to Account Security settings
   - Generate an "App Password" (not your regular password)
   - Save this app password

2. **Save Credentials:**
   ```
   Cred: yahoo_imap
   ```
   Enter your Yahoo email and the app password.

3. **Test Integration:**
   ```bash
   python scripts/test_yahoo_imap.py
   ```

4. **Usage:**
   - Clean spam: "clean yahoo spam" or "empty spam"
   - Organize folders: "organize my yahoo mail folders"
   - List messages: Mail tool supports list, read, send, folder management
   - Browser automation also available for complex workflows

### Available Functions
- List folders and messages
- Read messages
- Send messages (with confirmation)
- Create/delete/rename folders
- Move messages by sender/domain
- Clean spam folder (browser automation)

## Blackboard (UTMB)

### Setup Status
- ✅ Login playbook: `agent/memory/site_playbooks/blackboard.yaml`
- ✅ Download materials playbook: `playbooks/blackboard-download-materials.md`
- ✅ Assignment tracking playbook: `playbooks/blackboard-track-assignments.md`

### Setup Instructions

1. **Save Credentials:**
   ```
   Cred: blackboard
   ```
   Enter your UTMB username and password.

2. **Test Login:**
   The agent can now log into Blackboard using browser automation.

3. **Usage:**
   - Login: Automatic when accessing Blackboard
   - Download materials: "Auto: download materials from my Blackboard courses"
   - Track assignments: "Auto: track my Blackboard assignments"
   - Sync to calendar: "Auto: sync Blackboard assignments to my calendar"

### Notes
- Uses browser automation (Blackboard REST API requires institutional setup)
- Login redirects through UTMB Web Login Service (idp.utmb.edu)
- May require Duo/2FA authentication (agent will pause for user input)
- Session typically lasts ~12 hours

### Assignment Tracking
- Extracts assignments with due dates from courses
- Stores assignment data in structured format
- Can sync to Google Calendar and Google Tasks
- Tracks assignment status and updates

## Testing All Integrations

### Quick Test Scripts

1. **Google Calendar/Tasks:**
   ```bash
   python scripts/test_google_integrations.py
   ```

2. **Yahoo Mail:**
   ```bash
   python scripts/test_yahoo_imap.py
   ```

3. **CoachRX & Blackboard:**
   - Test via agent commands (browser automation)
   - Credentials must be saved first

### Integration Test Checklist

- [ ] Google Calendar/Tasks credentials set up and tested
- [ ] CoachRX credentials saved and login tested
- [ ] Yahoo Mail IMAP credentials saved and tested
- [ ] Blackboard credentials saved and login tested
- [ ] All playbooks load correctly
- [ ] Browser automation works for CoachRX and Blackboard

## Usage Examples

### Google Calendar
```
Check my calendar for tomorrow
Create a calendar event for PT exam on January 20th at 2pm
List my upcoming events
```

### Google Tasks
```
Show me my tasks
Create a task: Study for anatomy exam
Mark task [id] as complete
```

### CoachRX
```
Log into CoachRX and check which clients need workouts
Show me my client list in CoachRX
```

### Yahoo Mail
```
Clean my Yahoo spam
Organize my Yahoo mail folders
List my recent emails
```

### Blackboard
```
Download materials from my Blackboard courses
Track my Blackboard assignments
Sync my Blackboard assignments to my calendar
Show me assignments due this week
```

## Troubleshooting

### Google Calendar/Tasks
- **Issue:** "Credentials file not found"
  - **Solution:** Download OAuth credentials from Google Cloud Console and save to `credentials/gcp-oauth-credentials.json`
- **Issue:** "Authentication failed"
  - **Solution:** Re-authenticate by running the OAuth flow again

### CoachRX/Blackboard
- **Issue:** "No credentials stored"
  - **Solution:** Run `Cred: coachrx` or `Cred: blackboard` to save credentials
- **Issue:** Login playbook fails
  - **Solution:** The playbook may need updating if the site structure changed. Use browser automation to record a new login flow.

### Yahoo Mail
- **Issue:** "IMAP login failed"
  - **Solution:** Make sure you're using an app password, not your regular Yahoo password
- **Issue:** "Credentials not found"
  - **Solution:** Run `Cred: yahoo_imap` to save credentials

## Next Steps

1. Set up credentials for all services you want to use
2. Test each integration individually
3. Try the usage examples above
4. Create custom workflows combining multiple integrations (e.g., Blackboard assignments → Google Calendar)

## Files Created/Modified

### New Files
- `scripts/test_google_integrations.py` - Google Calendar/Tasks test script
- `scripts/test_yahoo_imap.py` - Yahoo Mail IMAP test script
- `agent/memory/site_playbooks/coachrx.yaml` - CoachRX login playbook
- `agent/memory/site_playbooks/blackboard.yaml` - Blackboard login playbook
- `playbooks/coachrx-check-workouts.md` - CoachRX workout checking playbook
- `playbooks/blackboard-download-materials.md` - Blackboard download playbook
- `playbooks/blackboard-track-assignments.md` - Blackboard assignment tracking playbook
- `INTEGRATION_SETUP_GUIDE.md` - This file

### Existing Files (Verified)
- `agent/mcp/servers.json` - MCP server configuration (already configured)
- `agent/integrations/calendar_helper.py` - Calendar helper (already exists)
- `agent/integrations/tasks_helper.py` - Tasks helper (already exists)
- `agent/integrations/yahoo_mail.py` - Yahoo Mail IMAP integration (already exists)
- `agent/memory/site_playbooks/yahoo.yaml` - Yahoo login playbook (already exists)
- `playbooks/blackboard-login.md` - Blackboard login playbook (already exists, converted to YAML)

