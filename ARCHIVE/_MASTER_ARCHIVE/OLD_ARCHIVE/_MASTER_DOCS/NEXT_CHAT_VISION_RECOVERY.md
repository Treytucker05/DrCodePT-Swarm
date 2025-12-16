# 🚀 NEXT CHAT HANDOFF: DrCodePT-Swarm Vision Recovery

**Status**: File consolidation project paused  
**Purpose**: Progressive questioning to recover user's original vision and guide consolidation  
**Approach**: 1 question at a time, answers build on each other  
**Owner**: Trey Tucker  
**Created**: November 12, 2025

---

## 📌 WHAT HAPPENED IN LAST CHAT

1. **Created new master plan** (_MASTER_DOCS/) with 5 comprehensive documents
2. **Discovered massive existing work** that wasn't included:
   - Anatomy MCP system (1,206 lines, production-ready, Week 9 pilot)
   - DrCodePT v0.1 (local RAG + textbook studying)
   - HALF_A detailed analysis (10 files, architecture decisions)
   - MASTER_PROGRAM_SPEC (570 lines, consolidates 27 documents)
   - unified_control_center (alternative vision with unified dashboard)

3. **Problem identified**: 60+ .md files across 5+ locations, multiple versions, unclear which is "real"

4. **Decision made**: Don't consolidate based on documents. Instead, ask Trey directly what they want the system to do.

---

## 🎯 THE VISION RECOVERY PROCESS

**Hypothesis**: Your original vision got spread across multiple versions and documents. By asking targeted questions about WHAT you want (not HOW), we can:
- Recover the true vision
- Consolidate documentation around that vision
- Make clean decisions about which systems to keep/integrate

**Process**:
1. Start with **Question 1** (foundational)
2. Trey answers Question 1
3. Claude asks **Question 2** (informed by Question 1 answer)
4. Trey answers Question 2
5. Continue until vision is clear...
6. Then consolidate documentation to match that vision

---

## 📊 WHAT EXISTS (Quick Inventory for Context)

### **System 1: Blackboard Extraction**
- Status: ✅ Working (with Selenium scroll fixes)
- What it does: Scrapes 5 PT courses, extracts due dates, modules, announcements
- Target: ~48 due dates from all 5 courses

### **System 2: Anki Integration**
- Status: ✅ Working (via AnkiConnect)
- What it does: Adds flashcards to Anki decks
- Technical: addCardToDeck tool (detailed spec exists)
- Strategy: Hybrid (AnkiConnect + AnkiWeb fallback + local deck.json)

### **System 3: MCP Server (fastmcp-server)**
- Status: ✅ Working (13 tools exposed)
- What it does: Provides interface for Claude to call tools
- Tools: 5 study tools + 8 deck management tools
- Deployment: Via ngrok tunnel to ChatGPT

### **System 4: Anatomy MCP** (Advanced)
- Status: ✅ Production-ready (not integrated yet)
- What it does: Extracts facts from anatomy slides + transcripts using AI
- Features: Dual-source verification (4 tiers), entity detection, transcript alignment
- Output: Verified Anki decks, JSONL, Markdown with coverage reports
- Scope: Currently Week 9 pilot (can scale to all 5 courses)
- Code: 1,206 lines of Python, complete documentation

### **System 5: DrCodePT v0.1** (Local RAG)
- Status: ✅ Ready to use (not integrated with Blackboard/Anki pipeline)
- What it does: Study PT textbooks locally with citations using Ollama + AnythingLLM
- Features: Query textbooks, generate Anki cards, NPTE questions
- Output: Anki-importable CSV
- Commands: `study dutton chapter 12`, `anki pathology 20`, `npte scapular`

### **System 6: Dashboard** (In Development)
- Status: ⏳ Not started
- What it does: Node.js + React interface for system status + control

---

## 🤔 WHAT WE DON'T KNOW (Yet)

These are the questions we need to answer through progressive questioning:

**About Your Vision:**
- Q1: What's the PRIMARY goal? (automation for your study workflow? dashboard for monitoring? comprehensive research system?)
- Q2: What systems should work TOGETHER vs. SEPARATELY?
- Q3: What's the entry point? (Claude conversation? CLI? Dashboard?)
- Q4: Should Anatomy MCP and DrCodePT v0.1 be integrated or kept standalone?
- Q5: What does "done" look like? (Phase 3? Phase 4? Full production?)
- Q6: Which of the 5+ systems is most critical?
- Q7: Should we unify under ONE master plan or keep separate system docs?

**About Integration:**
- Q8: How should Anatomy MCP facts feed into card generation?
- Q9: How should DrCodePT v0.1 connect to Blackboard extraction?
- Q10: Should there be a unified "study assistant" Claude that orchestrates everything?

