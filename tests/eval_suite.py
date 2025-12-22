"""
Evaluation suite for DrCodePT-Swarm autonomous agent.

Run with: python -m tests.eval_suite

This suite tests:
- Basic tool execution (file ops, shell, Python)
- Multi-step planning
- Error recovery and retry behavior
- Loop detection
- Memory persistence
- Research capabilities (if web tools enabled)
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Ensure repo root is in path
import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class EvalCheck:
    """A single verification check for a task."""
    name: str
    check_fn: Callable[[Dict[str, Any]], bool]
    description: str = ""


@dataclass
class EvalTask:
    """A task to evaluate the agent on."""
    name: str
    task: str
    checks: List[EvalCheck]
    category: str = "general"
    timeout_seconds: int = 120
    max_steps: int = 20
    setup_fn: Optional[Callable[[Path], None]] = None
    cleanup_fn: Optional[Callable[[Path], None]] = None


@dataclass
class EvalResult:
    """Result of running a single eval task."""
    name: str
    category: str
    task: str
    success: bool
    checks_passed: int
    checks_total: int
    score: float
    stop_reason: str
    steps_executed: int
    duration_seconds: float
    error: Optional[str] = None
    check_details: Dict[str, bool] = field(default_factory=dict)


# =============================================================================
# Helper functions for checks
# =============================================================================

def file_exists(path: str) -> Callable[[Dict], bool]:
    """Check if a file exists in the workspace."""
    def check(ctx: Dict) -> bool:
        workspace = ctx.get("workspace_dir", Path.cwd())
        return (Path(workspace) / path).exists()
    return check


def file_contains(path: str, content: str) -> Callable[[Dict], bool]:
    """Check if a file contains specific content."""
    def check(ctx: Dict) -> bool:
        workspace = ctx.get("workspace_dir", Path.cwd())
        file_path = Path(workspace) / path
        if not file_path.exists():
            return False
        return content in file_path.read_text(encoding="utf-8", errors="ignore")
    return check


def dir_exists(path: str) -> Callable[[Dict], bool]:
    """Check if a directory exists."""
    def check(ctx: Dict) -> bool:
        workspace = ctx.get("workspace_dir", Path.cwd())
        return (Path(workspace) / path).is_dir()
    return check


def file_count_in_dir(path: str, expected: int) -> Callable[[Dict], bool]:
    """Check if a directory has expected number of files."""
    def check(ctx: Dict) -> bool:
        workspace = ctx.get("workspace_dir", Path.cwd())
        dir_path = Path(workspace) / path
        if not dir_path.is_dir():
            return False
        files = [f for f in dir_path.iterdir() if f.is_file()]
        return len(files) == expected
    return check


def steps_under(n: int) -> Callable[[Dict], bool]:
    """Check if task completed in under N steps."""
    def check(ctx: Dict) -> bool:
        return ctx.get("steps_executed", 999) < n
    return check


def stopped_gracefully() -> Callable[[Dict], bool]:
    """Check if agent stopped gracefully (not max_steps or timeout)."""
    def check(ctx: Dict) -> bool:
        return ctx.get("stop_reason") in ("goal_achieved", "finish")
    return check


def did_not_loop() -> Callable[[Dict], bool]:
    """Check if agent didn't hit loop detection."""
    def check(ctx: Dict) -> bool:
        return ctx.get("stop_reason") != "loop_detected"
    return check


def tool_was_called(tool_name: str) -> Callable[[Dict], bool]:
    """Check if a specific tool was called."""
    def check(ctx: Dict) -> bool:
        return tool_name in ctx.get("tools_called", [])
    return check


def task_succeeded() -> Callable[[Dict], bool]:
    """Check if the agent reported success."""
    def check(ctx: Dict) -> bool:
        return ctx.get("agent_success", False)
    return check


