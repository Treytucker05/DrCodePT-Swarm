from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.skills.google_calendar import GoogleCalendarSkill
from agent.skills.base import AuthStatus


def main() -> int:
    skill = GoogleCalendarSkill()
    status = skill.auth_status()

    if status == AuthStatus.NOT_CONFIGURED:
        print(skill.setup_guide())
        return 0

    if status in {AuthStatus.NEEDS_AUTH, AuthStatus.AUTH_EXPIRED}:
        print("Starting Google OAuth flow...")
        skill.begin_oauth()
        status = skill.auth_status()

    if status not in {AuthStatus.AUTHENTICATED, AuthStatus.AUTH_EXPIRED}:
        print("Google Calendar authentication failed.")
        print(skill.setup_guide())
        return 1

    result = skill.list_tomorrow_events()
    if not result.ok:
        print(f"Error: {result.error}")
        if result.needs_auth:
            print(skill.setup_guide())
        return 1

    events = result.data or []
    if not events:
        print("No events found for tomorrow.")
        return 0

    print("Tomorrow's events:")
    for event in events:
        start = event.get("start", {})
        when = start.get("dateTime") or start.get("date") or "unknown time"
        summary = event.get("summary", "Untitled")
        print(f"- {summary} at {when}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
