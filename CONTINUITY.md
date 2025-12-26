Goal (incl. success criteria):
- Implement MCP-based Google Calendar + Tasks integration (client, helpers, tools, registry, treys_agent startup/shutdown) plus tests/scripts per spec.

Constraints/Assumptions:
- Use local MCP servers config in `agent/mcp/servers.json` with Windows paths.
- Keep MCPClient compatible with current helpers/tools.
- Use explicit phase banners in replies and start with Ledger Snapshot.

Key decisions:
- Replace `agent/mcp/client.py` with the provided placeholder multi-server implementation.
- Update helpers/tests to use `call_tool` and `list_tools`.
- Initialize calendar/tasks MCP client during tool registry setup.

State:
  - Done:
    - Updated `agent/mcp/client.py` to match the provided spec.
    - Updated calendar/tasks helpers to use `call_tool` and added update/delete event + task helpers.
    - Added update/delete calendar/task tool wrappers and registry entries.
    - Updated tests and integration script to use `list_tools`, and aligned test file with pytest_asyncio fixtures.
    - Initialized calendar/tasks MCP client in builtins registry setup.
    - Ran `python -m py_compile` on updated modules.
    - Ran `python -m pytest -q tests/test_calendar_tasks_integration.py` (5 skipped).
  - Now:
    - Ready for any additional file updates or commit/push.
  - Next:
    - Commit/push if requested.

Open questions (UNCONFIRMED if needed):
- None.

Working set (files/ids/commands):
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent\mcp\client.py`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent\integrations\calendar_helper.py`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent\integrations\tasks_helper.py`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent\autonomous\tools\calendar_tasks_tools.py`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent\autonomous\tools\registry.py`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\agent\autonomous\tools\builtins.py`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\tests\test_calendar_tasks_integration.py`
- `C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\test_integration.py`
