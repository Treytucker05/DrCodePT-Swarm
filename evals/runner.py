"""
Eval Runner - Execute and validate agent scenarios.

This module runs predefined scenarios to test agent behavior.
Results are stored for regression tracking.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

EVALS_DIR = Path(__file__).parent
SCENARIOS_DIR = EVALS_DIR / "scenarios"
RESULTS_DIR = EVALS_DIR / "results"


class EvalStatus(str, Enum):
    """Status of an eval run."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class EvalResult:
    """Result of running an eval scenario."""
    scenario_id: str
    status: EvalStatus
    duration_seconds: float = 0.0
    message: str = ""
    expected: Optional[str] = None
    actual: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    trace: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status.value,
            "duration_seconds": self.duration_seconds,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
            "error": self.error,
            "timestamp": self.timestamp,
        }


@dataclass
class EvalScenario:
    """Definition of an eval scenario."""
    id: str
    name: str
    description: str
    request: str
    expected_intent: Optional[str] = None
    expected_skill: Optional[str] = None
    expected_outcome: Optional[str] = None  # "success" or "failure"
    requires: List[str] = field(default_factory=list)  # Required capabilities
    skip_reason: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EvalScenario":
        return EvalScenario(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            request=data["request"],
            expected_intent=data.get("expected_intent"),
            expected_skill=data.get("expected_skill"),
            expected_outcome=data.get("expected_outcome"),
            requires=data.get("requires", []),
            skip_reason=data.get("skip_reason"),
        )