def _stub_plan_for(task_spec: EvalTask) -> Dict[str, Any]:
    if task_spec.name == "file_write_read":
        return {
            "goal": "Write hello.txt",
            "steps": [
                {
                    "id": "step_1",
                    "goal": "Write hello.txt",
                    "rationale_short": "Stubbed plan for file write",
                    "tool_name": "file_write",
                    "tool_args": [
                        {"key": "path", "value": "hello.txt"},
                        {"key": "content", "value": "Hello, World!"},
                        {"key": "mode", "value": "overwrite"},
                    ],
                    "success_criteria": [],
                    "preconditions": [],
                    "postconditions": [],
                }
            ],
        }
    if task_spec.name == "python_calculation":
        code = (
            "import math\n"
            "with open('factorial.txt', 'w', encoding='utf-8') as f:\n"
            "    f.write(str(math.factorial(10)))\n"
        )
        return {
            "goal": "Compute factorial",
            "steps": [
                {
                    "id": "step_1",
                    "goal": "Compute factorial of 10",
                    "rationale_short": "Stubbed plan using python_exec",
                    "tool_name": "python_exec",
                    "tool_args": [{"key": "code", "value": code}],
                    "success_criteria": [],
                    "preconditions": [],
                    "postconditions": [],
                }
            ],
        }
    if task_spec.name == "shell_command":
        return {
            "goal": "Create marker file",
            "steps": [
                {
                    "id": "step_1",
                    "goal": "Create test_dir/marker.txt",
                    "rationale_short": "Stubbed plan using file_write",
                    "tool_name": "file_write",
                    "tool_args": [
                        {"key": "path", "value": "test_dir/marker.txt"},
                        {"key": "content", "value": ""},
                        {"key": "mode", "value": "overwrite"},
                    ],
                    "success_criteria": [],
                    "preconditions": [],
                    "postconditions": [],
                }
            ],
        }
    return {
        "goal": "Finish",
        "steps": [
            {
                "id": "step_1",
                "goal": "Finish quickly",
                "rationale_short": "Stubbed plan default",
                "tool_name": "finish",
                "tool_args": [{"key": "summary", "value": "stub"}],
                "success_criteria": [],
                "preconditions": [],
                "postconditions": [],
            }
        ],
    }


def _stub_reflection() -> Dict[str, Any]:
    return {
        "status": "success",
        "explanation_short": "stub",
        "next_hint": "",
        "failure_type": "none",
        "lesson": "",
        "memory_write": None,
    }


def _stub_finish_plan() -> Dict[str, Any]:
    return {
        "goal": "Finish",
        "steps": [
            {
                "id": "step_finish",
                "goal": "Finish",
                "rationale_short": "Stubbed finish step",
                "tool_name": "finish",
                "tool_args": [{"key": "summary", "value": "stub"}],
                "success_criteria": [],
                "preconditions": [],
                "postconditions": [],
            }
        ],
    }

# =============================================================================
# Eval Tasks
# =============================================================================

