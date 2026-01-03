# Blackboard - Track Assignments and Due Dates

## Purpose
Extract assignment information from Blackboard courses, track due dates, and optionally sync to Google Calendar/Tasks.

## Prerequisites
- Credentials saved: `Cred: blackboard`
- Google Calendar/Tasks set up (optional, for syncing)
- Logged into Blackboard (UTMB)

## Steps
1. Navigate to https://utmb.blackboard.com/
2. Log in using saved credentials (if not already logged in)
3. Navigate to Courses page
4. For each course:
   - Open the course
   - Navigate to Assignments section
   - Extract assignment details:
     - Assignment name
     - Due date/time
     - Points/grade weight
     - Description/instructions
     - Submission type
5. Store assignments in structured format (JSON file or database)
6. Optionally sync to Google Calendar/Tasks:
   - Create calendar events for due dates
   - Create tasks for assignments

## Data Structure
```json
{
  "assignments": [
    {
      "course": "Course Name",
      "assignment_name": "Assignment Title",
      "due_date": "2025-01-15T23:59:59",
      "points": 100,
      "description": "Assignment description",
      "submission_type": "Online",
      "status": "not_started",
      "synced_to_calendar": false,
      "synced_to_tasks": false
    }
  ]
}
```

## Storage Location
- `agent/memory/blackboard_assignments.json` (or similar)
- Update on each run
- Compare with previous run to detect new assignments

## Calendar/Tasks Sync
- Create calendar event for due date (1 day before due date)
- Create Google Task with assignment details
- Link task to calendar event (if possible)

## Implementation Notes
- Parse assignment tables/lists from Blackboard pages
- Extract dates and convert to ISO format
- Handle different assignment types (discussions, quizzes, papers, etc.)
- Update existing assignments if details change
- Mark completed assignments (if status available)

## Usage
```
Auto: track my Blackboard assignments
Auto: sync Blackboard assignments to my calendar
Auto: show me assignments due this week from Blackboard
```

