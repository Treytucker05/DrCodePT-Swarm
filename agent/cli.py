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
import re
import time
import json
from dataclasses import dataclass
from typing import Optional, Tuple, List, Any
from datetime import datetime

from agent.autonomous.runner import AgentRunner
from agent.autonomous.config import RunnerConfig, AgentConfig, PlannerConfig
from agent.autonomous.memory.sqlite_store import SqliteMemoryStore
from agent.config.profile import ProfileName
from agent.llm.base import LLMClient

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


def _get_llm_client(backend: str = "codex_cli", model: Optional[str] = None):
    """Get the LLM client based on environment configuration.

    Prefers Codex CLI when available.
    Falls back to OpenRouter if Codex is unavailable.
    """
    if backend == "server":
        try:
            from agent.llm.server_client import ServerClient
            client = ServerClient.from_env()
            if model and model != "default" and hasattr(client, "set_model"):
                client.set_model(model)
            return client
        except Exception as e:
            logger.debug(f"ServerClient init failed: {e}")
            # Fallback to codex_cli
            pass

    try:
        from agent.llm.codex_cli_client import CodexCliClient
        client = CodexCliClient.from_env()
        # Don't block on auth check - let Codex try at runtime
        if hasattr(client, "check_auth"):
            try:
                if not client.check_auth():
                    logger.warning("Codex auth check failed, but will attempt to use Codex anyway...")
            except Exception:
                logger.warning("Codex auth check error, but will attempt to use Codex anyway...")
        return client
    except Exception as e:
        logger.debug(f"CodexCliClient not available: {e}")

    if os.getenv("OPENROUTER_API_KEY"):
        try:
            from agent.llm.openrouter_client import OpenRouterClient
            client = OpenRouterClient.from_env()
            if model and model != "default":
                client.model = model
            return client
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
    backend: str = "codex_cli",
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
        llm = _get_llm_client(backend=backend)
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


def _is_local_task_hint(task: str, skill=None) -> bool:
    """Heuristic to detect local desktop automation tasks."""
    if skill is not None:
        try:
            tags = {t.lower() for t in (skill.tags or [])}
            if tags & {"notepad", "open_app", "desktop", "calculator"}:
                return True
        except Exception:
            pass
    lower = task.lower()
    local_keywords = [
        "notepad",
        "calculator",
        "paint",
        "wordpad",
        "file explorer",
        "start menu",
        "desktop",
        "window",
    ]
    return any(k in lower for k in local_keywords)


