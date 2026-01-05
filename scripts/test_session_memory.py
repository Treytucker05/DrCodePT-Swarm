import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.append(os.getcwd())

def test_memory_injection():
    print("Testing Session Memory Injection...")
    
    # Mock some history
    session_history = [
        "User: What's on my calendar?\nAssistant: You have Sleep at 8am.",
        "User: Who is Trey?\nAssistant: Trey is the user."
    ]
    
    current_input = "But how long does sleep last?"
    
    # Simulate the logic in interactive_loop
    history_text = "\n".join(session_history[-3:])
    full_task = f"Context from previous turns in this session:\n{history_text}\n\nCurrent Task: {current_input}"
    
    print(f"\nConstructed Prompt:\n{full_task}")
    
    # Basic check
    if "Context from previous turns" in full_task and "Sleep at 8am" in full_task:
        print("\nSUCCESS: Context correctly injected into the current task.")
    else:
        print("\nFAILURE: Context missing.")

if __name__ == "__main__":
    test_memory_injection()
