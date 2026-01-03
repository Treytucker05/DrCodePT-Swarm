#!/usr/bin/env python3
"""
Quick command to check Google Calendar.

Usage:
    python check_calendar.py
"""
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.commands.check_calendar import main

if __name__ == "__main__":
    main()