def _try_run_learned_skill(llm, task: str) -> bool:
    """Run a learned skill if a strong match exists."""
    try:
        from agent.autonomous.skill_library import get_skill_library
        from agent.autonomous.learning_agent import get_learning_agent

        library = get_skill_library()
        library.initialize()
        matches = library.search(task, k=3)
        if not matches:
            return False

        best_skill, similarity = matches[0]
        agent = get_learning_agent(llm)

        def on_status(msg: str) -> None:
            lowered = msg.lower()
            if lowered.startswith("learning agent initialized"):
                return
            if lowered.startswith("using hybrid executor"):
                return
            print(f"  [SKILL] {msg}")

        agent.on_status = on_status
        agent.on_user_input = lambda question: input("  > ").strip()
        agent.initialize()

        is_local = _is_local_task_hint(task, best_skill)
        threshold = agent._skill_match_threshold(is_local)
        if similarity < threshold:
            return False

        print(f"\n{'=' * 50}")
        print("  USING LEARNED SKILL")
        print(f"{'=' * 50}")
        print(f"  Skill: {best_skill.name} ({best_skill.id})")
        print(f"  Match: {similarity:.0%} (threshold {threshold:.0%})\n")

        result = agent._execute_skill(best_skill, task)

        print(f"\n{'=' * 50}")
        print(f"  Result: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"  Summary: {result.summary}")
        print(f"  Steps: {result.steps_taken}")
        print(f"{'=' * 50}\n")

        return result.success
    except Exception as e:
        print(f"[WARN] Failed to run learned skill: {e}")
        return False


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
            skill_label = result.skill_learned
            try:
                from agent.autonomous.skill_library import get_skill_library
                library = get_skill_library()
                library.initialize()
                skill = library.get(result.skill_learned)
                if skill:
                    skill_label = f"{skill.name} ({skill.id})"
            except Exception:
                pass
            print(f"  NEW SKILL LEARNED: {skill_label}")
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
    # Note: "calendar" removed - calendar requests should use existing calendar tools
    learning_keywords = [
        # Email (but not calendar - calendar has MCP tools available)
        "outlook", "gmail", "email",
        # Auth (for new integrations)
        "oauth", "authenticate", "login", "sign in",
        # Integration (for new setups)
        "api", "integrate", "connect", "setup", "configure",
        # Web automation (for new sites)
        "automate", "browser", "website", "web page",
        # Desktop automation - USE LEARNING AGENT for these
        "notepad", "calculator", "open", "launch", "type", "write", "click",
        "window", "application", "app", "desktop",
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





@dataclass
class CLISettings:
    model: str = "default"
    profile: ProfileName = "fast"
    mode: str = "react"
    
    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({
                "model": self.model,
                "profile": self.profile,
                "mode": self.mode
            }, f)
            
    @classmethod
    def load(cls, path: Path) -> "CLISettings":
        if not path.exists():
            return cls()
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return cls(**data)
        except Exception:
            return cls()

def _print_settings_menu(settings: CLISettings):
    print("\n" + "="*30)
    print("      SETTINGS MENU")
    print("="*30)
    print(f"  Model:   {settings.model}")
    print(f"  Profile: {settings.profile}  (fast = low latency, deep = high reasoning)")
    print(f"  Mode:    {settings.mode}")
    print("-"*30)
    print("  Commands: ")
    print("    /model <name>   - Change LLM model")
    print("    /profile <fast|deep|audit> - Change reasoning depth")
    print("    /settings       - Show this menu")
    print("="*30 + "\n")

def interactive_loop(backend: str = "codex_cli") -> int:
    """
    Run an interactive REPL that feeds tasks to AgentRunner.

    This replaces the old treys_agent.py routing logic.
    Uses persistent memory across all tasks so the agent learns and remembers.
    """
    _setup_logging(verbose=False)

    print("\n" + "=" * 50)
    print("          🚀 TREY'S AGENT - Interactive Mode")
    print("=" * 50)
    print("\nType your task and press Enter. Type 'exit' to quit.")
    print("Commands: /settings, help, tools, skills, learn, exit\n")

    settings_path = Path.home() / ".drcodept_swarm" / "cli_settings.json"
    settings = CLISettings.load(settings_path)

    # Get LLM client with initial model from settings
    backend_val = "server" if os.environ.get("LLM_BACKEND") == "server" else "codex_cli"
    try:
        llm = _get_llm_client(backend=backend_val, model=settings.model)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        return 1

    # Create persistent memory store that persists across all tasks in this session
    memory_store = None
    try:
        repo_root = Path(__file__).resolve().parent.parent
        memory_path = repo_root / "agent" / "memory" / "autonomous_memory.sqlite3"
        memory_path.parent.mkdir(parents=True, exist_ok=True)
        memory_store = SqliteMemoryStore(path=memory_path)
        print(f"[MEMORY] Using persistent memory: {memory_path}")
        print(f"[MEMORY] Agent will remember past tasks and learn from experience")
    except Exception as e:
        logger.debug(f"Could not initialize persistent memory: {e}")
        print(f"[WARNING] Persistent memory unavailable - agent won't remember past tasks")

    session_history: List[str] = []

    while True:
        try:
            user_input = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return 0

        if not user_input:
            continue

        if user_input.lower() == "exit":
            break
            
        if user_input.lower().startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()
            
            if cmd == "/settings":
                _print_settings_menu(settings)
                continue
            elif cmd == "/model":
                if len(parts) > 1:
                    settings.model = parts[1]
                    settings.save(settings_path)
                    # Re-initialize LLM with new model
                    try:
                        llm = _get_llm_client(backend=backend_val, model=settings.model)
                        print(f"[OK] Model set to: {settings.model}")
                    except Exception as e:
                        print(f"[ERROR] Failed to switch model: {e}")
                else:
                    print("[ERROR] Please specify a model name.")
                continue
            elif cmd == "/profile":
                if len(parts) > 1 and parts[1] in ("fast", "deep", "audit"):
                    settings.profile = parts[1]
                    settings.save(settings_path)
                    print(f"[OK] Profile set to: {settings.profile}")
                else:
                    print("[ERROR] Profile must be 'fast', 'deep', or 'audit'.")
                continue
            elif cmd == "/help":
                print("\nAvailable commands:")
                print("  /settings - View current settings")
                print("  /model    - Set LLM model")
                print("  /profile  - Set reasoning profile (fast/deep/audit)")
                print("  exit      - Close the agent\n")
                continue
            continue

        lower = user_input.lower()

        if lower in {"exit", "quit", "q"}:
            print("Goodbye!")
            return 0

        if lower in {"help", "?"}:
            print("""
Commands:
  <task>       - Run a task (uses Learning Agent for complex tasks)
  /settings    - Change Model, Speed (fast/deep), and Reasoning settings
  /model       - Switch LLM model (e.g., /model gpt-4)
  /profile     - Switch speed (e.g., /profile fast OR /profile deep OR /profile audit)
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

        # Route all natural language tasks to the AgentRunner "Brain"
        # This fulfills the user goal of reasoning before fetching programs/tools.
        
        # Use persistent settings for runner config
        runner_cfg = RunnerConfig(
            max_steps=30,
            timeout_seconds=600,
            profile=settings.profile,
            llm_heartbeat_seconds=5.0,
        )

        agent_cfg = AgentConfig(
            allow_human_ask=True,
            allow_interactive_tools=True,
            memory_db_path=Path(memory_store.path) if memory_store else None,
        )

        planner_cfg = PlannerConfig(mode=settings.mode)

        runner = AgentRunner(
            cfg=runner_cfg,
            agent_cfg=agent_cfg,
            planner_cfg=planner_cfg,
            llm=llm,
            memory_store=memory_store,  # Share memory across all tasks
        )

        print(f"\n[TASK] {user_input}")
        print("       Working...\n")

        # Inject local time and session history for context
        now = datetime.now()
        # Try to get timezone name natively
        try:
            import tzlocal
            tz = tzlocal.get_localzone_name()
        except ImportError:
            # Fallback to a simple Windows command if needed, or just use the offset
            tz = datetime.now().astimezone().tzname()
        
        local_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        full_task = f"Current Local Time: {local_time_str} ({tz})\n"
        if session_history:
            history_text = "\n".join(session_history[-3:]) # Keep last 3 turns
            full_task += f"Context from previous turns in this session:\n{history_text}\n"
        
        full_task += f"Current Task: {user_input}"

        result = runner.run(full_task)

        # Extract and display the answer
        answer = _extract_answer(result)
        if answer:
            print(f"\n[ANSWER] {answer}")
            session_history.append(f"User: {user_input}\nAssistant: {answer}")
            # ALSO store in persistent memory for cross-session learning
            if memory_store:
                memory_store.upsert(
                    kind="conversation",
                    key=f"turn_{int(time.time())}",
                    content=f"User Task: {user_input}\nAssistant Answer: {answer}",
                    metadata={"task": user_input}
                )
        else:
            session_history.append(f"User: {user_input}\nAssistant: (Task completed with stop reason: {result.stop_reason})")

        status = "SUCCESS" if result.success else "FAILED"
        print(f"[{status}] {result.stop_reason} (steps: {result.steps_executed})\n")


def _extract_answer(result) -> Optional[str]:
    """Extract the answer from an agent result."""
    # Try to get answer from trace file
    try:
        from pathlib import Path
        import json
        from datetime import datetime

        if result.trace_path:
            trace_path = Path(result.trace_path)
            if trace_path.exists():
                last_successful_output = None
                last_tool_name = None

                # Read the trace file and find the finish tool call OR last successful output
                with open(trace_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            # Look for step with finish action
                            if entry.get("type") == "step":
                                action = entry.get("action", {})
                                tool_result = entry.get("result", {})

                                if action.get("tool_name") == "finish":
                                    tool_args = action.get("tool_args", {})
                                    if isinstance(tool_args, dict):
                                        return tool_args.get("summary") or tool_args.get("answer") or tool_args.get("result")
                                    elif isinstance(tool_args, list):
                                        for arg in tool_args:
                                            if isinstance(arg, dict) and arg.get("key") in ("summary", "answer", "result"):
                                                return arg.get("value")

                                # If tool succeeded and has output, remember it
                                if tool_result.get("success"):
                                    last_tool_name = action.get("tool_name")
                                    last_successful_output = tool_result.get("output")
                        except json.JSONDecodeError:
                            continue

                # If no finish tool was called but we have calendar/tasks results, format them
                if last_successful_output and last_tool_name == "list_calendar_events":
                    events = last_successful_output.get("events", [])
                    if events:
                        answer = f"Found {len(events)} event(s):\n\n"
                        for event in events:
                            start = event.get("start", {}).get("dateTime", "")
                            end = event.get("end", {}).get("dateTime", "")
                            summary = event.get("summary", "Untitled")

                            # Parse and format times
                            try:
                                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                                time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
                            except:
                                time_str = f"{start} - {end}"

                            answer += f"  • {summary}: {time_str}\n"
                        return answer.strip()
                    else:
                        return "No events found in that time range."

                elif last_successful_output and last_tool_name == "list_all_tasks":
                    tasks = last_successful_output.get("tasks", [])
                    if tasks:
                        answer = f"Found {len(tasks)} task(s):\n\n"
                        for task in tasks:
                            title = task.get("title", "Untitled")
                            answer += f"  • {title}\n"
                        return answer.strip()
                    else:
                        return "No tasks found."

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
        "--llm-backend",
        choices=["codex_cli", "server"],
        default="codex_cli",
        help="LLM backend to use (default: codex_cli)",
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
        # Set backend in env so loops can pick it up
        os.environ["LLM_BACKEND"] = args.llm_backend
        sys.exit(interactive_loop(backend=args.llm_backend))

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
            backend=args.llm_backend,
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
            backend=args.llm_backend,
        )
        sys.exit(exit_code)

    parser.print_help()


if __name__ == "__main__":
    main()
