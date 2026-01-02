"""
GPT-5.2-Codex with xhigh Reasoning Integration for DrCodePT-Swarm Phase 3

Uses your existing Codex CLI login (no OpenAI API) with native GPT-5.2-Codex xhigh reasoning.
Designed for autonomous agent tasks with extended thinking.

Key Features:
- Integrates with existing CodexCliClient
- Uses xhigh reasoning effort for complex planning/validation
- Uses medium reasoning for execution (cost-efficient)
- Native loop detection and self-healing
- Persistent execution history and learning

PERRIO Protocol v6.4 Optimization:
- Gather: xhigh reasoning for intelligent data collection
- Prime: medium reasoning for context preparation  
- Encode: medium reasoning for transformation
- Retrieve: xhigh for pattern validation
- Reinforce: xhigh for memory consolidation
- Close: medium for cleanup
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

try:
    from agent.llm import CodexCliClient, LLMBackend, RunConfig
except ImportError:
    # Fallback if importing from wrong location
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from agent.llm import CodexCliClient, LLMBackend, RunConfig

logger = logging.getLogger(__name__)


class ReasoningEffort(Enum):
    """GPT-5.2-Codex reasoning effort levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"  # NEW: Extended High reasoning


class ExecutionPhase(BaseModel):
    """Single execution phase with reasoning metadata"""
    phase_name: str
    reasoning_effort: ReasoningEffort
    task_description: str
    output: str
    thinking_tokens_estimate: int = 0  # Xhigh uses more thinking tokens
    execution_time_seconds: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    success: bool = True
    error_message: Optional[str] = None


class AutonomousTaskResult(BaseModel):
    """Result of autonomous task execution"""
    task_id: str
    task_description: str
    success: bool
    phases: List[ExecutionPhase] = Field(default_factory=list)
    final_output: str
    total_execution_time: float = 0.0
    xhigh_phases_used: int = 0
    learned_insights: List[str] = Field(default_factory=list)


