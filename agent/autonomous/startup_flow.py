"""Intelligent startup flow for agent initialization."""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ExecutionMode(Enum):
    """Execution modes for the agent."""
    SOLO = "solo"
    TEAM = "team"
    SWARM = "swarm"
    AUTO = "auto"

class AnalysisDepth(Enum):
    """Analysis depth profiles."""
    FAST = "fast"
    DEEP = "deep"
    AUDIT = "audit"

class StartupFlow:
    """Intelligent startup flow for agent initialization."""
    
    def __init__(self):
        self.task: Optional[str] = None
        self.mode: Optional[ExecutionMode] = None
        self.depth: Optional[AnalysisDepth] = None
        self.specialists: list = []
        self.plan: Dict[str, Any] = {}
    
    def ask_clarifying_questions(self) -> Dict[str, Any]:
        """Ask user clarifying questions about their goal."""
        logger.info("Starting intelligent startup flow...")
        
        responses = {
            "scope": self._ask_scope(),
            "execution_mode": self._ask_execution_mode(),
            "depth": self._ask_depth(),
            "focus_areas": self._ask_focus_areas(),
        }
        
        return responses
    
    def _ask_scope(self) -> str:
        """Ask about analysis scope."""
        print("\n What's the scope of your task?")
        print("  a) Single file/repo analysis")
        print("  b) Compare multiple files")
        print("  c) Deep dive into architecture")
        print("  d) Performance optimization")
        print("  e) Security audit")
        
        choice = input("\nYour choice (a-e): ").strip().lower()
        scope_map = {
            "a": "single_analysis",
            "b": "comparison",
            "c": "architecture",
            "d": "performance",
            "e": "security",
        }
        return scope_map.get(choice, "single_analysis")
    
    def _ask_execution_mode(self) -> ExecutionMode:
        """Ask about execution mode."""
        print("\n⚙️ How should I work?")
        print("  a) Solo - Fast, single agent (5-10 min)")
        print("  b) Team - Multiple specialists (10-20 min)")
        print("  c) Swarm - Parallel workers (15-30 min)")
        print("  d) Auto - Let me decide")
        
        choice = input("\nYour choice (a-d): ").strip().lower()
        mode_map = {
            "a": ExecutionMode.SOLO,
            "b": ExecutionMode.TEAM,
            "c": ExecutionMode.SWARM,
            "d": ExecutionMode.AUTO,
        }
        return mode_map.get(choice, ExecutionMode.AUTO)
    
    def _ask_depth(self) -> AnalysisDepth:
        """Ask about analysis depth."""
        print("\n Analysis depth?")
        print("  a) Fast - Quick overview (5 min)")
        print("  b) Deep - Thorough analysis (15 min)")
        print("  c) Audit - Comprehensive review (30 min)")
        
        choice = input("\nYour choice (a-c): ").strip().lower()
        depth_map = {
            "a": AnalysisDepth.FAST,
            "b": AnalysisDepth.DEEP,
            "c": AnalysisDepth.AUDIT,
        }
        return depth_map.get(choice, AnalysisDepth.DEEP)
    
    def _ask_focus_areas(self) -> list:
        """Ask about focus areas."""
        print("\n Focus areas?")
        print("  a) Performance")
        print("  b) Security")
        print("  c) Code quality")
        print("  d) All of the above")
        
        choice = input("\nYour choice (a-d): ").strip().lower()
        focus_map = {
            "a": ["performance"],
            "b": ["security"],
            "c": ["quality"],
            "d": ["performance", "security", "quality"],
        }
        return focus_map.get(choice, ["quality"])
    
    def generate_plan(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution plan based on responses."""
        mode = responses["execution_mode"]
        depth = responses["depth"]
        focus_areas = responses["focus_areas"]
        
        plan = {
            "mode": mode.value,
            "depth": depth.value,
            "focus_areas": focus_areas,
            "specialists": self._select_specialists(focus_areas, mode),
            "estimated_time": self._estimate_time(mode, depth),
            "estimated_cost": self._estimate_cost(mode, depth),
        }
        
        return plan
    
    def _select_specialists(self, focus_areas: list, mode: ExecutionMode) -> list:
        """Select specialists based on focus areas."""
        if mode == ExecutionMode.SOLO:
            return ["general_analyst"]
        
        specialists = []
        if "performance" in focus_areas:
            specialists.append("performance_specialist")
        if "security" in focus_areas:
            specialists.append("security_specialist")
        if "quality" in focus_areas:
            specialists.append("quality_specialist")
        
        return specialists if specialists else ["general_analyst"]
    
    def _estimate_time(self, mode: ExecutionMode, depth: AnalysisDepth) -> str:
        """Estimate execution time."""
        time_map = {
            (ExecutionMode.SOLO, AnalysisDepth.FAST): "5-10 min",
            (ExecutionMode.SOLO, AnalysisDepth.DEEP): "10-15 min",
            (ExecutionMode.SOLO, AnalysisDepth.AUDIT): "20-30 min",
            (ExecutionMode.TEAM, AnalysisDepth.FAST): "10-15 min",
            (ExecutionMode.TEAM, AnalysisDepth.DEEP): "15-25 min",
            (ExecutionMode.TEAM, AnalysisDepth.AUDIT): "25-40 min",
            (ExecutionMode.SWARM, AnalysisDepth.FAST): "8-12 min",
            (ExecutionMode.SWARM, AnalysisDepth.DEEP): "12-20 min",
            (ExecutionMode.SWARM, AnalysisDepth.AUDIT): "20-35 min",
        }
        return time_map.get((mode, depth), "15-20 min")
    
    def _estimate_cost(self, mode: ExecutionMode, depth: AnalysisDepth) -> str:
        """Estimate execution cost."""
        cost_map = {
            (ExecutionMode.SOLO, AnalysisDepth.FAST): "$0.10-0.20",
            (ExecutionMode.SOLO, AnalysisDepth.DEEP): "$0.20-0.40",
            (ExecutionMode.SOLO, AnalysisDepth.AUDIT): "$0.40-0.80",
            (ExecutionMode.TEAM, AnalysisDepth.FAST): "$0.30-0.50",
            (ExecutionMode.TEAM, AnalysisDepth.DEEP): "$0.50-1.00",
            (ExecutionMode.TEAM, AnalysisDepth.AUDIT): "$1.00-2.00",
            (ExecutionMode.SWARM, AnalysisDepth.FAST): "$0.25-0.40",
            (ExecutionMode.SWARM, AnalysisDepth.DEEP): "$0.40-0.80",
            (ExecutionMode.SWARM, AnalysisDepth.AUDIT): "$0.80-1.50",
        }
        return cost_map.get((mode, depth), "$0.50-1.00")
    
    def display_plan(self, plan: Dict[str, Any]) -> None:
        """Display the execution plan to the user."""
        print("\n" + "="*50)
        print(" EXECUTION PLAN")
        print("="*50)
        print(f"Mode: {plan['mode'].upper()}")
        print(f"Depth: {plan['depth'].upper()}")
        print(f"Focus: {', '.join(plan['focus_areas'])}")
        print(f"Specialists: {', '.join(plan['specialists'])}")
        print(f"Estimated time: {plan['estimated_time']}")
        print(f"Estimated cost: {plan['estimated_cost']}")
        print("="*50)
    
    def get_confirmation(self) -> bool:
        """Get user confirmation to proceed."""
        response = input("\n✅ Ready to proceed? (yes/no): ").strip().lower()
        return response in ["yes", "y"]
    
    def run(self, task: str) -> Dict[str, Any]:
        """Run the complete startup flow."""
        self.task = task
        
        responses = self.ask_clarifying_questions()
        plan = self.generate_plan(responses)
        self.plan = plan
        self.display_plan(plan)
        
        if not self.get_confirmation():
            logger.info("User cancelled execution")
            return {"status": "cancelled"}
        
        return {
            "status": "confirmed",
            "task": self.task,
            "plan": plan,
        }
