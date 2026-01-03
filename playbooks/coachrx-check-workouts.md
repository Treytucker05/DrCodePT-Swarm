# CoachRX - Check Workouts Needed for Clients

## Purpose
Check which clients need workouts created in CoachRX.

## Prerequisites
- Credentials saved: `Cred: coachrx`
- Logged into CoachRX dashboard

## Steps
1. Navigate to https://dashboard.coachrx.app/
2. Log in using saved credentials (if not already logged in)
3. Navigate to Clients section
4. Look for indicators of clients needing workouts (e.g., "Needs Workout", overdue dates, empty workout slots)
5. Extract list of clients who need workouts
6. Return client list with details

## Implementation Notes
- Uses browser automation with vision executor
- May need to click through client list or filter by status
- Look for visual indicators like badges, dates, or empty workout slots
- Return structured data: client name, last workout date, next workout due date

## Usage
```
Auto: check which clients need workouts in CoachRX
```