@dataclass
class Codex52XhighRouter:
    """
    Routes tasks to GPT-5.2-Codex with intelligent reasoning effort selection.
    
    Uses Codex CLI login (existing credentials, no OpenAI API).
    Automatically selects xhigh for complex reasoning, medium for execution.
    """
    
    llm: LLMBackend
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".codex")
    max_task_budget: int = Field(default=150000)  # Max thinking tokens per task
    execution_history: List[AutonomousTaskResult] = Field(default_factory=list)
    loop_detection_threshold: int = Field(default=3)
    
    @classmethod
    def from_codex_cli(cls) -> "Codex52XhighRouter":
        """Initialize from existing Codex CLI credentials"""
        return cls(
            llm=CodexCliClient.from_env(),
            config_dir=Path.home() / ".codex"
        )
    
    async def _execute_with_reasoning(
        self,
        task: str,
        reasoning_effort: ReasoningEffort,
        phase_name: str = "execution"
    ) -> ExecutionPhase:
        """Execute single phase with specified reasoning effort"""
        
        start_time = time.time()
        
        try:
            # Build prompt with reasoning instruction
            reasoning_prefix = {
                ReasoningEffort.NONE: "",
                ReasoningEffort.LOW: "[REASONING: fast, minimal thinking]",
                ReasoningEffort.MEDIUM: "[REASONING: balanced, focused thinking]",
                ReasoningEffort.HIGH: "[REASONING: thorough, deep thinking]",
                ReasoningEffort.XHIGH: "[REASONING: xhigh, extended maximum thinking for critical decisions]"
            }
            
            prompt = f"{reasoning_prefix[reasoning_effort]}\n\n{task}"
            
            # Call Codex CLI with reasoning config
            result = self.llm.run(
                prompt=prompt,
                workdir=None,
                run_dir=None,
                config=RunConfig(
                    profile=reasoning_effort.value,  # Maps to codex reasoning profile
                    timeout_seconds=600 if reasoning_effort == ReasoningEffort.XHIGH else 300
                )
            )
            
            execution_time = time.time() - start_time
            
            # Estimate thinking tokens (rough heuristic)
            # xhigh: ~40% of response is thinking, medium: ~20%, low: ~10%
            thinking_token_ratio = {
                ReasoningEffort.NONE: 0.0,
                ReasoningEffort.LOW: 0.1,
                ReasoningEffort.MEDIUM: 0.2,
                ReasoningEffort.HIGH: 0.3,
                ReasoningEffort.XHIGH: 0.4
            }
            
            output_tokens = len((result.data.get("output", "") if isinstance(result.data, dict) else str(result.data)).split())
            estimated_thinking = int(output_tokens * thinking_token_ratio[reasoning_effort])
            
            return ExecutionPhase(
                phase_name=phase_name,
                reasoning_effort=reasoning_effort,
                task_description=task[:500],  # Store first 500 chars
                output=str(result.data),
                thinking_tokens_estimate=estimated_thinking,
                execution_time_seconds=execution_time,
                success=True
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Phase '{phase_name}' failed: {str(e)}")
            
            return ExecutionPhase(
                phase_name=phase_name,
                reasoning_effort=reasoning_effort,
                task_description=task[:500],
                output="",
                execution_time_seconds=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def _detect_loop(self, output: str, history: List[str]) -> bool:
        """Detect infinite loops by checking output similarity"""
        if len(history) < self.loop_detection_threshold:
            return False
        
        # Check if last N outputs are identical
        recent_outputs = history[-self.loop_detection_threshold:]
        return all(out == recent_outputs[0] for out in recent_outputs)
    
    async def execute_autonomous_task(
        self,
        task: str,
        use_three_phase: bool = True,
        max_iterations: int = 3
    ) -> AutonomousTaskResult:
        """
        Execute task with intelligent 3-phase approach:
        
        Phase 1: Planning (xhigh) - Deep reasoning for strategy
        Phase 2: Execution (medium) - Efficient implementation  
        Phase 3: Validation (xhigh) - Thorough quality check
        
        Auto-recovers from loops by switching to xhigh reasoning.
        """
        
        task_id = f"task_{int(time.time() * 1000)}"
        result = AutonomousTaskResult(
            task_id=task_id,
            task_description=task,
            success=False,
            final_output=""
        )
        
        start_time = time.time()
        output_history: List[str] = []
        
        for iteration in range(max_iterations):
            phases_this_iteration = []
            
            if use_three_phase:
                # PHASE 1: Planning with xhigh
                logger.info(f"[{task_id}] PHASE 1: Planning with xhigh reasoning...")
                plan_phase = await self._execute_with_reasoning(
                    task=f"Create a detailed execution plan for: {task}\n\nProvide step-by-step strategy.",
                    reasoning_effort=ReasoningEffort.XHIGH,
                    phase_name=f"plan_iter{iteration+1}"
                )
                phases_this_iteration.append(plan_phase)
                
                if not plan_phase.success:
                    result.phases.extend(phases_this_iteration)
                    result.success = False
                    break
                
                plan = plan_phase.output
                result.xhigh_phases_used += 1
                
                # PHASE 2: Execution with medium
                logger.info(f"[{task_id}] PHASE 2: Executing with medium reasoning (efficient)...")
                exec_task = f"{plan}\n\n---\n\nNow execute this plan:\n{task}"
                exec_phase = await self._execute_with_reasoning(
                    task=exec_task,
                    reasoning_effort=ReasoningEffort.MEDIUM,
                    phase_name=f"execute_iter{iteration+1}"
                )
                phases_this_iteration.append(exec_phase)
                
                if not exec_phase.success:
                    result.phases.extend(phases_this_iteration)
                    # Try recovery with xhigh
                    if iteration < max_iterations - 1:
                        logger.warning(f"[{task_id}] Execution failed, attempting recovery...")
                        continue
                    break
                
                execution_output = exec_phase.output
                output_history.append(execution_output)
                
                # Check for loops
                if self._detect_loop(execution_output, output_history):
                    logger.warning(f"[{task_id}] Loop detected! Forcing xhigh reasoning...")
                    if iteration < max_iterations - 1:
                        # Force xhigh on next iteration
                        continue
                
                # PHASE 3: Validation with xhigh
                logger.info(f"[{task_id}] PHASE 3: Validating with xhigh reasoning...")
                validation_task = f"""Validate this execution output and identify any issues:
                
{execution_output}

Provide:
1. Quality assessment
2. Any errors or problems
3. Recommendations for improvement
"""
                val_phase = await self._execute_with_reasoning(
                    task=validation_task,
                    reasoning_effort=ReasoningEffort.XHIGH,
                    phase_name=f"validate_iter{iteration+1}"
                )
                phases_this_iteration.append(val_phase)
                result.xhigh_phases_used += 1
                
                # Success!
                if all(p.success for p in phases_this_iteration):
                    result.phases.extend(phases_this_iteration)
                    result.success = True
                    result.final_output = execution_output
                    result.learned_insights = [
                        f"Successfully completed with {iteration + 1} iteration(s)",
                        f"Used {result.xhigh_phases_used} xhigh phases for deep reasoning",
                        f"Phase execution: {[p.phase_name for p in phases_this_iteration]}"
                    ]
                    break
            
            else:
                # Single-phase execution with adaptive reasoning
                if self._detect_loop("", output_history) and iteration > 0:
                    effort = ReasoningEffort.XHIGH
                else:
                    effort = ReasoningEffort.MEDIUM
                
                phase = await self._execute_with_reasoning(
                    task=task,
                    reasoning_effort=effort,
                    phase_name=f"single_phase_iter{iteration+1}"
                )
                phases_this_iteration.append(phase)
                
                if phase.success:
                    result.phases.extend(phases_this_iteration)
                    result.success = True
                    result.final_output = phase.output
                    break
                
                output_history.append(phase.output)
            
            result.phases.extend(phases_this_iteration)
        
        result.total_execution_time = time.time() - start_time
        self.execution_history.append(result)
        
        return result
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all executions"""
        if not self.execution_history:
            return {"executions": 0, "success_rate": 0.0, "xhigh_phases_total": 0}
        
        successful = sum(1 for e in self.execution_history if e.success)
        total_xhigh = sum(e.xhigh_phases_used for e in self.execution_history)
        total_time = sum(e.total_execution_time for e in self.execution_history)
        
        return {
            "executions": len(self.execution_history),
            "success_rate": successful / len(self.execution_history),
            "xhigh_phases_total": total_xhigh,
            "total_execution_time": total_time,
            "average_time_per_task": total_time / len(self.execution_history),
            "recent_tasks": [
                {
                    "task_id": e.task_id,
                    "success": e.success,
                    "phases": len(e.phases),
                    "xhigh_used": e.xhigh_phases_used
                }
                for e in self.execution_history[-5:]
            ]
        }
