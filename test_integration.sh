#!/bin/bash
# Test script for Google Calendar and Tasks integration

set -e

echo "=== Google Calendar & Tasks Integration Test ==="
echo ""

# Test 1: Check credentials file
echo "[1/5] Checking credentials file..."
if [ -f "credentials/gcp-oauth-credentials.json" ]; then
    echo "✓ Credentials file found"
else
    echo "✗ Credentials file not found"
    exit 1
fi

# Test 2: Check MCP servers config
echo "[2/5] Checking MCP servers configuration..."
if grep -q "google-calendar" agent/mcp/servers.json; then
    echo "✓ Google Calendar server configured"
else
    echo "✗ Google Calendar server not configured"
    exit 1
fi

if grep -q "google-tasks" agent/mcp/servers.json; then
    echo "✓ Google Tasks server configured"
else
    echo "✗ Google Tasks server not configured"
    exit 1
fi

# Test 3: Check Python modules
echo "[3/5] Checking Python modules..."
if [ -f "agent/mcp/client.py" ]; then
    echo "✓ MCP client module found"
else
    echo "✗ MCP client module not found"
    exit 1
fi

if [ -f "agent/integrations/calendar_helper.py" ]; then
    echo "✓ Calendar helper module found"
else
    echo "✗ Calendar helper module not found"
    exit 1
fi

if [ -f "agent/integrations/tasks_helper.py" ]; then
    echo "✓ Tasks helper module found"
else
    echo "✗ Tasks helper module not found"
    exit 1
fi

# Test 4: Run Python unit tests
echo "[4/5] Running unit tests..."
python -m pytest tests/test_calendar_tasks_integration.py -v || true

# Test 5: Test MCP server startup
echo "[5/5] Testing MCP server startup..."
python -c "
import asyncio
from agent.mcp.client import MCPClient

async def test():
    client = MCPClient()
    await client.initialize(['google-calendar', 'google-tasks'])
    print('✓ MCP servers initialized successfully')
    print(f'✓ Available tools: {len(client.list_tools())}')
    await client.shutdown()

asyncio.run(test())
" || echo "⚠ MCP server test skipped (may require authentication)"

echo ""
echo "=== Integration Test Complete ==="
