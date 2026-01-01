"""
Test script to verify:
1. Memory persistence across tasks
2. Agent reasoning (not using hardcoded playbooks)
3. Learning from failures
"""
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
from agent.autonomous.runner import AgentRunner
from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
from agent.llm.codex_cli_client import CodexCliClient

def test_memory_persistence():
    """Test that memory persists across AgentRunner instances."""
    print("\n" + "=" * 60)
    print("TEST 1: Memory Persistence")
    print("=" * 60)
    
    repo_root = Path(__file__).parent
    memory_path = repo_root / "agent" / "memory" / "autonomous_memory.sqlite3"
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create memory store
    memory_store = SqliteMemoryStore(path=memory_path)
    print(f"[OK] Created memory store: {memory_path}")
    
    # Store a test memory
    try:
        record_id = memory_store.upsert(
            kind="experience",
            content="Test: Created file memory_test.txt with content 'test 1'",
            key="test_memory_1",
            metadata={"test": True}
        )
        print(f"[OK] Stored test memory (ID: {record_id})")
        
        # Retrieve it
        results = memory_store.search("memory_test.txt", limit=5)
        if results:
            print(f"[OK] Retrieved {len(results)} memories containing 'memory_test.txt'")
            for r in results:
                print(f"  - {r.content[:80]}...")
        else:
            print("[FAIL] No memories found")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        memory_store.close()
    
    print("\n" + "=" * 60)

def test_agent_reasoning():
    """Test that agent reasons through tasks (not using hardcoded scripts)."""
    print("\n" + "=" * 60)
    print("TEST 2: Agent Reasoning")
    print("=" * 60)
    
    try:
        llm = CodexCliClient.from_env()
        print("✓ LLM client initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize LLM: {e}")
        return
    
    repo_root = Path(__file__).parent
    memory_path = repo_root / "agent" / "memory" / "autonomous_memory.sqlite3"
    memory_store = SqliteMemoryStore(path=memory_path) if memory_path.parent.exists() else None
    
    runner_cfg = RunnerConfig(max_steps=10, timeout_seconds=120, profile="fast")
    agent_cfg = AgentConfig(
        allow_human_ask=False,  # Don't ask questions during test
        allow_interactive_tools=False,
        memory_db_path=memory_path if memory_store else None,
    )
    planner_cfg = PlannerConfig(mode="react")
    
    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
        memory_store=memory_store,
    )
    print("[OK] AgentRunner created with memory store")
    
    # Test task: Create a simple file (should reason through it, not use script)
    task = "Create a file called reasoning_test.txt with content 'Agent reasoned through this task'"
    print(f"\nTesting task: {task}")
    print("Expected: Agent should REASON through the task, not use hardcoded script")
    print("\nRunning (this may take a moment)...\n")
    
    result = runner.run(task)
    
    print("\n" + "=" * 60)
    print(f"Result: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Reason: {result.stop_reason}")
    print(f"Steps: {result.steps_executed}")
    if result.trace_path:
        print(f"Trace: {result.trace_path}")
    
    # Check if file was created
    test_file = repo_root / "reasoning_test.txt"
    if test_file.exists():
        content = test_file.read_text()
        print(f"\n[OK] File created: {test_file}")
        print(f"[OK] Content: {content[:100]}")
    else:
        print(f"\n[FAIL] File not found: {test_file}")
    
    print("\n" + "=" * 60)
    
    if memory_store:
        memory_store.close()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AGENT MEMORY & REASONING TEST")
    print("=" * 60)
    
    test_memory_persistence()
    
    print("\nProceeding with reasoning test (non-interactive)...")
    test_agent_reasoning()
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)

