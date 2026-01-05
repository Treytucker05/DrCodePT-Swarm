"""
Unit tests for Google Calendar and Tasks integration.
"""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio

from agent.mcp.client import MCPClient
from agent.integrations.calendar_helper import CalendarHelper
from agent.integrations.tasks_helper import TasksHelper

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def mcp_client():
    """Create and initialize MCP client."""
    client = MCPClient()
    await client.initialize(["google-calendar", "google-tasks"])
    yield client
    await client.shutdown()


@pytest_asyncio.fixture
async def calendar_helper(mcp_client):
    """Create calendar helper."""
    return CalendarHelper(mcp_client)


@pytest_asyncio.fixture
async def tasks_helper(mcp_client):
    """Create tasks helper."""
    return TasksHelper(mcp_client)


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initialization."""
    client = MCPClient()
    assert client is not None
    assert len(client.servers) > 0
    await client.shutdown()


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools."""
    client = MCPClient()
    await client.initialize(["google-calendar", "google-tasks"])

    tools = client.list_tools()
    assert len(tools) > 0

    calendar_tools = client.list_tools("google-calendar")
    assert len(calendar_tools) > 0

    tasks_tools = client.list_tools("google-tasks")
    assert len(tasks_tools) > 0

    await client.shutdown()


@pytest.mark.asyncio
async def test_calendar_helper_initialization(calendar_helper):
    """Test calendar helper initialization."""
    assert calendar_helper is not None
    assert calendar_helper.client is not None


@pytest.mark.asyncio
async def test_tasks_helper_initialization(tasks_helper):
    """Test tasks helper initialization."""
    assert tasks_helper is not None
    assert tasks_helper.client is not None


@pytest.mark.asyncio
async def test_list_calendar_events(calendar_helper):
    """Test listing calendar events."""
    now = datetime.utcnow()
    end = now + timedelta(days=7)

    result = await calendar_helper.list_events(
        now.isoformat() + "Z",
        end.isoformat() + "Z",
    )

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_create_calendar_event(calendar_helper):
    """Test creating a calendar event."""
    now = datetime.utcnow()
    start = now + timedelta(hours=1)
    end = start + timedelta(hours=1)

    result = await calendar_helper.create_event(
        title="Test Event",
        start_time=start.isoformat() + "Z",
        end_time=end.isoformat() + "Z",
        description="Test event for integration testing",
    )

    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_list_tasks(tasks_helper):
    """Test listing tasks."""
    result = await tasks_helper.list_all_tasks()

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_create_task(tasks_helper):
    """Test creating a task."""
    result = await tasks_helper.create_task(
        title="Test Task",
        notes="Test task for integration testing",
    )

    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_search_tasks(tasks_helper):
    """Test searching tasks."""
    result = await tasks_helper.search_tasks("test")

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_calendar_tasks_tools_initialization(calendar_helper, tasks_helper):
    """Test CalendarTasksTools initialization."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    assert tools is not None
    assert tools.calendar is not None
    assert tools.tasks is not None


@pytest.mark.asyncio
async def test_get_free_time(calendar_helper, tasks_helper):
    """Test get_free_time tool."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    result = await tools.get_free_time_async(duration_minutes=60, days_ahead=7)

    assert isinstance(result, dict)
    assert "success" in result


@pytest.mark.asyncio
async def test_check_calendar_conflicts(calendar_helper, tasks_helper):
    """Test check_calendar_conflicts tool."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    now = datetime.utcnow()
    start = now + timedelta(hours=1)
    end = start + timedelta(hours=1)

    result = await tools.check_calendar_conflicts_async(
        event_title="Test Event",
        start_time=start.isoformat() + "Z",
        end_time=end.isoformat() + "Z",
    )

    assert isinstance(result, dict)
    assert "success" in result


@pytest.mark.asyncio
async def test_create_calendar_event_tool(calendar_helper, tasks_helper):
    """Test create_calendar_event tool."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    now = datetime.utcnow()
    start = now + timedelta(hours=1)
    end = start + timedelta(hours=1)

    result = await tools.create_calendar_event_async(
        title="Test Event",
        start_time=start.isoformat() + "Z",
        end_time=end.isoformat() + "Z",
        description="Test event",
    )

    assert isinstance(result, dict)
    assert "success" in result


@pytest.mark.asyncio
async def test_list_calendar_events_tool(calendar_helper, tasks_helper):
    """Test list_calendar_events tool."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    now = datetime.utcnow()
    end = now + timedelta(days=7)

    result = await tools.list_calendar_events_async(
        time_min=now.isoformat() + "Z",
        time_max=end.isoformat() + "Z",
    )

    assert isinstance(result, dict)
    assert "success" in result


@pytest.mark.asyncio
async def test_list_all_tasks_tool(calendar_helper, tasks_helper):
    """Test list_all_tasks tool."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    result = await tools.list_all_tasks_async()

    assert isinstance(result, dict)
    assert "success" in result


@pytest.mark.asyncio
async def test_create_task_tool(calendar_helper, tasks_helper):
    """Test create_task tool."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    result = await tools.create_task_async(
        title="Test Task",
        notes="Test task",
    )

    assert isinstance(result, dict)
    assert "success" in result


@pytest.mark.asyncio
async def test_search_tasks_tool(calendar_helper, tasks_helper):
    """Test search_tasks tool."""
    from agent.autonomous.tools.calendar_tasks_tools import CalendarTasksTools

    tools = CalendarTasksTools(calendar_helper, tasks_helper)
    result = await tools.search_tasks_async("test")

    assert isinstance(result, dict)
    assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
