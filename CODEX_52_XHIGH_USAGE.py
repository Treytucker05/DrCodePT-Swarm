"""
Example: Using GPT-5.2-Codex xhigh in DrCodePT-Swarm

This shows how to integrate the new xhigh reasoning methods into your existing learning_agent.py

Usage in learning_agent.py:
    
    from agent.codex_client import CodexTaskClient
    
    client = CodexTaskClient.from_env()
    
    # For complex planning/analysis (use xhigh)
    result = client.execute_three_phase_task(
        task="Extract 48 due dates from Blackboard and create study schedule",
        use_planning=True
    )
    
    # For simple tasks (use medium reasoning - faster, cheaper)
    output = client.call_with_medium("Convert this data to JSON")
    
    # For critical decisions (use xhigh)
    analysis = client.call_with_xhigh("Validate this schedule and identify conflicts")
"""

# ============================================================================
# Example 1: Three-Phase Task Execution (Best for complex agent work)
# ============================================================================

from agent.codex_client import CodexTaskClient

client = CodexTaskClient.from_env()

# Execute complex task with planning → execution → validation
result = client.execute_three_phase_task(
    task="Analyze 48 due dates across 5 PT courses and create optimized study schedule",
    use_planning=True
)

print(f"✅ Task Success: {result['success']}")
print(f"📋 Planning Phase: {result['plan'][:200]}...")
print(f"⚙️  Execution Phase: {result['execution'][:200]}...")
print(f"✔️  Validation Phase: {result['validation'][:200]}...")

# ============================================================================
# Example 2: Direct xhigh for Complex Analysis
# ============================================================================

# For something that needs DEEP thinking
analysis_task = """
Analyze these course deadlines and identify:
1. Critical paths
2. Resource bottlenecks
3. Optimal study order

Courses:
- Legal & Ethical Issues (14 dates)
- Lifespan Development (2 dates)  
- Clinical Pathology (22 dates)
- Human Anatomy (6 dates)
- PT Examination Skills (4 dates)
"""

deep_analysis = client.call_with_xhigh(
    analysis_task,
    timeout_seconds=600  # xhigh can use longer timeout
)

print("\n🧠 Deep Analysis (xhigh):")
print(deep_analysis)

# ============================================================================
# Example 3: Fast Execution with Medium Reasoning
# ============================================================================

# For simple transformations or follow-ups
json_conversion = client.call_with_medium(
    "Convert this schedule to JSON format with fields: course, assignment, due_date, weight"
)

print("\n⚡ Quick Execution (medium):")
print(json_conversion)

# ============================================================================
# INTEGRATION INTO learning_agent.py
# ============================================================================

"""
Add this to your learning_agent.py's execute_task method:

    async def execute_autonomous_task(self, task: str) -> Dict[str, Any]:
        # Initialize Codex client with xhigh support
        client = CodexTaskClient.from_env()
        
        # Use 3-phase execution for complex tasks
        result = client.execute_three_phase_task(
            task=task,
            use_planning=True
        )
        
        return {
            "success": result["success"],
            "plan": result["plan"],
            "execution": result["execution"],
            "validation": result["validation"],
            "reasoning_level": "xhigh (planning + validation) + medium (execution)"
        }

This gives you:
✅ Deep reasoning for planning (xhigh)
✅ Fast execution (medium)  
✅ Quality validation (xhigh)
✅ Uses your existing Codex CLI login
✅ No OpenAI API keys needed
"""
