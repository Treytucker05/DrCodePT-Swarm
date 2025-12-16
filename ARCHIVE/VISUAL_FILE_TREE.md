# DrCodePT-Swarm - Visual File Tree
**Generated**: November 14, 2025, 8:05 PM

```
DrCodePT-Swarm/
│
├── 📄 README.md ⭐ START HERE
├── 📄 COMPLETE_FILE_STRUCTURE.md
├── 📄 FILE_ORGANIZATION_INDEX.md
├── 📄 CLEANUP_SUMMARY_2025-11-14.md
├── 📄 .gitignore
│
├── 🚀 Launchers
│   ├── LAUNCH_CODEX.bat
│   ├── LAUNCH_CODEX.ps1
│   ├── START_DRCODEPT.bat
│   ├── START_DR_CODEPT_RAG.bat
│   ├── START_MCP_SERVER.bat
│   ├── WSL CODEX.bat
│   ├── WSL CODEX.ps1
│   ├── WSL DIAGNOSTIC.bat
│   └── SET-UBUNTU-DEFAULT.bat
│
├── 📂 DOCS/ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ All Documentation
│   ├── 📄 START_HERE.md ⭐ New User Entry
│   ├── 📄 PROJECT_STATUS.md
│   ├── 📄 EXECUTION_PLAN.md
│   ├── 📄 MASTER_PLAN.md (CANONICAL)
│   ├── 📄 SYSTEM_INVENTORY.md
│   └── 📄 CODEX.md
│
├── 📂 Codex Tasks/ ━━━━━━━━━━━━━━━━━━━━━━━━━ Claude ↔ Codex Coordination
│   ├── 📄 TASKS.md ✅ Populated Nov 14
│   ├── 📄 CLAUDE_STATE.md ✅ Populated Nov 14
│   ├── 📄 README.md
│   ├── 📄 4_INTEGRATION_MAP.md
│   │
│   └── 📂 CODEX_ASSIGNMENTS/
│       ├── 📄 PHASE_2C_CODEX_SPECIFICATIONS.md
│       ├── 📄 COORDINATION_GUIDE.md
│       ├── 📄 QUICK_START.md
│       ├── 📄 ADDCARDTODECK_DESIGN.md
│       └── 📄 PHASE2C_DISCOVERY_REPORT.md
│
├── 📂 PROGRAMS/ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ All Working Code
│   │
│   ├── 📂 blackboard-agent/ ━━━━━━━━━━━━━━ UTMB Blackboard Automation
│   │   ├── 📄 agent.py ⭐ Main Entry
│   │   ├── 📄 claude_tools.py
│   │   ├── 📄 build_course_maps.py
│   │   ├── 📄 .env
│   │   ├── 📄 requirements.txt
│   │   ├── 📄 opstore.db
│   │   │
│   │   ├── 📄 1_BLACKBOARD_DOWNLOAD_SPEC.md
│   │   │
│   │   ├── 📂 handlers/
│   │   │   ├── 📄 blackboard_handler.py ⭐ Core Scraper
│   │   │   ├── 📄 claude_handler.py
│   │   │   ├── 📄 file_handler.py
│   │   │   ├── 📄 process_handler.py
│   │   │   ├── 📄 state_manager.py
│   │   │   ├── 📄 web_handler.py
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📂 __pycache__/
│   │   │
│   │   ├── 📂 config/
│   │   ├── 📂 computer_use/
│   │   ├── 📂 venv/
│   │   ├── 📂 venv312/
│   │   │
│   │   ├── 📄 COURSE_URLS.txt ✅ 5 courses
│   │   ├── 📄 COURSE_DUE_DATES.txt ✅ 48 dates
│   │   ├── 📄 COURSE_DUE_DATES_NORMALIZED.txt
│   │   │
│   │   ├── 📄 extract_course_urls.py
│   │   ├── 📄 extract_due_dates_from_list.py
│   │   ├── 📄 interactive_track_courses.py
│   │   ├── 📄 __tmp_download.py
│   │   └── 📄 __tmp_test1.py
│   │
│   ├── 📂 fastmcp-server/ ━━━━━━━━━━━━━━━━ MCP Server + Anki Bridge
│   │   ├── 📄 server.py ⭐ Main MCP Server
│   │   ├── 📄 requirements.txt
│   │   ├── 📄 START_DRCODEPT.bat
│   │   ├── 📄 START_DRCODEPT.ps1
│   │   │
│   │   ├── 🧬 Anatomy MCP Components
│   │   │   ├── 📄 entities.py
│   │   │   ├── 📄 aligner.py
│   │   │   ├── 📄 verifier.py
│   │   │   └── 📄 manifest_loader.py
│   │   │
│   │   ├── 🃏 Anki Integration
│   │   │   ├── 📄 anki_bridge.py
│   │   │   └── 📄 addcardtodeck.py
│   │   │
│   │   ├── 📄 manifest.yaml
│   │   ├── 📄 ngrok.yml
│   │   │
│   │   ├── 📂 adapters/
│   │   ├── 📂 config/
│   │   ├── 📂 courses/
│   │   ├── 📂 data/
│   │   │   └── 📄 study_pack.md
│   │   ├── 📂 index/
│   │   ├── 📂 normalizer/
│   │   │
│   │   ├── 📂 modules/
│   │   │   └── 📂 wk09_glute_postthigh/ ✅ Week 9 Pilot
│   │   │       ├── 📄 facts.db
│   │   │       ├── 📄 facts.md
│   │   │       └── 📄 coverage.json
│   │   │
│   │   ├── 📂 venv/
│   │   ├── 📂 __pycache__/
│   │   │
│   │   └── 📚 Documentation
│   │       ├── 📄 README_CONSOLIDATED.md
│   │       ├── 📄 LIVE_USAGE_GUIDE.md
│   │       ├── 📄 CHATGPT_SETUP_COMPLETE.md
│   │       ├── 📄 IMPLEMENTATION_SUMMARY.md
│   │       ├── 📄 SERVER_PY_INTEGRATION.md
│   │       ├── 📄 3_CONTENT_PIPELINE_SPEC.md
│   │       ├── 📄 TRANSCRIPTION_PIPELINE.md
│   │       └── 📄 TROUBLESHOOTING.md
│   │
│   ├── 📂 drcodept-rag/ ━━━━━━━━━━━━━━━━━━ RAG Query Client
│   │   ├── 📄 drcodept.py ⭐ Main CLI
│   │   ├── 📄 README_RAG.md
│   │   │
│   │   └── 📂 core/
│   │       ├── 📄 anythingllm_client.py
│   │       ├── 📄 rag_handler.py
│   │       └── 📂 generators/
│   │           ├── 📄 anki_generator.py
│   │           └── 📄 npte_generator.py
│   │
│   └── 📂 dashboard-api/ ━━━━━━━━━━━━━━━━━ Dashboard Backend
│       ├── 📄 api-server.js ⭐ Main Server
│       ├── 📄 api-server.log
│       ├── 📄 .env
│       ├── 📄 .env.example
│       ├── 📄 .gitignore
│       ├── 📄 package.json
│       ├── 📄 package-lock.json
│       ├── 📄 README.md
│       │
│       ├── 📂 dashboard/
│       ├── 📂 data/
│       ├── 📂 node_modules/
│       ├── 📂 scripts/
│       ├── 📂 src/
│       └── 📂 tests/
│
└── 📂 _MASTER_ARCHIVE/ ━━━━━━━━━━━━━━━━━━━ Historical Files (Read-Only)
    ├── 📄 FILE_MANIFEST.md
    │
    ├── 📂 OLD_ARCHIVE/ ━━━━━━━━━━━━━━━━━━ Pre-Nov 13 Cleanup
    │   ├── 📄 CURRENT_SYSTEM_STATE.md ← Moved Nov 14
    │   ├── 📄 ACTIVE_ROADMAP.md
    │   ├── 📄 BLACKBOARD_SCRAPER_STATUS.md
    │   ├── 📄 BLACKBOARD_AGENT_TEST_REPORT.md
    │   ├── 📄 BLACKBOARD_FILE_DOWNLOAD_AUDIT.md
    │   ├── 📄 CODEX_V2.md
    │   ├── 📄 COMPUTER_USE_AUDIT.md
    │   ├── 📄 MASTER_PLAN_OPTION_B_UPDATE.md
    │   ├── 📄 MASTER_PROGRAM_SPEC.md
    │   ├── 📄 README_MORNING.md
    │   ├── 📄 AGENT_END_TO_END_TEST_REPORT.md
    │   │
    │   ├── 📂 DOCS/
    │   ├── 📂 HALF_A_FINDINGS/
    │   ├── 📂 IMPLEMENTATION/
    │   └── 📂 _MASTER_DOCS/
    │
    └── 📂 _ARCHIVE/ ━━━━━━━━━━━━━━━━━━━━━ Even Older Files
        ├── 📄 HANDOFF_FOR_NEXT_CHAT.md
        ├── 📄 ORGANIZATION_FINAL.md
        │
        ├── 📂 OLD_DOCS/
        ├── 📂 external/
        └── 📂 phase7_unified_system/
```

