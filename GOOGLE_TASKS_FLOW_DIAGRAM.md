# Google Tasks Fast Path - Visual Flow Diagram

## Complete Execution Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                     USER TYPES QUERY                                │
│   "what workouts do I need to make"                                │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│                  STEP 1: DETECTION                                  │
│   File: cli.py:422-438                                             │
│   Function: _is_google_calendar_or_tasks_query()                   │
│                                                                     │
│   Keywords checked:                                                │
│   - tasks: ✗                                                       │
│   - workout: ✓ MATCH!                                              │
│   - calendar: ✗                                                    │
│                                                                     │
│   Time: 0.001 seconds                                              │
└────────────────────────────────────────────────────────────────────┘
                              ↓ YES
┌────────────────────────────────────────────────────────────────────┐
│               STEP 2: FAST PATH ENTRY                               │
│   File: cli.py:517-666                                             │
│   Function: _handle_google_fast_path()                             │
│                                                                     │
│   Action: Check for OAuth token                                    │
│   Path: ~/.drcodept_swarm/google_calendar/token.json              │
│   Status: ✓ Found                                                  │
│                                                                     │
│   Time: 0.01 seconds                                               │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│              STEP 3: BUILD GOOGLE API CLIENT                        │
│                                                                     │
│   1. Load token.json contents                                      │
│   2. Create Credentials object                                     │
│   3. Build Google Tasks API service                                │
│                                                                     │
│   Time: 0.1 seconds                                                │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│              STEP 4: FETCH ALL TASK LISTS                           │
│                                                                     │
│   API Call: service.tasklists().list().execute()                   │
│                                                                     │
│   Response:                                                        │
│   ┌──────────────────────────────────────┐                        │
│   │ "Reclaim"       (id: abc123)         │                        │
│   │ "To do"         (id: def456)         │                        │
│   │ "Workouts"      (id: ghi789)         │                        │
│   │ "My Tasks"      (id: jkl012)         │                        │
│   └──────────────────────────────────────┘                        │
│                                                                     │
│   Time: 0.3 seconds                                                │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│              STEP 5: LLM BRAIN INTERPRETATION                       │
│   File: cli.py:441-514                                             │
│   Function: _interpret_task_query()                                │
│                                                                     │
│   Input to LLM:                                                    │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │ User request: "what workouts do I need to make"           │   │
│   │                                                            │   │
│   │ Available lists:                                           │   │
│   │ - "Reclaim"                                                │   │
│   │ - "To do"                                                  │   │
│   │ - "Workouts"                                               │   │
│   │ - "My Tasks"                                               │   │
│   │                                                            │   │
│   │ Analyze and return JSON with:                             │   │
│   │ - action: list_all | list_specific | filter_by_keyword    │   │
│   │ - list_name: specific list or null                        │   │
│   │ - filter_keyword: keyword or null                         │   │
│   └──────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│   LLM Response:                                                    │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │ {                                                          │   │
│   │   "action": "list_specific",                              │   │
│   │   "list_name": "Workouts",                                │   │
│   │   "filter_keyword": null,                                 │   │
│   │   "interpretation": "User wants Workouts list"            │   │
│   │ }                                                          │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│   Time: 5.0 seconds (LLM) OR 0.01 seconds (fallback)              │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│            STEP 6: FETCH ALL TASKS FROM ALL LISTS                   │
│                                                                     │
│   For each list:                                                   │
│   API Call: service.tasks().list(tasklist=list_id).execute()       │
│                                                                     │
│   Results:                                                         │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │ [To do] (4 tasks)                                          │   │
│   │   - Sell Car                (status: needsAction)          │   │
│   │   - Fix car                 (status: needsAction)          │   │
│   │   - Taxes                   (status: needsAction)          │   │
│   │   - Get Diet going          (status: needsAction)          │   │
│   │                                                            │   │
│   │ [Workouts] (3 tasks)                                       │   │
│   │   - Heather add in CrossFit (status: needsAction)          │   │
│   │   - Maria                   (status: needsAction)          │   │
│   │   - My GPP workout          (status: needsAction)          │   │
│   │                                                            │   │
│   │ [My Tasks] (0 tasks)                                       │   │
│   │                                                            │   │
│   │ [Reclaim] (2 tasks - COMPLETED, filtered out)             │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│   Total active tasks: 7                                            │
│   Time: 0.5 seconds                                                │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│              STEP 7: APPLY LLM FILTERS                              │
│   File: cli.py:586-603                                             │
│                                                                     │
│   LLM said: action = "list_specific", list_name = "Workouts"       │
│                                                                     │
│   Filtering logic:                                                 │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │ if action == "list_specific" and list_name:               │   │
│   │     Keep only tasks where:                                │   │
│   │       task['_list_title'] == "Workouts"                   │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│   Filtered results:                                                │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │ [Workouts] (3 tasks)                                       │   │
│   │   - Heather add in CrossFit style                          │   │
│   │   - Maria                                                  │   │
│   │   - My GPP workout                                         │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│   Time: 0.001 seconds                                              │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│              STEP 8: DISPLAY RESULTS                                │
│   File: cli.py:597-633                                             │
│                                                                     │
│   Output to terminal:                                              │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │ [TASK] what workouts do I need to make                    │   │
│   │ [UNDERSTANDING] User wants Workouts list                  │   │
│   │ [ANSWER] Your Active Google Tasks (3 found):              │   │
│   │                                                            │   │
│   │   [Workouts] (3 tasks):                                   │   │
│   │      1. Heather add in CrossFit style                     │   │
│   │      2. Maria                                              │   │
│   │      3. My GPP workout                                     │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                     │
│   Time: 0.001 seconds                                              │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│                      ✓ DONE!                                        │
│                                                                     │
│   Total Time: ~6 seconds                                           │
│                                                                     │
│   Breakdown:                                                       │
│   - Detection:        0.001s                                       │
│   - Load token:       0.01s                                        │
│   - Build service:    0.1s                                         │
│   - Fetch lists:      0.3s                                         │
│   - LLM brain:        5.0s                                         │
│   - Fetch tasks:      0.5s                                         │
│   - Filter:           0.001s                                       │
│   - Display:          0.001s                                       │
│                                                                     │
│   vs Learning Agent: 30-60 seconds                                 │
│   Speed improvement: 5-10x faster!                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## Alternative Path: Keyword Fallback (if LLM times out)

