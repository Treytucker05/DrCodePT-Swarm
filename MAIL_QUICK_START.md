# Quick Start: Mail Organization

## What Changed?
Your agent now has **interactive planning** for mail organization instead of immediately scanning everything.

## How to Use

### Option 1: Basic Interactive Mode (Default)
```
> organize my yahoo mail folders
```

You'll see a menu:
```
What would you like to do?
  1) Get a quick overview (scan recent messages)
  2) Deep dive into specific folders
  3) Plan a folder reorganization strategy  ← RECOMMENDED FOR PLANNING
  4) Find and clean up spam/unwanted senders
  5) Custom - tell me what you need
```

**Choose Option 3** to plan your folder strategy:
- Discuss your goals
- Create folders before organizing
- Get strategy suggestions
- Then optionally scan

### Option 2: AI Conversational Planning
For a more conversational experience with AI helping you plan:

**Windows PowerShell:**
```powershell
$env:MAIL_USE_COLLAB="1"
python agent/treys_agent.py
```

**Windows CMD:**
```cmd
set MAIL_USE_COLLAB=1
python agent/treys_agent.py
```

Then:
```
> organize my yahoo mail folders
```

You'll get an AI assistant that talks with you about your goals before organizing.

## Example Session (Option 3 - Planning)

```
> organize my yahoo mail folders

[Shows your folders]

What would you like to do?
Choose an option (1-5): 3

[MAIL] Let's plan your folder organization strategy.

What's your main goal? separate work from personal

[MAIL] Goal: separate work from personal

Let me suggest some strategies:
  • Create top-level categories (Work, Personal, Finance, etc.)
  • Use subfolders for specific topics
  • Set up rules to auto-file incoming mail

Do you want to: (a) scan first to see what you have, (b) create folders now, (c) both: b

[MAIL] Let's create some folders.

New folder name (or 'done' to finish): Work
[MAIL] ✓ Created folder: Work

New folder name (or 'done' to finish): Personal
[MAIL] ✓ Created folder: Personal

New folder name (or 'done' to finish): done

[MAIL] Folders created! Run this again when you're ready to organize messages.
```

## Tips

1. **Start with Option 3** if you want to plan before scanning
2. **Use Option 4** if you just want to find spam quickly
3. **Enable MAIL_USE_COLLAB** if you want AI to help you think through your strategy
4. The agent won't make changes without your approval - it's safe to explore!

## Need Help?
Type `help` in the agent to see all available commands.