---

## 🎯 LEGEND

### Symbols
```
📄 = File
📂 = Folder
⭐ = Important/Entry Point
✅ = Working/Complete
❌ = Not Implemented
❓ = Status Unknown
🚀 = Launcher Script
━━ = Section Separator
```

### Status Indicators
```
DOCS/                  ✅ All current (Nov 13)
Codex Tasks/          ✅ Populated (Nov 14)
blackboard-agent/     ✅ Working (48 dates extracted)
fastmcp-server/       ✅ Working (MCP operational)
drcodept-rag/         ✅ Working (RAG functional)
dashboard-api/        ❓ Unknown status
```

---

## 📊 QUICK STATS

```
Total Programs:        4
Active Docs:          6
Coordination Files:   7
Archive Files:        50+
Launchers:            9

Lines of Documentation: ~2,000+
Lines of Code:         ~5,000+ (estimated)
```

---

## 🔍 KEY PATHS

### Start Here
```
README.md
└── DOCS/START_HERE.md
    └── DOCS/PROJECT_STATUS.md
        └── DOCS/EXECUTION_PLAN.md
```

### Active Work
```
Codex Tasks/TASKS.md           ← Your task list
Codex Tasks/CLAUDE_STATE.md    ← Session context
```

### Working Code
```
PROGRAMS/blackboard-agent/agent.py
PROGRAMS/fastmcp-server/server.py
PROGRAMS/drcodept-rag/drcodept.py
PROGRAMS/dashboard-api/api-server.js
```

### Extracted Data
```
PROGRAMS/blackboard-agent/
├── COURSE_URLS.txt              (5 courses)
└── COURSE_DUE_DATES.txt         (48 dates)

PROGRAMS/fastmcp-server/modules/wk09_*/
└── facts.db                      (Anatomy facts)
```

---

## 🎨 COLOR CODING (if viewing in markdown viewer)

- 📄 **Blue** = Documentation files
- 📂 **Yellow** = Directories
- ⭐ **Gold** = Entry points / Most important
- ✅ **Green** = Working / Complete
- 🚀 **Red** = Launchers / Actions
- 🧬 **Purple** = Specialized components
- 📊 **Orange** = Data / Stats

---

**Total Depth**: 4 levels
**Total Directories**: ~35
**Total Files**: ~100+

