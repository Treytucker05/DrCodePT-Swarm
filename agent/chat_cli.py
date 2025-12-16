from __future__ import annotations

"""
Terminal chat client for DrCodePT.

Usage:
    python -m agent.chat_cli "your question"
    python -m agent.chat_cli   # enters interactive mode

Offline-only: returns local summaries (no API calls).
"""

import sys

from agent.chat_engine import chat_reply


def main():
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
        print("You:", msg)
        print("Assistant:", chat_reply(msg))
        return

    print("DrCodePT chat (type 'exit' to quit)")
    while True:
        try:
            msg = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if msg.lower() in {"exit", "quit"}:
            print("Bye.")
            break
        print("Assistant:", chat_reply(msg))


if __name__ == "__main__":
    main()
