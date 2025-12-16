# DrCodePT-Swarm Agent Guide

- You are running with: `desktop` (PyAutoGUI) and `playwright` MCP servers, plus web search.
- Default behavior: prefer Playwright for anything in a browser; fall back to `desktop` for OS/windows outside the browser.
- For natural-language requests:
  - If context is unclear, first call `desktop/screenshot` (or `playwright/screenshot` when a Playwright page is open) to see the UI.
  - Use text/aria selectors in Playwright before resorting to pixel coordinates.
  - After each meaningful action, take another screenshot to verify state.
  - Ask for confirmation only when an action looks destructive (delete, submit, purchase, irreversible changes).
- Never ask the user for coordinates; choose them from the screenshot yourself.
- Keep outputs concise; summarize what you did and what you need next (if anything) before ending the turn.
