# Agent Improvements - Mail Organization & Simple Questions

**Status:** Historical/Archive. Do not update as a source of truth. See `AGENT_BEHAVIOR.md` and `conductor/tracks.md`.



Source of truth for agent behavior: `AGENT_BEHAVIOR.md`
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

### 2. Interactive Mail Organization (NEW!)
Mail organization now starts with an **interactive planning menu** instead of immediately scanning all folders.

**What's new:**
- **Planning menu** with 5 options when you start
- **Strategy discussion** before scanning
- **Folder creation** before organizing
- **Targeted scanning** (specific folders, spam hunting, etc.)
- **Optional AI conversation mode** for planning

**The new flow:**
```
> organize my yahoo mail folders

[Shows your current folders]

What would you like to do?
  1) Get a quick overview (scan recent messages)
  2) Deep dive into specific folders
  3) Plan a folder reorganization strategy
  4) Find and clean up spam/unwanted senders
  5) Custom - tell me what you need

Choose an option (1-5):
```

**Option 3 - Plan a folder reorganization strategy:**
- Asks about your goals
- Suggests strategies
- Lets you create folders first
- Then optionally scans to see what you have

**Option 4 - Find and clean up spam:**
- Focuses on finding unwanted senders
- Scans specific folder (default: INBOX)
- Shows top senders for you to mark as spam

### 3. AI-Powered Mail Planning (Optional)
Set `MAIL_USE_COLLAB=1` to enable conversational AI planning before organizing.

**How it works:**
```
> organize my yahoo mail folders

[MAIL COLLAB] Let's work together to organize your mail.

[ASSISTANT] I'd be happy to help you organize your Yahoo mail folders! 
To get started, could you tell me what's currently challenging about 
your folder organization? Are you dealing with too many folders, 
difficulty finding emails, or something else?

You: I have too many folders and don't know what to keep

[ASSISTANT] That's a common issue! Here's what I suggest:
1. First, let's identify which folders you actually use
2. Archive or delete folders you haven't touched in 6+ months
3. Consolidate similar folders (e.g., merge "Work" and "Work Projects")

Would you like to start by scanning your folders to see which ones 
have the most messages?

You: yes

[Launches supervised mail mode with your context]
```

### 4. Automatic Mail Mode Routing
Mail organization tasks are now automatically detected and routed to the **interactive mail mode**.

**Detected patterns:**
- "organize my mail/email/inbox"
- "clean my mail/email/inbox"
- "organize my yahoo/gmail folders"
- Any query with mail/email/folder keywords

**Examples:**
```
> organize my yahoo mail folders
[Routes to interactive Mail mode]

> clean my yahoo inbox
[Routes to interactive Mail mode]

> help me organize my email
[Routes to interactive Mail mode]
```

## How to Use

### Basic (Interactive Menu)
```
> organize my yahoo mail folders
```
Then choose from the menu what you want to do.

### With AI Planning (Conversational)
```bash
# In terminal, set environment variable:
set MAIL_USE_COLLAB=1

# Then in agent:
> organize my yahoo mail folders
```
You'll get a conversational AI that helps you plan before organizing.

### Explicit Mail Mode
```
> Mail: review my Yahoo inbox and suggest rules
```

## Files Modified
- `agent/treys_agent.py` - Added simple question handling and mail intent detection
- `agent/modes/mail_supervised.py` - Added interactive planning menu
- `agent/modes/mail_collab.py` - NEW: AI-powered conversational mail planning

## Testing
All changes have been tested and verified working.
