# Agent Improvements - Mail Organization & Simple Questions

## Changes Made

### 1. Simple Question Answering
The agent now detects and directly answers simple questions instead of going into autonomous mode.

**Supported patterns:**
- "Do you have X?" - Checks if Python package X is installed
- "Is X installed?" - Checks if package/command X is installed
- Questions ending with "?"

**Examples:**
```
> Do you have googleapi?
[NO] googleapi is not installed.
[TIP] To install it, run: pip install googleapi

> Do you have google-api-python-client?
[YES] google-api-python-client is installed (version 2.187.0)

> Is pip installed?
[YES] pip is installed (version 25.3)
```

### 2. Automatic Mail Mode Routing
Mail organization tasks are now automatically detected and routed to the **supervised mail mode** instead of autonomous mode.

**Why this matters:**
- The supervised mail mode is **interactive** - it prompts you at each step
- It won't make changes without your approval
- It shows you statistics and lets you choose what to organize
- The autonomous mode was getting stuck because it tried to do everything automatically

**Detected patterns:**
- "organize my mail/email/inbox"
- "clean my mail/email/inbox"
- "organize my yahoo/gmail folders"
- Any query with mail/email/folder keywords

**Examples:**
```
> organize my yahoo mail folders
[Routes to Mail: supervised mode]

> clean my yahoo inbox
[Routes to Mail: supervised mode]

> help me organize my email
[Routes to Mail: supervised mode]
```

### 3. How to Use Mail Organization

**Option 1: Natural language (now auto-detected)**
```
> organize my yahoo mail folders
> clean my yahoo inbox
> help me organize my email
```

**Option 2: Explicit Mail: prefix (always worked)**
```
> Mail: review my Yahoo inbox and suggest rules
```

**What happens:**
1. Agent connects to your Yahoo mail via IMAP
2. Prompts you to select folders to scan
3. Shows you statistics (top senders, domains)
4. Asks which senders are important/spam
5. Suggests folder organization
6. **Asks for your approval before making any changes**
7. Only moves/organizes what you approve

## Files Modified
- `agent/treys_agent.py` - Added simple question handling and mail intent detection

## Testing
All changes have been tested and verified working.