EVAL_TASKS: List[EvalTask] = [
    # -------------------------------------------------------------------------
    # Category: Basic Tool Execution
    # -------------------------------------------------------------------------
    EvalTask(
        name="file_write_read",
        category="basic",
        task="Create a file called 'hello.txt' containing 'Hello, World!'",
        checks=[
            EvalCheck("file_created", file_exists("hello.txt"), "File was created"),
            EvalCheck("content_correct", file_contains("hello.txt", "Hello, World!"), "Content matches"),
            EvalCheck("efficient", steps_under(5), "Completed in under 5 steps"),
        ],
    ),
    
    EvalTask(
        name="python_calculation",
        category="basic",
        task="Use Python to calculate the factorial of 10 and save the result to 'factorial.txt'",
        checks=[
            EvalCheck("file_created", file_exists("factorial.txt"), "Output file created"),
            EvalCheck("correct_answer", file_contains("factorial.txt", "3628800"), "Factorial is correct"),
            EvalCheck("used_python", tool_was_called("python_exec"), "Used Python execution"),
        ],
    ),
    
    EvalTask(
        name="shell_command",
        category="basic",
        task="Run a shell command to create a directory called 'test_dir' and create an empty file 'test_dir/marker.txt' inside it",
        checks=[
            EvalCheck("dir_created", dir_exists("test_dir"), "Directory was created"),
            EvalCheck("file_created", file_exists("test_dir/marker.txt"), "Marker file exists"),
            EvalCheck("efficient", steps_under(6), "Completed efficiently"),
        ],
    ),

    # -------------------------------------------------------------------------
    # Category: Multi-Step Planning
    # -------------------------------------------------------------------------
    EvalTask(
        name="project_structure",
        category="planning",
        task="Create a Python project structure with: a 'myproject' folder containing 'src/', 'tests/', and 'docs/' subdirectories, plus a README.md file in the root myproject folder",
        checks=[
            EvalCheck("root_dir", dir_exists("myproject"), "Project root exists"),
            EvalCheck("src_dir", dir_exists("myproject/src"), "src/ directory exists"),
            EvalCheck("tests_dir", dir_exists("myproject/tests"), "tests/ directory exists"),
            EvalCheck("docs_dir", dir_exists("myproject/docs"), "docs/ directory exists"),
            EvalCheck("readme", file_exists("myproject/README.md"), "README.md exists"),
            EvalCheck("efficient", steps_under(12), "Completed in reasonable steps"),
        ],
        max_steps=15,
    ),
    
    EvalTask(
        name="numbered_files",
        category="planning",
        task="Create a folder called 'output' and inside it create 5 text files named 'file_1.txt' through 'file_5.txt', each containing its own number",
        checks=[
            EvalCheck("output_dir", dir_exists("output"), "Output directory exists"),
            EvalCheck("file_count", file_count_in_dir("output", 5), "Exactly 5 files created"),
            EvalCheck("file_1", file_contains("output/file_1.txt", "1"), "file_1.txt has correct content"),
            EvalCheck("file_5", file_contains("output/file_5.txt", "5"), "file_5.txt has correct content"),
        ],
        max_steps=15,
    ),
    
    EvalTask(
        name="data_processing",
        category="planning",
        task="Create a CSV file called 'data.csv' with columns 'name,age,city' and 3 rows of sample data. Then use Python to read it and create 'summary.txt' with the average age.",
        checks=[
            EvalCheck("csv_created", file_exists("data.csv"), "CSV file created"),
            EvalCheck("csv_has_header", file_contains("data.csv", "name,age,city"), "CSV has correct header"),
            EvalCheck("summary_created", file_exists("summary.txt"), "Summary file created"),
            EvalCheck("used_python", tool_was_called("python_exec"), "Used Python for processing"),
        ],
        max_steps=12,
    ),

    # -------------------------------------------------------------------------
    # Category: Error Recovery
    # -------------------------------------------------------------------------
    EvalTask(
        name="missing_file_recovery",
        category="recovery",
        task="Try to read a file called 'nonexistent.txt'. When it fails, create the file with the content 'Created after failed read'",
        checks=[
            EvalCheck("attempted_read", tool_was_called("file_read"), "Attempted to read file"),
            EvalCheck("file_created", file_exists("nonexistent.txt"), "File was created after failure"),
            EvalCheck("correct_content", file_contains("nonexistent.txt", "Created"), "Has expected content"),
            EvalCheck("graceful", stopped_gracefully(), "Stopped gracefully"),
        ],
    ),
    
    EvalTask(
        name="invalid_python_recovery",
        category="recovery",
        task="Run this Python code: 'print(undefined_variable)'. When it fails, fix it by defining the variable as 'fixed' and run again, saving 'success' to 'recovery.txt'",
        checks=[
            EvalCheck("attempted_bad_code", tool_was_called("python_exec"), "Attempted Python execution"),
            EvalCheck("recovery_file", file_exists("recovery.txt"), "Recovery file created"),
            EvalCheck("recovered", file_contains("recovery.txt", "success"), "Successfully recovered"),
        ],
        max_steps=10,
    ),

    # -------------------------------------------------------------------------
    # Category: Loop Detection & Boundaries
    # -------------------------------------------------------------------------
    EvalTask(
        name="impossible_task",
        category="boundaries",
        task="Find a file called 'unicorn_rainbow_42.txt' in the current directory. Search thoroughly but give up gracefully if not found.",
        checks=[
            EvalCheck("didnt_loop", did_not_loop(), "Didn't get stuck in a loop"),
            EvalCheck("stopped_reasonably", steps_under(15), "Stopped in reasonable steps"),
            EvalCheck("graceful_exit", stopped_gracefully(), "Exited gracefully"),
        ],
        max_steps=20,
    ),
    
    EvalTask(
        name="ambiguous_task",
        category="boundaries",
        task="Do something interesting with files",
        checks=[
            EvalCheck("took_action", lambda ctx: ctx.get("steps_executed", 0) > 0, "Took some action"),
            EvalCheck("didnt_crash", lambda ctx: ctx.get("error") is None, "Didn't crash"),
            EvalCheck("finished", stopped_gracefully(), "Finished gracefully"),
        ],
        max_steps=10,
    ),

    # -------------------------------------------------------------------------
    # Category: Memory
    # -------------------------------------------------------------------------
    EvalTask(
        name="memory_store_retrieve",
        category="memory",
        task="Store the fact 'The secret code is 12345' in memory with key 'secret'. Then search memory for 'secret code' and write what you find to 'retrieved.txt'",
        checks=[
            EvalCheck("used_memory_store", tool_was_called("memory_store"), "Used memory_store"),
            EvalCheck("used_memory_search", tool_was_called("memory_search"), "Used memory_search"),
            EvalCheck("retrieved_file", file_exists("retrieved.txt"), "Created retrieval output"),
            EvalCheck("correct_content", file_contains("retrieved.txt", "12345"), "Retrieved correct content"),
        ],
        max_steps=10,
    ),

    # -------------------------------------------------------------------------
    # Category: Complex / Integration
    # -------------------------------------------------------------------------
    EvalTask(
        name="todo_app",
        category="complex",
        task="""Create a simple todo list manager:
1. Create 'todos.json' with an empty list
2. Use Python to add 3 todos: 'Buy groceries', 'Call mom', 'Finish project'
3. Use Python to mark the second todo as complete
4. Save the final state to 'todos_final.json'""",
        checks=[
            EvalCheck("initial_json", file_exists("todos.json"), "Initial JSON created"),
            EvalCheck("final_json", file_exists("todos_final.json"), "Final JSON created"),
            EvalCheck("has_todos", file_contains("todos_final.json", "Buy groceries"), "Contains todo items"),
            EvalCheck("has_complete", file_contains("todos_final.json", "complete"), "Has completion status"),
        ],
        max_steps=15,
        timeout_seconds=180,
    ),
    
    EvalTask(
        name="log_analyzer",
        category="complex",
        task="""Create a mock log file 'app.log' with 10 lines including some 'ERROR' and some 'INFO' entries.
Then use Python to analyze it and create 'analysis.txt' containing:
- Total line count
- Number of ERROR lines
- Number of INFO lines""",
        checks=[
            EvalCheck("log_created", file_exists("app.log"), "Log file created"),
            EvalCheck("analysis_created", file_exists("analysis.txt"), "Analysis file created"),
            EvalCheck("has_total", file_contains("analysis.txt", "10"), "Shows total count"),
            EvalCheck("mentions_error", file_contains("analysis.txt", "ERROR"), "Analyzes ERROR entries"),
        ],
        max_steps=12,
    ),
]

