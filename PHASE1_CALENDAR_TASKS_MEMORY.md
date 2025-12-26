# Phase 1 Implementation Plan: Calendar + Tasks + Memory MCP

## Goal
Add Google Calendar, Google Tasks, and Memory MCP to DrCodePT-Swarm for automated PT school management.

---

## Installation Steps

### 1. Google Calendar MCP Setup ⏰

**Best Option:** `@cocal/google-calendar-mcp` (814 stars, most popular)

**Features:**
- Multi-account support (personal + work calendars)
- Multi-calendar support
- Cross-account conflict detection
- Free/busy queries
- Smart scheduling with natural language
- Import events from images/PDFs
- Recurring events management

**Installation:**

```bash
# Install the MCP server globally
npm install -g @cocal/google-calendar-mcp

# OR use npx (no install needed)
# It will be called via npx in agent config
```

**Google Cloud Setup:**
1. Go to https://console.cloud.google.com
2. Create new project: "DrCodePT-Calendar"
3. Enable "Google Calendar API"
4. Create OAuth 2.0 credentials:
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" type
   - Download JSON credentials
   - Save as `gcp-oauth-calendar.keys.json`
5. Add test users (your email) during development

**Agent Configuration:**

Add to `agent/mcp/servers.json`:
```json
{
  "google-calendar": {
    "command": "npx",
    "args": [
      "-y",
      "@cocal/google-calendar-mcp"
    ],
    "env": {
      "GOOGLE_OAUTH_CREDENTIALS": "C:\\Users\\treyt\\OneDrive\\Desktop\\DrCodePT-Swarm\\credentials\\gcp-oauth-calendar.keys.json"
    }
  }
}
```

**First-Time Authentication:**
```bash
# Set environment variable
set GOOGLE_OAUTH_CREDENTIALS=C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\credentials\gcp-oauth-calendar.keys.json

# Run authentication
npx @cocal/google-calendar-mcp auth
```

Browser will open for Google OAuth → Grant permissions → Token saved

---

### 2. Google Tasks MCP Setup ✅

**Best Option:** `@zcaceres/gtasks` (TypeScript, actively maintained)

**Features:**
- List all tasks
- Search tasks
- Create new tasks
- Update existing tasks
- Delete tasks
- Mark tasks complete/incomplete

**Installation:**

```bash
# Install the MCP server globally
npm install -g @zcaceres/gtasks

# OR clone and build locally (recommended for customization)
cd C:\Users\treyt\OneDrive\Desktop
git clone https://github.com/zcaceres/gtasks-mcp.git
cd gtasks-mcp
npm install
npm run build
```

**Google Cloud Setup:**
1. Go to https://console.cloud.google.com
2. Use SAME project: "DrCodePT-Calendar"
3. Enable "Google Tasks API"
4. Create OAuth 2.0 credentials (if not already done):
   - Choose "Desktop app" type
   - Download JSON credentials
   - Save as `gcp-oauth-tasks.keys.json`

**Agent Configuration:**

Add to `agent/mcp/servers.json`:
```json
{
  "google-tasks": {
    "command": "C:\\Program Files\\nodejs\\node.exe",
    "args": [
      "C:\\Users\\treyt\\OneDrive\\Desktop\\gtasks-mcp\\dist\\index.js"
    ],
    "env": {
      "GOOGLE_OAUTH_CREDENTIALS": "C:\\Users\\treyt\\OneDrive\\Desktop\\DrCodePT-Swarm\\credentials\\gcp-oauth-tasks.keys.json"
    }
  }
}
```

**First-Time Setup:**
Copy credentials file into gtasks-mcp directory:
```bash
cd C:\Users\treyt\OneDrive\Desktop\gtasks-mcp
copy C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\credentials\gcp-oauth-tasks.keys.json gcp-oauth.keys.json
```

Run authentication flow (first API call will trigger OAuth)

---

### 3. Memory MCP Setup 🧠

**Official Anthropic Server:** `@modelcontextprotocol/server-memory`

**Features:**
- Knowledge graph storage (entities + relations)
- Persistent across sessions
- Local SQLite database
- Structured knowledge relationships
- Searchable memory
- Privacy-first (all data local)

**Installation:**

```bash
# No installation needed, uses npx
# Memory will be stored in local SQLite database
```

**Agent Configuration:**

Add to `agent/mcp/servers.json`:
```json
{
  "memory": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-memory"
    ],
    "env": {
      "MEMORY_FILE_PATH": "C:\\Users\\treyt\\OneDrive\\Desktop\\DrCodePT-Swarm\\data\\agent-memory.jsonl"
    }
  }
}
```

**Directory Structure:**
```
DrCodePT-Swarm/
├── credentials/
│   ├── gcp-oauth-calendar.keys.json
│   └── gcp-oauth-tasks.keys.json
├── data/
│   └── agent-memory.jsonl  (auto-created)
└── agent/
    └── mcp/
        └── servers.json
```

---

## Integration with DrCodePT-Swarm

### Update MCP Client (`agent/mcp/client.py`)