```
┌─────────────────────────────────────────┐
│   STEP 5 (FALLBACK): KEYWORD MATCHING   │
│   Time: 0.01 seconds                    │
│                                         │
│   Query: "what workouts do I need"      │
│                                         │
│   Check list names:                     │
│   - "reclaim" in query? ✗               │
│   - "to do" in query? ✗                 │
│   - "workout" in query? ✓ MATCH!        │
│                                         │
│   Decision:                             │
│   {                                     │
│     "action": "list_specific",          │
│     "list_name": "Workouts",            │
│     "interpretation": "Showing Workouts"│
│   }                                     │
└─────────────────────────────────────────┘
                ↓
         (continues to Step 6)

Total time with fallback: ~0.9 seconds
```

---

## Code Structure Map

```
agent/cli.py
│
├── _is_google_calendar_or_tasks_query()  [lines 422-438]
│   └── Detection: keywords → boolean
│
├── _interpret_task_query()  [lines 441-514]
│   ├── LLM prompt → structured JSON
│   └── Fallback: keyword matching
│
└── _handle_google_fast_path()  [lines 517-666]
    ├── Load OAuth token
    ├── Build Google API service
    ├── Fetch all lists
    ├── Call _interpret_task_query()
    ├── Fetch all tasks
    ├── Apply filters
    └── Display results

interactive_loop()  [lines 669+]
    └── if _is_google_calendar_or_tasks_query():
            _handle_google_fast_path()
```

---

## Data Flow: Detailed

```
User Input String
    ↓
[Detection]
    ↓
Boolean: is_google_query
    ↓ (if True)
[Load Token]
    ↓
OAuth Credentials Object
    ↓
[Build Service]
    ↓
Google Tasks API Service Object
    ↓
[Fetch Lists]
    ↓
List of TaskList Objects
[{id, title}, {id, title}, ...]
    ↓
[LLM Interpretation]
    ↓
Decision Object
{action, list_name, filter_keyword, interpretation}
    ↓
[Fetch Tasks]
    ↓
List of Task Objects
[{title, notes, status, _list_title}, ...]
    ↓
[Apply Filters]
    ↓
Filtered List of Tasks
    ↓
[Group by List]
    ↓
Dictionary of Lists
{"Workouts": [task1, task2, task3]}
    ↓
[Display]
    ↓
Terminal Output
```

---

## Integration with CLI

```
┌─────────────────────────────────────────────────────┐
│          interactive_loop() Entry Point              │
└─────────────────────────────────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │ Get user input       │
         │ user_input = input() │
         └──────────────────────┘
                    ↓
         ┌──────────────────────────────────────────┐
         │ Check: Is this a Google Calendar/Tasks   │
         │ query?                                    │
         │                                           │
         │ if _is_google_calendar_or_tasks_query()  │
         └──────────────────────────────────────────┘
                    ↓
              YES          NO
               ↓            ↓
    ┌──────────────────┐  ┌─────────────────────────┐
    │ Fast Path        │  │ Other paths:            │
    │ ~6 seconds       │  │ - Learning Agent (30s)  │
    │                  │  │ - Simple queries        │
    │ if success:      │  │ - AgentRunner          │
    │   continue       │  └─────────────────────────┘
    │ else:            │
    │   fall through → │──→ Learning Agent
    └──────────────────┘
```

---

This visual guide shows exactly how your query flows through the system!