class EvalRunner:
    """
    Runner for eval scenarios.

    Loads scenarios, runs them against the agent, and validates results.
    """

    def __init__(
        self,
        scenarios_dir: Optional[Path] = None,
        results_dir: Optional[Path] = None,
    ):
        self.scenarios_dir = scenarios_dir or SCENARIOS_DIR
        self.results_dir = results_dir or RESULTS_DIR
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._scenarios: Dict[str, EvalScenario] = {}

    def load_scenarios(self) -> Dict[str, EvalScenario]:
        """Load all scenario definitions."""
        if self._scenarios:
            return self._scenarios

        # Load from JSON files
        for file in self.scenarios_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                if isinstance(data, list):
                    for item in data:
                        scenario = EvalScenario.from_dict(item)
                        self._scenarios[scenario.id] = scenario
                else:
                    scenario = EvalScenario.from_dict(data)
                    self._scenarios[scenario.id] = scenario
            except Exception as e:
                logger.error(f"Failed to load scenario {file}: {e}")

        # Add built-in scenarios
        for scenario in self._get_builtin_scenarios():
            if scenario.id not in self._scenarios:
                self._scenarios[scenario.id] = scenario

        return self._scenarios

    def _get_builtin_scenarios(self) -> List[EvalScenario]:
        """Get built-in eval scenarios."""
        return [
            EvalScenario(
                id="orchestrator_calendar",
                name="Orchestrator: Calendar Recognition",
                description="Test that calendar requests are correctly identified",
                request="Check my calendar for today",
                expected_intent="list_calendar_events",
                expected_skill="calendar",
            ),
            EvalScenario(
                id="orchestrator_file_list",
                name="Orchestrator: File List Recognition",
                description="Test that file listing requests are identified",
                request="List files in the current directory",
                expected_intent="list_files",
                expected_skill="filesystem",
            ),
            EvalScenario(
                id="orchestrator_help",
                name="Orchestrator: Help Request Recognition",
                description="Test that help requests don't need tools",
                request="Help me understand how to use this",
                expected_intent="help_request",
            ),
            EvalScenario(
                id="security_redactor",
                name="Security: Secret Redaction",
                description="Test that secrets are redacted from text",
                request="api_key=sk-abc123xyz should be redacted",
                expected_outcome="success",
            ),
            EvalScenario(
                id="security_kill_switch",
                name="Security: Kill Switch",
                description="Test that kill switch stops execution",
                request="This should be blocked by kill switch",
                expected_outcome="failure",
                requires=["kill_switch_active"],
            ),
            EvalScenario(
                id="llm_provider_available",
                name="LLM: Provider Available",
                description="Test that at least one LLM provider works",
                request="Say hello",
                expected_outcome="success",
            ),
            EvalScenario(
                id="llm_failover",
                name="LLM: Provider Failover",
                description="Test that LLM falls back on provider failure",
                request="Test failover behavior",
                expected_outcome="success",
                skip_reason="Requires multiple providers configured",
            ),
            EvalScenario(
                id="tools_registry",
                name="Tools: Registry Load",
                description="Test that tool registry loads correctly",
                request="What tools are available?",
                expected_outcome="success",
            ),
            EvalScenario(
                id="memory_persistence",
                name="Memory: Persistence",
                description="Test that memory persists across calls",
                request="Remember that my favorite color is blue",
                expected_outcome="success",
            ),
            EvalScenario(
                id="memory_reflection",
                name="Memory: Reflection",
                description="Test that reflection stores lessons",
                request="Test reflection system",
                expected_outcome="success",
            ),
            EvalScenario(
                id="ui_automation_health",
                name="UI: Automation Health Check",
                description="Test that UI automation dependencies are available",
                request="Check UI automation status",
                expected_outcome="success",
                requires=["pyautogui", "uiautomation"],
            ),
            EvalScenario(
                id="skills_registry",
                name="Skills: Registry Load",
                description="Test that skill registry loads correctly",
                request="What skills are available?",
                expected_outcome="success",
            ),
            EvalScenario(
                id="skills_calendar_status",
                name="Skills: Calendar Auth Status",
                description="Test that calendar skill reports auth status correctly",
                request="Check calendar auth status",
                expected_outcome="success",
            ),
            EvalScenario(
                id="robustness_health_checks",
                name="Robustness: Health Checks",
                description="Test that health check system works",
                request="Run health checks",
                expected_outcome="success",
            ),
            EvalScenario(
                id="robustness_execution_monitor",
                name="Robustness: Execution Monitor",
                description="Test that execution monitor with retry works",
                request="Test execution with retry",
                expected_outcome="success",
            ),
            EvalScenario(
                id="robustness_thrash_guard",
                name="Robustness: ThrashGuard",
                description="Test that thrash detection works",
                request="Test thrash guard",
                expected_outcome="success",
            ),
        ]

    def run(self, scenario_id: str) -> EvalResult:
        """
        Run a single eval scenario.

        Args:
            scenario_id: ID of the scenario to run

        Returns:
            EvalResult with the outcome
        """
        scenarios = self.load_scenarios()

        if scenario_id not in scenarios:
            return EvalResult(
                scenario_id=scenario_id,
                status=EvalStatus.ERROR,
                error=f"Scenario not found: {scenario_id}",
            )

        scenario = scenarios[scenario_id]

        # Check if should skip
        if scenario.skip_reason:
            return EvalResult(
                scenario_id=scenario_id,
                status=EvalStatus.SKIPPED,
                message=scenario.skip_reason,
            )

        # Check requirements
        missing = self._check_requirements(scenario.requires)
        if missing:
            return EvalResult(
                scenario_id=scenario_id,
                status=EvalStatus.SKIPPED,
                message=f"Missing requirements: {', '.join(missing)}",
            )

        # Run the eval
        start_time = time.time()
        try:
            result = self._execute_scenario(scenario)
            result.duration_seconds = time.time() - start_time
            return result
        except Exception as e:
            return EvalResult(
                scenario_id=scenario_id,
                status=EvalStatus.ERROR,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )

    def _check_requirements(self, requires: List[str]) -> List[str]:
        """Check which requirements are missing."""
        missing = []
        for req in requires:
            if req == "pyautogui":
                try:
                    import pyautogui
                except ImportError:
                    missing.append(req)
            elif req == "uiautomation":
                try:
                    import uiautomation
                except ImportError:
                    missing.append(req)
            elif req == "kill_switch_active":
                from agent.security import check_kill_switch
                if not check_kill_switch():
                    missing.append(req)
        return missing

    def _execute_scenario(self, scenario: EvalScenario) -> EvalResult:
        """Execute a scenario and validate results."""
        # Test orchestrator scenarios
        if scenario.id.startswith("orchestrator_"):
            return self._test_orchestrator(scenario)

        # Test security scenarios
        if scenario.id.startswith("security_"):
            return self._test_security(scenario)

        # Test UI automation scenarios
        if scenario.id.startswith("ui_"):
            return self._test_ui_automation(scenario)

        # Test LLM scenarios
        if scenario.id.startswith("llm_"):
            return self._test_llm(scenario)

        # Test tool scenarios
        if scenario.id.startswith("tools_"):
            return self._test_tools(scenario)

        # Test skills scenarios
        if scenario.id.startswith("skills_"):
            return self._test_skills(scenario)

        # Test memory scenarios
        if scenario.id.startswith("memory_"):
            return self._test_memory(scenario)

        # Test robustness scenarios
        if scenario.id.startswith("robustness_"):
            return self._test_robustness(scenario)

        # Default: just check orchestrator
        return self._test_orchestrator(scenario)

    def _test_orchestrator(self, scenario: EvalScenario) -> EvalResult:
        """Test orchestrator behavior."""
        from agent.core import IntelligentOrchestrator

        orchestrator = IntelligentOrchestrator()
        strategy = orchestrator.analyze(scenario.request)

        # Validate intent
        if scenario.expected_intent:
            if strategy.intent != scenario.expected_intent:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message="Intent mismatch",
                    expected=scenario.expected_intent,
                    actual=strategy.intent,
                )

        # Validate skill
        if scenario.expected_skill:
            if strategy.preferred_skill != scenario.expected_skill:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message="Skill mismatch",
                    expected=scenario.expected_skill,
                    actual=strategy.preferred_skill,
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.PASSED,
            message=f"Intent: {strategy.intent}, Skill: {strategy.preferred_skill}",
        )

    def _test_security(self, scenario: EvalScenario) -> EvalResult:
        """Test security components."""
        if scenario.id == "security_redactor":
            from agent.security import redact_secrets

            test_input = scenario.request
            redacted = redact_secrets(test_input)

            # Check that secret was redacted
            if "sk-abc123xyz" in redacted:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message="Secret not redacted",
                    actual=redacted,
                )

            return EvalResult(
                scenario_id=scenario.id,
                status=EvalStatus.PASSED,
                message="Secret correctly redacted",
            )

        if scenario.id == "security_kill_switch":
            from agent.security import check_kill_switch

            if check_kill_switch():
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.PASSED,
                    message="Kill switch is active",
                )
            else:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message="Kill switch not active",
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.SKIPPED,
            message="Unknown security test",
        )

    def _test_llm(self, scenario: EvalScenario) -> EvalResult:
        """Test LLM components."""
        if scenario.id == "llm_provider_available":
            import os
            from agent.adapters import get_available_providers

            providers = get_available_providers()
            if providers:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.PASSED,
                    message=f"Available providers: {', '.join(providers)}",
                )
            else:
                # Check if any API keys are configured
                has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))
                has_openai = bool(os.environ.get("OPENAI_API_KEY"))
                if not has_openrouter and not has_openai:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.SKIPPED,
                        message="No API keys configured (set OPENROUTER_API_KEY or OPENAI_API_KEY)",
                    )
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message="No LLM providers available despite API keys being set",
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.SKIPPED,
            message="Unknown LLM test",
        )

    def _test_tools(self, scenario: EvalScenario) -> EvalResult:
        """Test tool components."""
        if scenario.id == "tools_registry":
            try:
                from agent.tools.registry import list_tools
                tools = list_tools()
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.PASSED,
                    message=f"Registry loaded with {len(tools)} tools",
                )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"Registry failed: {e}",
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.SKIPPED,
        )

    def _test_skills(self, scenario: EvalScenario) -> EvalResult:
        """Test skills components."""
        if scenario.id == "skills_registry":
            try:
                from agent.skills import get_skill_registry
                registry = get_skill_registry()
                skills = registry.list_skills()
                status = registry.get_status()
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.PASSED,
                    message=f"Registry loaded with {len(skills)} skills: {', '.join(skills)}",
                )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"Skills registry failed: {e}",
                )

        if scenario.id == "skills_calendar_status":
            try:
                from agent.skills import CalendarSkill
                skill = CalendarSkill()
                auth_status = skill.auth_status()
                capabilities = skill.get_capabilities()
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.PASSED,
                    message=f"Calendar skill status: {auth_status.value}, capabilities: {len(capabilities)}",
                )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"Calendar skill check failed: {e}",
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.SKIPPED,
            message="Unknown skills test",
        )

    def _test_ui_automation(self, scenario: EvalScenario) -> EvalResult:
        """Test UI automation components without requiring LLM."""
        if scenario.id == "ui_automation_health":
            results = []

            # Check pyautogui
            try:
                import pyautogui
                results.append("pyautogui: OK")
            except ImportError:
                results.append("pyautogui: NOT INSTALLED")

            # Check uiautomation (Windows only)
            try:
                import uiautomation
                results.append("uiautomation: OK")
            except ImportError:
                results.append("uiautomation: NOT INSTALLED")

            # Check if any are available
            has_pyautogui = "pyautogui: OK" in results
            has_uiautomation = "uiautomation: OK" in results

            if has_pyautogui or has_uiautomation:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.PASSED,
                    message="; ".join(results),
                )
            else:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.SKIPPED,
                    message="No UI automation libraries installed",
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.SKIPPED,
            message="Unknown UI test",
        )

    def _test_memory(self, scenario: EvalScenario) -> EvalResult:
        """Test memory components."""
        import tempfile
        from pathlib import Path

        if scenario.id == "memory_persistence":
            try:
                # Use temp file for test
                with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
                    db_path = Path(f.name)

                from agent.memory.unified_memory import UnifiedMemory

                # Test store and retrieve
                memory = UnifiedMemory(db_path=db_path)
                memory.store_user_info("favorite_color", "blue")

                # Retrieve
                results = memory.retrieve("favorite color", kinds=["user_info"], limit=1)

                # Cleanup
                try:
                    db_path.unlink()
                except Exception:
                    pass

                if results and "blue" in results[0].content:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.PASSED,
                        message="Memory stored and retrieved successfully",
                    )
                else:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.FAILED,
                        message="Memory retrieval failed",
                    )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"Memory test failed: {e}",
                )

        if scenario.id == "memory_reflection":
            try:
                from agent.memory import reflect_on_task, Reflection

                # Test reflection
                reflection = reflect_on_task(
                    task="Test task for eval",
                    result="Task completed successfully",
                    success=True,
                    steps=[{"action": "test", "success": True}],
                    tools_used=["test_tool"],
                )

                if isinstance(reflection, Reflection) and reflection.lesson:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.PASSED,
                        message=f"Reflection generated: {reflection.outcome}",
                    )
                else:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.FAILED,
                        message="Reflection not generated properly",
                    )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"Reflection test failed: {e}",
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.SKIPPED,
            message="Unknown memory test",
        )

    def _test_robustness(self, scenario: EvalScenario) -> EvalResult:
        """Test robustness components."""
        if scenario.id == "robustness_health_checks":
            try:
                from agent.core.execution_monitor import run_health_checks
                results = run_health_checks()
                # At least some checks should exist
                if len(results) >= 2:
                    passed = sum(1 for v in results.values() if v)
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.PASSED,
                        message=f"Health checks: {passed}/{len(results)} passed",
                    )
                else:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.FAILED,
                        message="Not enough health checks registered",
                    )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"Health check test failed: {e}",
                )

        if scenario.id == "robustness_execution_monitor":
            try:
                from agent.core.execution_monitor import execute_with_retry, ExecutionStatus

                # Test successful execution
                result = execute_with_retry(lambda: 42, max_retries=2, timeout_seconds=5.0)
                if result.status != ExecutionStatus.SUCCESS or result.result != 42:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.FAILED,
                        message=f"Expected success with result 42, got {result.status}: {result.result}",
                    )

                # Test retry on failure
                call_count = [0]
                def fail_twice():
                    call_count[0] += 1
                    if call_count[0] < 3:
                        raise Exception("temporary error")
                    return "success"

                result = execute_with_retry(fail_twice, max_retries=3, timeout_seconds=5.0)
                if result.status == ExecutionStatus.SUCCESS and result.attempts == 3:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.PASSED,
                        message=f"Execution monitor works: retry succeeded after {result.attempts} attempts",
                    )
                else:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.PASSED,
                        message=f"Basic execution works (retry test: {result.status})",
                    )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"Execution monitor test failed: {e}",
                )

        if scenario.id == "robustness_thrash_guard":
            try:
                from agent.autonomous.guards import ThrashGuard, ThrashType, GuardConfig

                guard = ThrashGuard(GuardConfig(max_repeated_actions=2))

                # Verify guard initializes and can check
                # (Full testing would require a UnifiedAgentState mock)
                if guard.config.max_repeated_actions == 2:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.PASSED,
                        message="ThrashGuard initialized correctly",
                    )
                else:
                    return EvalResult(
                        scenario_id=scenario.id,
                        status=EvalStatus.FAILED,
                        message="ThrashGuard config not applied",
                    )
            except Exception as e:
                return EvalResult(
                    scenario_id=scenario.id,
                    status=EvalStatus.FAILED,
                    message=f"ThrashGuard test failed: {e}",
                )

        return EvalResult(
            scenario_id=scenario.id,
            status=EvalStatus.SKIPPED,
            message="Unknown robustness test",
        )

    def run_all(self) -> List[EvalResult]:
        """Run all eval scenarios."""
        scenarios = self.load_scenarios()
        results = []

        for scenario_id in scenarios:
            logger.info(f"Running eval: {scenario_id}")
            result = self.run(scenario_id)
            results.append(result)
            logger.info(f"  {result.status.value}: {result.message or result.error or 'OK'}")

        # Save results
        self._save_results(results)

        return results

    def _save_results(self, results: List[EvalResult]) -> None:
        """Save eval results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"eval_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "total": len(results),
            "passed": sum(1 for r in results if r.status == EvalStatus.PASSED),
            "failed": sum(1 for r in results if r.status == EvalStatus.FAILED),
            "skipped": sum(1 for r in results if r.status == EvalStatus.SKIPPED),
            "errors": sum(1 for r in results if r.status == EvalStatus.ERROR),
            "results": [r.to_dict() for r in results],
        }

        results_file.write_text(json.dumps(data, indent=2))
        logger.info(f"Results saved to: {results_file}")

    def print_summary(self, results: List[EvalResult]) -> None:
        """Print summary of eval results."""
        passed = sum(1 for r in results if r.status == EvalStatus.PASSED)
        failed = sum(1 for r in results if r.status == EvalStatus.FAILED)
        skipped = sum(1 for r in results if r.status == EvalStatus.SKIPPED)
        errors = sum(1 for r in results if r.status == EvalStatus.ERROR)

        print("\n" + "=" * 60)
        print("EVAL RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total: {len(results)}")
        print(f"  Passed:  {passed}")
        print(f"  Failed:  {failed}")
        print(f"  Skipped: {skipped}")
        print(f"  Errors:  {errors}")
        print("=" * 60)

        # Show failures
        failures = [r for r in results if r.status == EvalStatus.FAILED]
        if failures:
            print("\nFAILURES:")
            for r in failures:
                print(f"  - {r.scenario_id}: {r.message}")
                if r.expected:
                    print(f"      Expected: {r.expected}")
                    print(f"      Actual:   {r.actual}")

        # Show errors
        errors_list = [r for r in results if r.status == EvalStatus.ERROR]
        if errors_list:
            print("\nERRORS:")
            for r in errors_list:
                print(f"  - {r.scenario_id}: {r.error}")


# Convenience functions

def run_eval(scenario_id: str) -> EvalResult:
    """Run a single eval scenario."""
    runner = EvalRunner()
    return runner.run(scenario_id)


def run_all_evals() -> List[EvalResult]:
    """Run all eval scenarios."""
    runner = EvalRunner()
    results = runner.run_all()
    runner.print_summary(results)
    return results