**Current code handles filesystem only. Need to add:**

```python
# agent/mcp/client.py

class MCPClient:
    def __init__(self):
        # Existing code...
        self.available_tools = {}
        
    async def initialize(self):
        """Initialize all MCP servers"""
        servers = self._load_server_config()
        
        for server_name, server_config in servers.items():
            try:
                # Start server process
                session = await self._start_server(server_name, server_config)
                
                # List available tools from this server
                tools = await session.list_tools()
                
                # Register tools with namespace
                for tool in tools:
                    tool_name = f"{server_name}.{tool.name}"
                    self.available_tools[tool_name] = {
                        'session': session,
                        'tool': tool,
                        'server': server_name
                    }
                    
                logger.info(f"Loaded {len(tools)} tools from {server_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize {server_name}: {e}")
    
    async def call_tool(self, tool_name, arguments):
        """Call a tool from any MCP server"""
        if tool_name not in self.available_tools:
            # Try with server prefix
            if '.' not in tool_name:
                # Search for tool across all servers
                for full_name in self.available_tools:
                    if full_name.endswith(f".{tool_name}"):
                        tool_name = full_name
                        break
        
        if tool_name not in self.available_tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool_info = self.available_tools[tool_name]
        session = tool_info['session']
        tool = tool_info['tool']
        
        # Call the tool
        result = await session.call_tool(tool.name, arguments)
        return result
```

### Update Collaborative Mode (`agent/modes/collaborative.py`)

**Add tool listing to planning prompt:**

```python
# agent/modes/collaborative.py

async def _generate_plan(self, user_input: str, mcp_client) -> dict:
    """Generate execution plan with available tools"""
    
    # Get available tools
    available_tools = []
    for tool_name, tool_info in mcp_client.available_tools.items():
        tool_desc = tool_info['tool'].description
        available_tools.append(f"- {tool_name}: {tool_desc}")
    
    tools_list = "\n".join(available_tools)
    
    prompt = f"""
You are a planning assistant. Generate a step-by-step plan for this request.

USER REQUEST: {user_input}

AVAILABLE TOOLS:
{tools_list}

IMPORTANT:
- Google Calendar tools start with "google-calendar."
- Google Tasks tools start with "google-tasks."
- Memory tools start with "memory."
- Filesystem tools start with "filesystem."

Generate a plan with 1-3 steps maximum.
Each step should specify:
1. description: What to do
2. tool_name: Which tool to use (with server prefix)
3. tool_args: Arguments for the tool

Return ONLY valid JSON.
"""
    
    # Rest of planning logic...
```

---

## Usage Examples

### Calendar Operations

**Check availability:**
```
User: "What times am I free this week for a 1-hour meeting?"
Agent: [calls google-calendar.free_busy] → Returns free slots
```

**Add PT assignment deadline:**
```
User: "Add exam on Friday at 10am for Clinical Pathology"
Agent: [calls google-calendar.create_event] → Event created
```

**Find conflicts:**
```
User: "Do I have any conflicts between my gym schedule and PT classes?"
Agent: [calls google-calendar.check_conflicts] → Lists overlaps
```

### Task Operations

**List all tasks:**
```
User: "Show me all my incomplete tasks"
Agent: [calls google-tasks.list] → Returns task list
```

**Create task:**
```
User: "Remind me to review Anatomy chapter 5 by Wednesday"
Agent: [calls google-tasks.create] → Task created with due date
```

**Search tasks:**
```
User: "Find all tasks related to PT exams"
Agent: [calls google-tasks.search query="PT exam"] → Filtered results
```

### Memory Operations

**Store information:**
```
User: "Remember that I prefer to study PT material in the mornings"
Agent: [calls memory.create_entity] → Stores preference
```

**Retrieve context:**
```
User: "What do you remember about my study schedule?"
Agent: [calls memory.search] → Returns stored entities/relations
```

**Build knowledge graph:**
```
User: "I'm taking 5 PT courses: Legal Ethics, Lifespan Development, Clinical Pathology, Anatomy, and PT Exam Skills"
Agent: [calls memory.create_entities + memory.create_relations] 
       → Builds course entity graph
```

---

## Testing Plan

### Test 1: Calendar Integration
```bash
python -c "
import asyncio
from agent.mcp.client import MCPClient

async def test():
    client = MCPClient()
    await client.initialize()
    
    # List calendars
    result = await client.call_tool('google-calendar.list_calendars', {})
    print('Calendars:', result)
    
    # Get events for this week
    result = await client.call_tool('google-calendar.list_events', {
        'timeMin': '2025-12-26T00:00:00Z',
        'timeMax': '2026-01-02T00:00:00Z'
    })
    print('Events:', result)

asyncio.run(test())
"
```

### Test 2: Tasks Integration
```bash
python -c "
import asyncio
from agent.mcp.client import MCPClient

async def test():
    client = MCPClient()
    await client.initialize()
    
    # List all tasks
    result = await client.call_tool('google-tasks.list', {})
    print('Tasks:', result)
    
    # Create test task
    result = await client.call_tool('google-tasks.create', {
        'title': 'Test task from DrCodePT-Swarm',
        'notes': 'Testing MCP integration'
    })
    print('Created:', result)

asyncio.run(test())
"
```

