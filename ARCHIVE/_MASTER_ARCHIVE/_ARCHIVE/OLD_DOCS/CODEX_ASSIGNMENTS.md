# CODEX ASSIGNMENTS - November 12, 2025
**Owner:** Codex (AI Agent)  
**Status:** Ready to work  
**Mission:** Complete HALF A (Research & Planning)

---

## 🎯 YOUR MISSION

You are responsible for **HALF A: Understanding & Strategic Planning**.

This is 10 focused research/planning tasks that will create the exact specifications for building the missing `addCardToDeck` tool.

**Timeline:** Tonight/tomorrow (6-8 hours)  
**Deliverable:** 10 specification documents in `HALF_A_FINDINGS/`  
**Success:** Clear blueprint for implementation

---

## 📖 READ THESE FIRST (In Order)

1. **QUICK_REFERENCE_GUIDE.md** (5 min)
2. **START_HERE.md** (10 min)
3. **DIVIDED_WORK_PLAN_HALF_A_AND_B.md** - Read section "HALF A: UNDERSTANDING & STRATEGIC PLANNING" (30 min)

**Total:** 45 minutes to understand your mission

---

## ✅ YOUR 10 TASKS

All tasks are in: `DIVIDED_WORK_PLAN_HALF_A_AND_B.md` under "HALF A"

### HALF A TASK 1: Find StudyMCP Location (1 hour)
- Search for StudyMCP source code on Windows
- Determine if local or cloud-hosted
- Document exact path + repository info
- **Deliverable:** `HALF_A_FINDINGS/1_STUDYMCP_LOCATION.md`

### HALF A TASK 2: Understand Current Anki Integration (1 hour)
- Check if AnkiConnect is installed/running
- Search for existing Anki code
- Verify credentials storage
- **Deliverable:** `HALF_A_FINDINGS/2_ANKI_INTEGRATION_CURRENT.md`

### HALF A TASK 3: Map The Real Workflow (1 hour)
- Current data flow: ChatGPT → StudyMCP → ???
- What's the missing link?
- Document current vs desired workflow
- **Deliverable:** `HALF_A_FINDINGS/3_WORKFLOW_ANALYSIS.md`

### HALF A TASK 4: Audit Your 5 PT Courses (1 hour)
- Verify all 48 due dates extracted correctly
- Check C:\PT School\ folder structure
- Ensure no data corruption
- **Deliverable:** `HALF_A_FINDINGS/4_COURSE_AUDIT.md`

### HALF A TASK 5: Define addCardToDeck Specification (1 hour)
- Write technical spec for the tool
- Define inputs/outputs
- Plan error handling
- **Deliverable:** `HALF_A_FINDINGS/5_ADDCARDTODECK_SPEC.md`

### HALF A TASK 6: Create Integration Architecture Doc (1 hour)
- Document how all 5 systems connect
- Show data dependencies
- Identify breaking points
- **Deliverable:** `HALF_A_FINDINGS/6_INTEGRATION_ARCHITECTURE.md`

### HALF A TASK 7: Decision Matrix (0.5 hours)
- Create strategic choice framework
- ChatGPT workflow vs Dashboard priority?
- Anki integration method choice?
- **Deliverable:** `HALF_A_FINDINGS/7_DECISION_MATRIX.md`

### HALF A TASK 8: System Dependencies Checklist (0.5 hours)
- Verify all Python packages installed
- Check external services available
- Test file path access
- **Deliverable:** `HALF_A_FINDINGS/8_DEPENDENCIES.md`

### HALF A TASK 9: Status Update (0.5 hours)
- Document current state based on findings
- List what works, what's incomplete
- Identify blockers
- **Deliverable:** `HALF_A_FINDINGS/9_STATUS_UPDATE.md`

### HALF A TASK 10: Create HALF B Specifications (0.5 hours)
- Write exact instructions for developer
- Code patterns to follow
- Testing steps
- Success criteria
- **Deliverable:** `HALF_A_FINDINGS/10_HALF_B_SPECIFICATIONS.md`

---

## 📋 SETUP INSTRUCTIONS

### Step 1: Create Working Folder
```powershell
mkdir "C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\HALF_A_FINDINGS"
```

### Step 2: Start Task 1
Open `DIVIDED_WORK_PLAN_HALF_A_AND_B.md` and scroll to "HALF A TASK 1"

### Step 3: Document as You Go
Create numbered markdown files:
- `1_STUDYMCP_LOCATION.md`
- `2_ANKI_INTEGRATION_CURRENT.md`
- `3_WORKFLOW_ANALYSIS.md`
- etc.

---

## 🎯 SUCCESS CRITERIA

You're done when:

- ✅ All 10 `.md` files created in `HALF_A_FINDINGS/`
- ✅ Each file is 200-500 words (thorough but concise)
- ✅ All questions answered (no "unknown" items)
- ✅ Strategic decisions made in Decision Matrix
- ✅ Zero ambiguity about what to build next
- ✅ HALF B specification is implementation-ready

---

## 📊 TIME BREAKDOWN

```
Total: 6-8 hours

Task 1: 1 hour (Find StudyMCP)
Task 2: 1 hour (Anki audit)
Task 3: 1 hour (Workflow map)
Task 4: 1 hour (Course audit)
Task 5: 1 hour (addCardToDeck spec)
Task 6: 1 hour (Integration arch)
Task 7: 0.5 hours (Decision matrix)
Task 8: 0.5 hours (Dependencies)
Task 9: 0.5 hours (Status update)
Task 10: 0.5 hours (HALF B specs)
```

**Realistic timeline:** 2-3 sessions of 2-3 hours each

---

## 🔗 KEY REFERENCE DOCS

While working, refer to:
- `GAMEPLAN.md` - Master strategy
- `STATUS.md` - Current state
- `CODEX_INSTRUCTIONS.md` - Original task notes (for context)
- `QUICK_REFERENCE_GUIDE.md` - File locations + credentials

---

## ⚠️ IMPORTANT NOTES

**Do NOT:**
- ❌ Modify code in PROGRAMS/
- ❌ Change any existing systems
- ❌ Make decisions about implementation details
- ❌ Skip any of the 10 tasks

**DO:**
- ✅ Research thoroughly
- ✅ Document findings clearly
- ✅ Ask clarifying questions if stuck
- ✅ Make strategic decisions (what's priority?)
- ✅ Create specs that HALF B developer can follow blindly

---

## 📞 HANDOFF AFTER COMPLETION

When you finish all 10 tasks:

1. Update `STATUS.md` with "HALF A COMPLETE" section
2. Note any blockers/questions
3. Create summary: "HALF B is ready to proceed. Blockers: [list if any]"
4. Commit all `HALF_A_FINDINGS/*.md` files

**Next person (developer) picks up HALF B with zero questions.**

---

## 💡 KEY INSIGHTS FOR YOUR WORK

1. **The real blocker is StudyMCP location** - Once you find it, everything else becomes clear
2. **Anki integration is the second decision** - AnkiConnect (API) vs File-based (manual import)
3. **addCardToDeck spec is straightforward** - Just define inputs/outputs clearly
4. **You're creating a blueprint, not building** - Clarity over code

---

**Status:** Ready to start  
**Owner:** Codex  
**First task:** Read the 3 intro docs, then start HALF A TASK 1  
**Deadline:** Tomorrow morning (Trey reviews findings)

Go!

