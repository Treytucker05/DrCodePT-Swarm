# Google Tasks/Calendar - Quick Start Guide

## 5-Minute Setup

### Step 1: One-Time OAuth Setup

```bash
python setup_google_calendar.py
```

This will:
1. ✓ Check for OAuth credentials
2. ✓ Open browser for authorization
3. ✓ Save access token
4. ✓ Test connection

**Note**: If you get "Error 403: access_denied", you need to add yourself as a test user in Google Cloud Console:
- Go to: https://console.cloud.google.com/apis/credentials/consent
- Add your email under "Test users"

---

### Step 2: Try It Out!

```bash
# Show all tasks
python -m agent.cli "show my tasks"

# Show specific list
python -m agent.cli "what workouts do I need to make"

# Filter by keyword
python -m agent.cli "what do I need to do about my car"

# Check calendar
python -m agent.cli "what's on my calendar"
```

---

## Natural Language Examples

The agent has an LLM "brain" that understands natural language! Here's what you can say:

### ✅ Show All Tasks
```bash
"show my tasks"
"what do I need to do"
"list all my tasks"
"show me everything"
```

### ✅ Filter by List
```bash
"what workouts do I need to make"
"show my to do list"
"what's in my workouts"
"show tasks in reclaim list"
```

### ✅ Filter by Keyword
```bash
"what do I need to do about my car"
"show tasks about taxes"
"what's my diet plan"
```

### ✅ Calendar
```bash
"what's on my calendar"
"show upcoming events"
"what meetings do I have"
```

---

## How It Works

```
Your Query → LLM Brain → Google API → Results
    ↓          ↓             ↓           ↓
 "workouts"  Interprets   Fetches    Filters
             as list     all tasks   & shows
```

**Total time**: 5-10 seconds (vs 30-60 seconds with full agent!)

---

## Performance

| What You Get | Speed |
|-------------|-------|
| **Natural language understanding** | ✓ LLM-powered |
| **All task lists** | ✓ Fetched automatically |
| **Smart filtering** | ✓ By list or keyword |
| **Active tasks only** | ✓ Hides completed |
| **Execution time** | ⚡ 5-10s (vs 30-60s) |

---

## Troubleshooting

### "Google OAuth not authorized yet"
**Fix**: Run `python setup_google_calendar.py`

### "Error 403: access_denied"
**Fix**: Add your email as a test user in Google Cloud Console

### Slow performance (>10s)
**This is normal!** The LLM brain adds 5-10 seconds to understand your request, but it's still 6-12x faster than the full agent (30-60s).

---

## What's Next?

For detailed technical documentation, see: `GOOGLE_TASKS_FAST_PATH.md`

For general agent usage, see: `README.md`

---

## Summary

✅ **One-time setup**: Run `setup_google_calendar.py`
✅ **Natural language**: Ask in plain English
✅ **Blazing fast**: 5-10s vs 30-60s
✅ **Smart filtering**: By list or keyword
✅ **Always current**: Fetches latest from Google

**Start using it now:**
```bash
python -m agent.cli "show my tasks"
```
