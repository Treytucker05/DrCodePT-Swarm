# Documentation Index

Complete guide to all documentation in the DrCodePT-Swarm project.

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| `README.md` | Project overview and quick start | Everyone |
| `GOOGLE_TASKS_QUICK_START.md` | 5-minute setup for Google Tasks/Calendar | New users |
| `ARCHITECTURE.md` | Complete system architecture | Developers |
| `AGENT_BEHAVIOR.md` | Source of truth for agent behavior | Contributors |

---

## Core Documentation

### Getting Started

1. **`README.md`** - Main entry point
   - Project overview
   - Quick start instructions
   - Current status
   - Documentation map

2. **`START_HERE.md`** - Onboarding guide
   - First-run flow
   - Environment setup
   - Basic usage

3. **`AGENT_SETUP_GUIDE.md`** - Prerequisites
   - System requirements
   - Installation steps
   - Configuration

---

## Google Tasks/Calendar Fast Path (NEW!)

### User Documentation

1. **`GOOGLE_TASKS_QUICK_START.md`** - Quick setup (5 minutes)
   - One-time OAuth setup
   - Natural language examples
   - Troubleshooting

2. **`GOOGLE_TASKS_SUMMARY.md`** - Feature overview
   - What was built
   - Performance comparison
   - Usage examples
   - Limitations and future work

### Technical Documentation

3. **`GOOGLE_TASKS_FAST_PATH.md`** - Complete technical docs
   - Code flow walkthrough (step-by-step)
   - Architecture decisions
   - LLM brain implementation
   - Performance metrics
   - Files modified

4. **`GOOGLE_TASKS_FLOW_DIAGRAM.md`** - Visual flow diagrams
   - Complete execution flow with ASCII diagrams
   - Data flow
   - Code structure map
   - Integration points

---

## Architecture and Design

1. **`ARCHITECTURE.md`** - System architecture
   - Component overview
   - Core loop
   - CLI routing and fast paths (NEW section!)
   - Tool registry
   - Memory subsystem
   - Safety mechanisms

2. **`AGENT_BEHAVIOR.md`** - Behavioral source of truth
   - Decision making
   - Planning strategies
   - Tool usage patterns

3. **`USAGE_EXAMPLES.md`** - Real workflows
   - Common use cases
   - Best practices
   - Example commands

4. **`PRINCIPLES.md`** - Design philosophy
   - Core principles
   - Read before making changes

---

## Reference

1. **`QUICK_REFERENCE.md`** - Command cheat sheet
   - Common commands
   - Keyboard shortcuts
   - Quick tips

2. **`TROUBLESHOOTING.md`** - Common issues
   - Error messages
   - Solutions
   - Debugging tips

---

## Historical Context (Archive)

These provide context but are not maintained as source of truth:

- `ENHANCEMENT_SUMMARY.md`
- `UNIFIED_AGENT_PLAN.md`
- `IMPLEMENTATION_STEPS.md`
- `REBUILD_PLAN.md`
- `REVIEW_AND_ACTION_PLAN.md`
- `AGENT_IMPROVEMENTS.md`
- `STATUS.md` / `CURRENT_STATE.md` / `TODO.md`

---

## Workflow Documentation

1. **`AGENTS.md`** - Operating constraints
   - Workflow rules
   - Required constraints

2. **`CONTINUITY.md`** - Continuity ledger
   - Session tracking
   - State preservation

---

## Quick Navigation by Task

### "I want to use Google Tasks/Calendar"
→ Start with `GOOGLE_TASKS_QUICK_START.md`

### "I want to understand how the fast path works"
→ Read `GOOGLE_TASKS_FAST_PATH.md`

### "I want to see the code flow visually"
→ Check `GOOGLE_TASKS_FLOW_DIAGRAM.md`

### "I want to understand the overall architecture"
→ Read `ARCHITECTURE.md`

### "I'm new to the project"
→ Start with `README.md` then `START_HERE.md`

### "I need to troubleshoot an issue"
→ Check `TROUBLESHOOTING.md`

### "I want to contribute"
→ Read `PRINCIPLES.md` and `AGENT_BEHAVIOR.md`

---

## Documentation Maintenance

### Source of Truth Hierarchy

1. **`AGENT_BEHAVIOR.md`** - Always update first
2. **`ARCHITECTURE.md`** - Update for structural changes
3. **`README.md`** - Update for feature additions
4. **Specialized docs** - Update for specific features

### When Adding New Features

1. Update `AGENT_BEHAVIOR.md` (if behavior changes)
2. Update `ARCHITECTURE.md` (if architecture changes)
3. Update `README.md` (add to status section)
4. Create specialized docs (like `GOOGLE_TASKS_*.md`)
5. Update this index

### Documentation Standards

- **Be concise** - Get to the point quickly
- **Use examples** - Show, don't just tell
- **Include diagrams** - Visual > text for complex flows
- **Keep it current** - Remove outdated info
- **Cross-reference** - Link to related docs

---

## File Organization

```
DrCodePT-Swarm/
├── README.md                          # Main entry point
├── DOCUMENTATION_INDEX.md             # This file
│
├── Core Documentation/
│   ├── START_HERE.md
│   ├── ARCHITECTURE.md
│   ├── AGENT_BEHAVIOR.md
│   ├── PRINCIPLES.md
│   ├── USAGE_EXAMPLES.md
│   ├── QUICK_REFERENCE.md
│   ├── TROUBLESHOOTING.md
│   └── AGENT_SETUP_GUIDE.md
│
├── Google Tasks/Calendar Fast Path/
│   ├── GOOGLE_TASKS_QUICK_START.md   # Start here!
│   ├── GOOGLE_TASKS_SUMMARY.md
│   ├── GOOGLE_TASKS_FAST_PATH.md     # Technical details
│   └── GOOGLE_TASKS_FLOW_DIAGRAM.md  # Visual diagrams
│
├── Workflow/
│   ├── AGENTS.md
│   └── CONTINUITY.md
│
└── Archive/ (historical context only)
    ├── ENHANCEMENT_SUMMARY.md
    ├── UNIFIED_AGENT_PLAN.md
    └── ...
```

---

## Last Updated

- **Date**: January 3, 2026
- **Major Changes**: Added Google Tasks/Calendar fast path documentation
- **Updated Files**: ARCHITECTURE.md, README.md, + 4 new docs

---

## Need Help?

1. **Can't find what you need?** Check the relevant section above
2. **Documentation unclear?** File an issue on GitHub
3. **Want to contribute?** Read `PRINCIPLES.md` first

---

**Happy documenting!** 📚