# =============================================================================
# Eval Runner
# =============================================================================

def extract_tools_from_trace(trace_path: Optional[str]) -> List[str]:
    """Extract list of tools called from a trace file."""
    if not trace_path or not Path(trace_path).exists():
        return []
    
    tools = []
    try:
        with open(trace_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "step":
                        action = entry.get("action", {})
                        tool_name = action.get("tool_name")
                        if tool_name:
                            tools.append(tool_name)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    
    return tools


class EvalRunner:
    """Runs evaluation tasks against the agent."""
    
    def __init__(
        self,
        eval_dir: Optional[Path] = None,
        verbose: bool = True,
        use_stub_llm: bool = False,
    ):
        self.eval_dir = (eval_dir or Path("runs/eval") / datetime.now().strftime("%Y%m%d_%H%M%S")).resolve()
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.use_stub_llm = use_stub_llm
        self.results: List[EvalResult] = []
    
    def log(self, msg: str) -> None:
        if self.verbose:
            print(msg)
    
    def run_task(self, task_spec: EvalTask) -> EvalResult:
        """Run a single eval task."""
        self.log(f"\n{'='*60}")
        self.log(f"📋 Task: {task_spec.name}")
        self.log(f"📁 Category: {task_spec.category}")
        self.log(f"{'='*60}")
        self.log(f"Prompt: {task_spec.task[:100]}...")
        
        # Setup workspace
        workspace = self.eval_dir / task_spec.name / "workspace"
        run_dir = self.eval_dir / task_spec.name / "run"
        workspace.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(parents=True, exist_ok=True)
        workspace = workspace.resolve()
        run_dir = run_dir.resolve()
        
        # Run setup if provided
        if task_spec.setup_fn:
            try:
                task_spec.setup_fn(workspace)
            except Exception as e:
                self.log(f"⚠️  Setup failed: {e}")
        
        start_time = time.time()
        error = None
        agent_result = None
        
        try:
            # Import here to avoid circular imports
            from agent.autonomous.config import AgentConfig, PlannerConfig, RunnerConfig
            from agent.autonomous.runner import AgentRunner
            from agent.llm.codex_cli_client import CodexCliClient
            
            # Configure agent
            runner_cfg = RunnerConfig(
                max_steps=task_spec.max_steps,
                timeout_seconds=task_spec.timeout_seconds,
            )
            agent_cfg = AgentConfig(
                memory_db_path=self.eval_dir / task_spec.name / "memory.sqlite3",
                enable_web_gui=False,
                enable_desktop=False,
                fs_allowed_roots=(REPO_ROOT,),
            )
            planner_cfg = PlannerConfig(mode="react")
            
            # Get LLM
            if self.use_stub_llm:
                from agent.autonomous.llm.stub import StubLLM
                llm = StubLLM(
                    responses=[
                        _stub_plan_for(task_spec),
                        _stub_reflection(),
                        _stub_finish_plan(),
                        _stub_reflection(),
                    ]
                )
            else:
                llm = CodexCliClient.from_env()
            
            # Create and run agent
            # Note: AgentRunner creates workspace_dir as run_dir/workspace
            runner = AgentRunner(
                cfg=runner_cfg,
                agent_cfg=agent_cfg,
                planner_cfg=planner_cfg,
                llm=llm,
                run_dir=run_dir,
            )
            
            task_with_permission = (
                "You have permission to create, modify, and read files in the workspace.\n"
                + task_spec.task
            )
            agent_result = runner.run(task_with_permission)
            
            # Update workspace to actual location created by runner
            workspace = run_dir / "workspace"
            
        except Exception as e:
            error = str(e)
            self.log(f"❌ Agent error: {error}")
        
        duration = time.time() - start_time
        
        # Build context for checks
        ctx = {
            "workspace_dir": workspace,
            "run_dir": run_dir,
            "steps_executed": agent_result.steps_executed if agent_result else 0,
            "stop_reason": agent_result.stop_reason if agent_result else "error",
            "agent_success": agent_result.success if agent_result else False,
            "tools_called": extract_tools_from_trace(agent_result.trace_path if agent_result else None),
            "error": error,
        }
        
        # Run checks
        check_details = {}
        checks_passed = 0
        
        for check in task_spec.checks:
            try:
                passed = check.check_fn(ctx)
            except Exception as e:
                self.log(f"  ⚠️  Check '{check.name}' raised: {e}")
                passed = False
            
            check_details[check.name] = passed
            if passed:
                checks_passed += 1
                self.log(f"  ✅ {check.name}: {check.description}")
            else:
                self.log(f"  ❌ {check.name}: {check.description}")
        
        # Cleanup if provided
        if task_spec.cleanup_fn:
            try:
                task_spec.cleanup_fn(workspace)
            except Exception:
                pass
        
        # Build result
        checks_total = len(task_spec.checks)
        score = checks_passed / checks_total if checks_total > 0 else 0.0
        
        result = EvalResult(
            name=task_spec.name,
            category=task_spec.category,
            task=task_spec.task,
            success=checks_passed == checks_total,
            checks_passed=checks_passed,
            checks_total=checks_total,
            score=score,
            stop_reason=ctx["stop_reason"],
            steps_executed=ctx["steps_executed"],
            duration_seconds=duration,
            error=error,
            check_details=check_details,
        )
        
        self.log(f"\n📊 Result: {checks_passed}/{checks_total} ({score:.0%}) in {duration:.1f}s")
        
        return result
    
    def run_all(
        self,
        tasks: Optional[List[EvalTask]] = None,
        categories: Optional[List[str]] = None,
    ) -> List[EvalResult]:
        """Run all eval tasks (or filtered subset)."""
        tasks = tasks or EVAL_TASKS
        
        if categories:
            tasks = [t for t in tasks if t.category in categories]
        
        self.log(f"\n🚀 Running {len(tasks)} evaluation tasks")
        self.log(f"📂 Results directory: {self.eval_dir}")
        
        self.results = []
        for task_spec in tasks:
            result = self.run_task(task_spec)
            self.results.append(result)
        
        return self.results
    
    def print_summary(self) -> None:
        """Print summary of all results."""
        if not self.results:
            print("No results to summarize.")
            return
        
        print(f"\n{'='*60}")
        print("📊 EVALUATION SUMMARY")
        print(f"{'='*60}")
        
        # Overall stats
        total_score = sum(r.score for r in self.results) / len(self.results)
        total_passed = sum(1 for r in self.results if r.success)
        total_tasks = len(self.results)
        
        print(f"\n🎯 Overall Score: {total_score:.1%}")
        print(f"✅ Tasks Passed: {total_passed}/{total_tasks}")
        
        # By category
        categories = sorted(set(r.category for r in self.results))
        print(f"\n📁 By Category:")
        for cat in categories:
            cat_results = [r for r in self.results if r.category == cat]
            cat_score = sum(r.score for r in cat_results) / len(cat_results)
            cat_passed = sum(1 for r in cat_results if r.success)
            print(f"   {cat}: {cat_score:.0%} ({cat_passed}/{len(cat_results)} passed)")
        
        # Individual results
        print(f"\n📋 Individual Tasks:")
        for r in self.results:
            status = "✅" if r.success else "❌"
            print(f"   {status} {r.name}: {r.checks_passed}/{r.checks_total} ({r.stop_reason}, {r.steps_executed} steps, {r.duration_seconds:.1f}s)")
        
        # Save results
        results_file = self.eval_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "overall_score": total_score,
                    "tasks_passed": total_passed,
                    "tasks_total": total_tasks,
                    "results": [
                        {
                            "name": r.name,
                            "category": r.category,
                            "success": r.success,
                            "score": r.score,
                            "checks_passed": r.checks_passed,
                            "checks_total": r.checks_total,
                            "stop_reason": r.stop_reason,
                            "steps_executed": r.steps_executed,
                            "duration_seconds": r.duration_seconds,
                            "check_details": r.check_details,
                            "error": r.error,
                        }
                        for r in self.results
                    ],
                },
                f,
                indent=2,
            )
        print(f"\n💾 Results saved to: {results_file}")

# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Main entry point for eval suite."""
    import argparse
    import sys
    
    # Fix Windows encoding for emoji support
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    parser = argparse.ArgumentParser(description="DrCodePT-Swarm Evaluation Suite")
    parser.add_argument(
        "--category", "-c",
        type=str,
        nargs="+",
        choices=["basic", "planning", "recovery", "boundaries", "memory", "complex"],
        help="Run only specific categories",
    )
    parser.add_argument(
        "--task", "-t",
        type=str,
        nargs="+",
        help="Run only specific tasks by name",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available tasks",
    )
    parser.add_argument(
        "--stub",
        action="store_true",
        help="Use stub LLM (for testing the eval framework itself)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (less output)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        help="Custom output directory for results",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick smoke test (basic category only, reduced timeout)",
    )
    
    args = parser.parse_args()

    # Auto-answer human_ask prompts during eval runs unless explicitly overridden.
    if os.getenv("AGENT_AUTO_ANSWER") is None and os.getenv("AGENT_AUTO_APPROVE") is None:
        os.environ["AGENT_AUTO_ANSWER"] = "yes"
    if os.getenv("AGENT_SKIP_PRECONDITIONS") is None:
        os.environ["AGENT_SKIP_PRECONDITIONS"] = "1"
    
    # List tasks
    if args.list:
        print("\n📋 Available Evaluation Tasks:\n")
        categories = sorted(set(t.category for t in EVAL_TASKS))
        for cat in categories:
            print(f"  [{cat}]")
            for task in EVAL_TASKS:
                if task.category == cat:
                    print(f"    • {task.name}: {task.task[:60]}...")
        print(f"\nTotal: {len(EVAL_TASKS)} tasks")
        return
    
    # Filter tasks
    tasks = EVAL_TASKS
    
    # Smoke test mode
    if args.smoke:
        tasks = [t for t in tasks if t.category == "basic"]
        print("🔥 Smoke test mode: running basic tasks only\n")
    
    if args.task:
        tasks = [t for t in tasks if t.name in args.task]
        if not tasks:
            print(f"❌ No tasks found matching: {args.task}")
            return
    
    # Setup runner
    eval_dir = Path(args.output_dir) if args.output_dir else None
    runner = EvalRunner(
        eval_dir=eval_dir,
        verbose=not args.quiet,
        use_stub_llm=args.stub,
    )
    
    # Run
    runner.run_all(tasks=tasks, categories=args.category)
    runner.print_summary()


if __name__ == "__main__":
    main()
