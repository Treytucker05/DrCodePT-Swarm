"""Test script to verify LearningAgent fixes work correctly."""
import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
load_dotenv()

from agent.autonomous.learning_agent import LearningAgent

def test_calendar_request():
    """Test that calendar request only sets up Calendar API, not Tasks."""
    print("=" * 60)
    print("Testing LearningAgent with calendar request")
    print("=" * 60)
    print()
    
    agent = LearningAgent()
    agent.initialize()
    
    # Set up status callback to see output
    def status_callback(msg: str):
        try:
            print(msg)
        except UnicodeEncodeError:
            # Handle Unicode (emojis) in Windows terminal
            print(msg.encode('ascii', errors='replace').decode('ascii'))
    
    agent.on_status = status_callback
    
    # Test request
    request = "check my google calendar and tell me what i have from 1-3 pm tomorrow"
    print(f"Request: {request}\n")
    
    result = agent.run(request)
    
    print("\n" + "=" * 60)
    print("Result:")
    print(f"  Success: {result.success}")
    print(f"  Summary: {result.summary}")
    if result.error:
        print(f"  Error: {result.error}")
    print("=" * 60)

if __name__ == "__main__":
    test_calendar_request()

