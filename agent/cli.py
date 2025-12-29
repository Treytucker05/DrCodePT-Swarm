"""
Unified Agent CLI - Single entrypoint that bypasses mode routing.

All user input goes directly to AgentRunner with ReAct planning.
No more keyword-based mode switching.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure agent package is importable
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def list_all_tools() -> None:
    """List all available tools from the unified registry."""
    print("\nInitializing unified tool registry...")

    try:
        from agent.tools.unified_registry import get_unified_registry

        registry = get_unified_registry()
        registry.initialize()
        registry.print_tools()

    except Exception as e:
        print(f"[ERROR] Failed to initialize registry: {e}")
        import traceback
        traceback.print_exc()


def _setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    import os

    if verbose:
        level = logging.DEBUG
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        os.environ["AGENT_VERBOSE"] = "1"
    else:
        level = logging.WARNING  # Only show warnings and errors
        fmt = "[%(levelname)s] %(message)s"
        os.environ["AGENT_VERBOSE"] = "0"
        os.environ["AGENT_QUIET"] = "1"  # Signal to suppress debug prints

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="%H:%M:%S",
    )

    # Silence noisy libraries
    if not verbose:
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        logging.getLogger("torch").setLevel(logging.ERROR)
        logging.getLogger("agent.mcp").setLevel(logging.ERROR)
        logging.getLogger("agent.autonomous").setLevel(logging.WARNING)

        # Silence tqdm progress bars
        os.environ["TQDM_DISABLE"] = "1"


def _get_llm_client():
    """Get the LLM client based on environment configuration.

    Prefers Codex CLI (free, capable) for the agent loop.
    Falls back to OpenRouter if Codex is not available.
    """
    # Try CodexCliClient first (preferred - free and capable)
    try:
        from agent.llm.codex_cli_client import CodexCliClient
        return CodexCliClient.from_env()
    except Exception as e:
        logger.debug(f"CodexCliClient not available: {e}")

    # Fall back to OpenRouter
    try:
        from agent.llm.openrouter_client import OpenRouterClient
        return OpenRouterClient.from_env()
    except Exception as e:
        logger.debug(f"OpenRouterClient not available: {e}")

    raise RuntimeError(
        "No LLM client available. Set OPENROUTER_API_KEY or configure Codex CLI."
    )


def _build_tool_registry(agent_cfg, run_dir: Path, memory_store=None):
    """Build the unified tool registry."""
    from agent.autonomous.tools.builtins import build_default_tool_registry
    return build_default_tool_registry(agent_cfg, run_dir, memory_store=memory_store)


def run_agent(
    task: str,
    *,
    profile: str = "deep",
    max_steps: int = 30,
    timeout_seconds: int = 600,
    interactive: bool = True,
    verbose: bool = False,
    resume_path: Optional[Path] = None,
) -> int:
    """
    Run the unified agent on a task.

    Args:
        task: The task/goal to accomplish
        profile: Execution profile (fast, deep, audit)
        max_steps: Maximum steps before stopping
        timeout_seconds: Overall timeout
        interactive: Whether to allow human_ask tool
        verbose: Enable verbose logging
        resume_path: Optional path to resume from checkpoint

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
    from agent.autonomous.runner import AgentRunner

    _setup_logging(verbose)

    # Build configurations
    runner_cfg = RunnerConfig(
        max_steps=max_steps,
        timeout_seconds=timeout_seconds,
        profile=profile,
        llm_heartbeat_seconds=5.0 if interactive else None,
    )

    agent_cfg = AgentConfig(
        allow_human_ask=interactive,
        allow_interactive_tools=interactive,
    )

    planner_cfg = PlannerConfig(
        mode="react",  # Always use ReAct - one decision per step
    )

    # Get LLM client
    try:
        llm = _get_llm_client()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        return 1

    # Create and run agent
    runner = AgentRunner(
        cfg=runner_cfg,
        agent_cfg=agent_cfg,
        planner_cfg=planner_cfg,
        llm=llm,
    )

    print(f"\n{'=' * 50}")
    print("  UNIFIED AGENT")
    print(f"  Profile: {profile} | Max steps: {max_steps}")
    print(f"{'=' * 50}\n")
    print(f"[TASK] {task}\n")

    result = runner.run(task, resume_path=resume_path)

    print(f"\n{'=' * 50}")
    print(f"  Result: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"  Reason: {result.stop_reason}")
    print(f"  Steps: {result.steps_executed}")
    print(f"  Run ID: {result.run_id}")
    print(f"{'=' * 50}\n")

    return 0 if result.success else 1


def _list_skills() -> None:
    """List all learned skills."""
    try:
        from agent.autonomous.skill_library import get_skill_library

        library = get_skill_library()
        library.initialize()

        skills = library.list_skills()

        if not skills:
            print("\nNo skills learned yet. Use 'learn <task>' to teach me something new.\n")
            return

        print(f"\n{'=' * 50}")
        print(f"  LEARNED SKILLS ({len(skills)})")
        print(f"{'=' * 50}")

        for skill in skills:
            success_rate = "N/A"
            if skill.success_count + skill.failure_count > 0:
                rate = skill.success_count / (skill.success_count + skill.failure_count) * 100
                success_rate = f"{rate:.0f}%"

            print(f"\n  [{skill.id}] {skill.name}")
            print(f"      {skill.description[:60]}...")
            print(f"      Tags: {', '.join(skill.tags) or 'none'}")
            print(f"      Success rate: {success_rate} ({skill.success_count}/{skill.success_count + skill.failure_count})")

        print(f"\n{'=' * 50}\n")

    except Exception as e:
        print(f"[ERROR] Could not list skills: {e}")


def _run_learning_agent(llm, task: str, force_learn: bool = False) -> None:
    """Run the learning agent on a task."""
    try:
        from agent.autonomous.learning_agent import get_learning_agent

        agent = get_learning_agent(llm)

        # Set up callbacks
        def on_status(msg):
            print(f"  [STATUS] {msg}")

        def on_user_input(question):
            print(f"\n  [AGENT ASKS] {question}")
            return input("  > ").strip()

        agent.on_status = on_status
        agent.on_user_input = on_user_input

        print(f"\n{'=' * 50}")
        print("  LEARNING AGENT")
        print(f"{'=' * 50}")
        print(f"\n  Task: {task}")
        print(f"  Mode: {'Force Learn' if force_learn else 'Auto'}\n")

        # Run the agent
        result = agent.run(task)

        print(f"\n{'=' * 50}")
        print(f"  Result: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"  Summary: {result.summary}")
        if result.skill_used:
            print(f"  Skill used: {result.skill_used}")
        if result.skill_learned:
            print(f"  NEW SKILL LEARNED: {result.skill_learned}")
        if result.research_performed:
            print("  (Research was performed)")
        print(f"  Steps: {result.steps_taken}")
        print(f"{'=' * 50}\n")

    except Exception as e:
        import traceback
        print(f"[ERROR] Learning agent failed: {e}")
        traceback.print_exc()


def _needs_learning_agent(text: str) -> bool:
    """Check if this task should use the learning agent."""
    lower = text.lower()

    # Keywords that suggest complex tasks needing learning
    learning_keywords = [
        "calendar", "outlook", "gmail", "email", "schedule",
        "oauth", "authenticate", "login", "sign in",
        "api", "integrate", "connect", "setup", "configure",
        "automate", "browser", "website", "web page",
    ]

    return any(kw in lower for kw in learning_keywords)


def _is_simple_query(text: str) -> bool:
    """Check if this is a simple query that doesn't need the full agent loop."""
    lower = text.lower().strip()

    # Simple patterns that don't need tools/planning
    simple_patterns = [
        # Math
        lambda t: all(c in "0123456789+-*/=().? " for c in t.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")),
        # What is X questions
        lambda t: t.startswith("what is ") and len(t) < 50,
        # Define/explain simple concepts
        lambda t: t.startswith("define ") and len(t) < 100,
        lambda t: t.startswith("explain ") and len(t) < 100,
        # Simple greetings/chat
        lambda t: t in {"hi", "hello", "hey", "thanks", "thank you", "ok", "okay"},
    ]

    return any(p(lower) for p in simple_patterns)


def _fast_answer(llm, query: str) -> Optional[str]:
    """Get a quick answer using Codex chat mode (no agent overhead)."""
    try:
        # Use chat method if available (much faster than full exec)
        if hasattr(llm, "chat"):
            result = llm.chat(query, timeout_seconds=30)
            if result:
                return result

        # Fallback to call_codex
        if hasattr(llm, "call_codex"):
            result = llm.call_codex(query, timeout_seconds=30)
            if isinstance(result, dict):
                return result.get("result") or result.get("answer") or str(result)
    except Exception:
        pass
    return None


def interactive_loop() -> int:
    """
    Run an interactive REPL that feeds tasks to AgentRunner.

    This replaces the old treys_agent.py routing logic.
    """
    from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
    from agent.autonomous.runner import AgentRunner

    _setup_logging(verbose=False)

    print("\n" + "=" * 50)
    print("          TREY'S AGENT - Interactive Mode")
    print("=" * 50)
    print("\nType your task and press Enter. Type 'exit' to quit.")
    print("Commands: help, tools, skills, learn, exit\n")

    # Get LLM client once
    try:
        llm = _get_llm_client()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        return 1

    while True:
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return 0

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in {"exit", "quit", "q"}:
            print("Goodbye!")
            return 0

        if lower in {"help", "?"}:
            print("""
Commands:
  <task>       - Run a task (uses Learning Agent for complex tasks)
  learn <task> - Force learning mode (research + learn new skill)
  tools        - List all available tools (local + MCP)
  skills       - List all learned skills
  help         - Show this help
  exit         - Quit

Examples:
  > what's on my calendar tomorrow
  > learn how to access outlook calendar
  > create a simple calculator script
  > search the web for Python best practices 2024
""")
            continue

        if lower == "tools":
            list_all_tools()
            continue

        if lower == "skills":
            _list_skills()
            continue

        if lower.startswith("learn "):
            # Force learning mode
            task = user_input[6:].strip()
            if task:
                _run_learning_agent(llm, task, force_learn=True)
            else:
                print("Usage: learn <task>")
            continue

        # Fast path for simple queries (no agent overhead)
        if _is_simple_query(user_input):
            print(f"\n[TASK] {user_input}")
            answer = _fast_answer(llm, user_input)
            if answer:
                print(f"[ANSWER] {answer}\n")
                continue
            # Fall through to full agent if fast path fails

        # Learning agent for complex tasks (calendar, email, OAuth, etc.)
        if _needs_learning_agent(user_input):
            _run_learning_agent(llm, user_input)
            continue

        # Everything else goes to AgentRunner
        runner_cfg = RunnerConfig(
            max_steps=30,
            timeout_seconds=600,
            profile="fast",  # Use fast profile for interactive - less overhead
            llm_heartbeat_seconds=5.0,
        )

        agent_cfg = AgentConfig(
            allow_human_ask=True,
            allow_interactive_tools=True,
        )

        planner_cfg = PlannerConfig(mode="react")

        runner = AgentRunner(
            cfg=runner_cfg,
            agent_cfg=agent_cfg,
            planner_cfg=planner_cfg,
            llm=llm,
        )

        print(f"\n[TASK] {user_input}")
        print("       Working...\n")

        result = runner.run(user_input)

        # Extract and display the answer
        answer = _extract_answer(result)
        if answer:
            print(f"\n[ANSWER] {answer}")

        status = "SUCCESS" if result.success else "FAILED"
        print(f"[{status}] {result.stop_reason} (steps: {result.steps_executed})\n")


def _extract_answer(result) -> Optional[str]:
    """Extract the answer from an agent result."""
    # Try to get answer from trace file
    try:
        from pathlib import Path
        import json

        if result.trace_path:
            trace_path = Path(result.trace_path)
            if trace_path.exists():
                # Read the trace file and find the finish tool call
                with open(trace_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            # Look for step with finish action
                            if entry.get("type") == "step":
                                action = entry.get("action", {})
                                if action.get("tool_name") == "finish":
                                    tool_args = action.get("tool_args", {})
                                    if isinstance(tool_args, dict):
                                        return tool_args.get("summary") or tool_args.get("answer") or tool_args.get("result")
                                    elif isinstance(tool_args, list):
                                        for arg in tool_args:
                                            if isinstance(arg, dict) and arg.get("key") in ("summary", "answer", "result"):
                                                return arg.get("value")
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        pass  # Silently fail - answer extraction is optional
    return None


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Unified Agent - Single loop, single registry, one decision per step",
    )

    parser.add_argument(
        "task",
        nargs="?",
        help="Task to execute (if not provided, enters interactive mode)",
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode (REPL)",
    )

    parser.add_argument(
        "-p", "--profile",
        default="deep",
        choices=["fast", "deep", "audit"],
        help="Execution profile (default: deep)",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=30,
        help="Maximum steps before stopping (default: 30)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds (default: 600)",
    )

    parser.add_argument(
        "--resume",
        type=str,
        help="Path to checkpoint to resume from",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Run legacy treys_agent.py (for backward compatibility)",
    )

    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all available tools (local + MCP) and exit",
    )

    args = parser.parse_args()

    # List tools mode - for debugging/verification
    if args.list_tools:
        list_all_tools()
        return

    # Legacy mode - run old treys_agent
    if args.legacy:
        from agent._legacy.treys_agent_legacy import main as legacy_main
        legacy_main()
        return

    # Interactive mode
    if args.interactive or (args.task is None and not args.resume):
        sys.exit(interactive_loop())

    # Single task mode
    if args.task:
        resume_path = Path(args.resume) if args.resume else None
        exit_code = run_agent(
            args.task,
            profile=args.profile,
            max_steps=args.max_steps,
            timeout_seconds=args.timeout,
            interactive=True,
            verbose=args.verbose,
            resume_path=resume_path,
        )
        sys.exit(exit_code)

    # Resume mode
    if args.resume:
        resume_path = Path(args.resume)
        # Load task from checkpoint
        import json
        checkpoint_file = resume_path / "checkpoint.json" if resume_path.is_dir() else resume_path
        if checkpoint_file.exists():
            data = json.loads(checkpoint_file.read_text())
            task = data.get("task", "Resume previous task")
        else:
            task = "Resume previous task"

        exit_code = run_agent(
            task,
            profile=args.profile,
            max_steps=args.max_steps,
            timeout_seconds=args.timeout,
            interactive=True,
            verbose=args.verbose,
            resume_path=resume_path,
        )
        sys.exit(exit_code)

    parser.print_help()


if __name__ == "__main__":
    main()
