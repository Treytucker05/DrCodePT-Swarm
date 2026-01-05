import sys
import os
from pathlib import Path
from datetime import datetime

# Add agent to path
sys.path.append(os.getcwd())

from agent.cli import _interpret_calendar_date

def test_interpretation():
    print("Testing Calendar Interpretation...")
    
    # Test 1: "Tomorrow"
    print("\n--- Test 1: Tomorrow ---")
    res = _interpret_calendar_date("what is on my calendar tomorrow?")
    print(f"Result: {res}")
    
    # Verify time_min is actually tomorrow local time
    if res and res.get("time_min"):
        dt = datetime.fromisoformat(res["time_min"])
        print(f"Parsed Time: {dt}")
        now = datetime.now().astimezone()
        print(f"Now: {now}")
        days_diff = (dt.date() - now.date()).days
        if days_diff == 1:
            print("SUCCESS: Date is correctly tomorrow.")
        else:
            print(f"FAILURE: Expected 1 day diff, got {days_diff}")
    else:
        print("FAILURE: No result from LLM.")

    # Test 2: "Personal Calendar"
    print("\n--- Test 2: Personal Calendar ---")
    res = _interpret_calendar_date("show my personal calendar events")
    print(f"Result: {res}")
    
    if res and res.get("calendar_filter") == ["personal"]:
        print("SUCCESS: Filter correctly identified as ['personal']")
    else:
        print(f"FAILURE: Expected ['personal'], got {res.get('calendar_filter')}")

if __name__ == "__main__":
    try:
        test_interpretation()
    except Exception as e:
        print(f"Test failed with error: {e}")
