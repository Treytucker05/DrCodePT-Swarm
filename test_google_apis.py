"""Quick test of Google APIs integration"""
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.integrations.google_apis import list_calendar_events, list_tasks

print("=" * 70)
print("  TESTING GOOGLE APIS INTEGRATION")
print("=" * 70)

print("\n1. Testing Google Calendar...")
try:
    events = list_calendar_events(calendar_id='primary', max_results=10)
    if events:
        print(f"   ✓ Found {len(events)} events:")
        for i, event in enumerate(events[:5], 1):
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'No date'))
            print(f"     {i}. {event.get('summary', 'No title')} - {start}")
    else:
        print("   ✓ No events found (but connection works)")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing Google Tasks...")
try:
    tasks = list_tasks(max_results=10)
    if tasks:
        print(f"   ✓ Found {len(tasks)} tasks:")
        for i, task in enumerate(tasks[:5], 1):
            print(f"     {i}. {task.get('title', 'No title')}")
    else:
        print("   ✓ No tasks found (but connection works)")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("  TEST COMPLETE")
print("=" * 70)