**About Documentation:**
- Q11: How many .md files is acceptable? (1? 5? 10?)
- Q12: Should documentation reflect systems (one doc per system) or phases (one doc per phase)?
- Q13: What should the _MASTER_DOCS folder contain?

---

## ❓ QUESTION 1 (Start Here)

### **WHAT IS THE PRIMARY PURPOSE OF THIS ENTIRE PROJECT?**

Choose one (or blend):

**A) STUDY AUTOMATION FOR PT SCHOOL**
- Goal: Extract course materials → Generate flashcards → Push to Anki automatically
- User: You study, system handles logistics
- Entry point: "Hey Claude, create flashcards for Pathology exam"
- Success: All exams studied through automated pipeline

**B) COMPREHENSIVE ANATOMY RESEARCH SYSTEM**
- Goal: Extract verified anatomy facts from slides + transcripts + textbooks
- User: You query for anatomy information with citations
- Entry point: Dashboard or CLI (`study gluteal muscles`, get verified facts)
- Success: Complete anatomy database for all modules, ready to study

**C) UNIFIED STUDY INTELLIGENCE PLATFORM**
- Goal: One system that handles extraction, research, card generation, scheduling, recommendations
- User: Claude is your study assistant that coordinates everything
- Entry point: Chat with Claude ("Create a study plan for next week")
- Success: Automated, intelligent study buddy

**D) DIFFERENT/HYBRID**
- If none of above match, describe what you actually want the system to do

---

### **HOW TO ANSWER**

Please respond with:
1. **Which option (A/B/C/D)?**
2. **Why that one?** (2-3 sentences)
3. **Any important nuances** I should know? (What did previous versions get wrong?)

---

## 📋 WHAT HAPPENS NEXT

Once you answer Question 1:
1. Claude will ask **Question 2** (informed by your answer)
2. You'll answer Q2
3. Pattern continues...
4. After ~5-7 questions, vision will be clear
5. Then Claude can make specific consolidation recommendations
6. Then we build clean documentation around YOUR vision

---

## 🔗 REFERENCE DOCUMENTS (If You Want to Review)

**To understand what exists:**
- `_MASTER_DOCS/AUDIT_AND_CONSOLIDATION_PLAN.md` (full inventory)
- `unified_control_center/CURRENT_SYSTEM_STATE.md` (what's working)
- `HALF_A_FINDINGS/6_INTEGRATION_ARCHITECTURE.md` (how systems connect)

**To see the systems:**
- `PROGRAMS/fastmcp-server/IMPLEMENTATION_SUMMARY.md` (Anatomy MCP)
- `PROGRAMS/card-generator/drcodept.py` (DrCodePT v0.1)
- `PROGRAMS/blackboard-agent/handlers/blackboard_handler.py` (Blackboard extraction)

**But you don't NEED to review these to answer Question 1.** Just think about what you want to build.

---

## ⏱️ NEXT CHAT FLOW

**New chat should:**
1. Show this handoff document
2. Ask the user to read the context (this section)
3. Jump straight to **QUESTION 1** above
4. Wait for their answer
5. Ask **QUESTION 2** (to be determined based on Q1 answer)
6. Continue progressive questioning...

---

## 🎯 SUCCESS METRIC

When we're done with this process, you should be able to say:

**"The project's purpose is [A/B/C/D]. The systems that matter are [X, Y, Z]. They should work together like [description]. The entry point is [how you use it]. Success looks like [specific outcome]."**

And we can build documentation that's 100% aligned with that vision.

---

## 💡 WHY THIS APPROACH WORKS

**Problem with asking "Do you want A, B, C, D, or E?" all at once:**
- Information overload
- Can't answer well without context
- Answers are disconnected
- Leads to unclear consolidation

**Benefits of progressive questioning:**
- Each answer informs the next question
- Conversation feels natural
- Vision emerges organically
- Decisions are interconnected
- Documentation reflects actual goals
- No token limit issues (1 Q/A per message cycle)

---

## 📌 INSTRUCTIONS FOR NEXT CLAUDE

**When you receive this file:**

1. **Acknowledge it**: "I've reviewed the audit. Let's recover your vision through progressive questioning."

2. **Show context**: Brief summary of what exists (A-F above)

3. **Ask Question 1**: Use the exact wording in the "QUESTION 1" section

4. **Wait for answer**: Let Trey respond fully

5. **Ask Question 2**: Based on their Q1 answer, ask the next logical question from the list above OR create a new one that's informed by their answer

6. **Continue**: Repeat until vision is clear (~5-7 questions)

7. **Summarize**: "Your vision is [summary]. Based on this, here's what I recommend for consolidation..."

8. **Execute consolidation**: Once they confirm, consolidate documentation to match vision

---

**Status**: Ready for new chat  
**Owner**: Trey Tucker  
**Next Step**: Answer Question 1 in new chat  
**Expected Outcome**: Clear project vision → Clean documentation → Focused development