### Test 3: Memory Integration
```bash
python -c "
import asyncio
from agent.mcp.client import MCPClient

async def test():
    client = MCPClient()
    await client.initialize()
    
    # Create entity
    result = await client.call_tool('memory.create_entity', {
        'name': 'Trey_Tucker',
        'entityType': 'person',
        'observations': ['First-year DPT student', 'Studies best in mornings']
    })
    print('Entity created:', result)
    
    # Search memory
    result = await client.call_tool('memory.search_nodes', {
        'query': 'Trey'
    })
    print('Memory search:', result)

asyncio.run(test())
"
```

---

## Rollout Schedule

**Week 1 (Dec 26 - Jan 1):**
- Day 1: Google Calendar MCP setup + authentication
- Day 2: Test calendar integration with agent
- Day 3: Google Tasks MCP setup + authentication
- Day 4: Test tasks integration with agent
- Day 5: Memory MCP setup
- Day 6: Test memory integration
- Day 7: End-to-end workflow test

**Week 2 (Jan 2 - Jan 8):**
- Build PT-specific playbooks using new tools
- Automate PT assignment deadline tracking
- Test collaborative planning with calendar/tasks
- Document usage patterns

**Week 3 (Jan 9+):**
- Production deployment
- Monitor error rates
- Optimize tool usage
- Collect feedback for improvements

---

## Success Metrics

**By end of Phase 1, agent should:**
1. ✅ Automatically check calendar for conflicts
2. ✅ Create tasks for PT assignments mentioned in conversation
3. ✅ Remember user preferences (study times, course info)
4. ✅ Suggest optimal study times based on calendar + preferences
5. ✅ Track all PT deadlines in Google Tasks
6. ✅ Build knowledge graph of PT courses and topics

**Quantifiable Goals:**
- 0 missed PT deadlines (automated tracking)
- 10+ hours saved per month on calendar management
- 90%+ accuracy on deadline extraction from Blackboard
- Memory retrieval working across sessions

---

## Troubleshooting Guide

### Issue: OAuth authentication fails
**Solution:**
1. Check credentials file path is absolute
2. Ensure Google Cloud project has correct APIs enabled
3. Add your email as test user in OAuth consent screen
4. Delete old token files and re-authenticate

### Issue: MCP server won't start
**Solution:**
1. Check Node.js version (18+)
2. Verify npx is in PATH
3. Check server.json syntax (valid JSON)
4. Look at agent logs for error messages

### Issue: Tool calls fail
**Solution:**
1. Check tool name includes server prefix (e.g., "google-calendar.list_events")
2. Verify arguments match tool schema
3. Check if token has expired (re-auth every 7 days in test mode)
4. Enable verbose logging in MCP client

---

## Files to Modify

1. `agent/mcp/servers.json` - Add 3 new server configs
2. `agent/mcp/client.py` - Add multi-server support
3. `agent/modes/collaborative.py` - Update planning with tool awareness
4. `agent/modes/execute_plan.py` - Add calendar/tasks/memory routing
5. `agent/treys_agent.py` - Initialize MCP client with all servers

## Files to Create

1. `credentials/gcp-oauth-calendar.keys.json` - OAuth credentials
2. `credentials/gcp-oauth-tasks.keys.json` - OAuth credentials
3. `data/agent-memory.jsonl` - Memory storage (auto-created)
4. `agent/integrations/calendar_helper.py` - Calendar utility functions
5. `agent/integrations/tasks_helper.py` - Tasks utility functions
6. `agent/integrations/memory_helper.py` - Memory utility functions

---

## Next Steps After Phase 1

**Phase 2: Blackboard Integration**
- Use calendar/tasks to auto-sync Blackboard deadlines
- Extract assignment details and create tasks automatically
- Set calendar reminders for upcoming due dates

**Phase 3: Study Workflow Automation**
- Use memory to track which topics studied
- Suggest study schedule based on calendar + memory
- Auto-generate Anki cards for studied topics

**Phase 4: Gym Business Automation**
- Separate calendar for gym events
- Client scheduling via Google Calendar
- Task management for gym operations

---

## Confidence Assessment

- **Calendar MCP setup:** 95% confident (well-documented, popular server)
- **Tasks MCP setup:** 90% confident (less mature but functional)
- **Memory MCP setup:** 98% confident (official Anthropic server)
- **Integration complexity:** 85% confident (requires MCP client refactoring)
- **Overall success:** 90% confident we can get this working in 1 week

---

## Resources

- Google Calendar MCP: https://github.com/nspady/google-calendar-mcp
- Google Tasks MCP: https://github.com/zcaceres/gtasks-mcp
- Memory MCP: https://github.com/modelcontextprotocol/servers/tree/main/src/memory
- MCP Specification: https://modelcontextprotocol.io
- Google Cloud Console: https://console.cloud.google.com
