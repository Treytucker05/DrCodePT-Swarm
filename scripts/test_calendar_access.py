
import asyncio
from agent.integrations.calendar_helper import CalendarHelper

async def test_access():
    print("Initializing CalendarHelper...")
    helper = CalendarHelper()
    try:
        print("Checking service...")
        helper._check_service()
        print("Listing events for next 24 hours...")
        from datetime import datetime, timedelta
        now = datetime.utcnow().isoformat() + "Z"
        tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
        events = await helper.list_events(now, tomorrow)
        print(f"Success! Found {len(events)} events.")
        for e in events:
            print(f" - {e.get('summary')} at {e.get('start', {}).get('dateTime')}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_access())
