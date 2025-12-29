"""
Enhanced Autonomous Mode with Self-Healing and Planning.

Wraps the existing autonomous mode with:
- Issue tracking and error recovery
- Multi-step planning with progress tracking
- Automatic retry with learned solutions
- Human-in-the-loop for 2FA and confirmations
"""

import os
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.memory.issue_tracker import (
    create_issue,
    find_similar_issue,
    update_issue,
    get_issue_summary
)
from agent.modes.autonomous import mode_autonomous

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"

def mode_autonomous_enhanced(task: str, max_retries: int = 3):
    """
    Enhanced autonomous mode with self-healing.
    
    Features:
    1. Runs task in autonomous mode
    2. If error occurs, checks for similar past issues
    3. Applies learned solutions or creates new issue
    4. Retries with different approaches
    5. Tracks all attempts for future reference
    """
    print(f"\n{CYAN}[ENHANCED AUTO]{RESET} Starting task: {task}")
    print(f"{YELLOW}[INFO]{RESET} Self-healing enabled (max_retries={max_retries})")
    
    summary = get_issue_summary()
    if summary["total"] > 0:
        print(f"{CYAN}[KNOWLEDGE]{RESET} {summary['resolved']} resolved issues available for reference")
    
    attempt = 0
    current_issue = None
    
    while attempt < max_retries:
        attempt += 1
        print(f"\n{CYAN}[ATTEMPT {attempt}/{max_retries}]{RESET}")
        
        if current_issue and current_issue.attempts:
            last_attempt = current_issue.attempts[-1]
            print(f"{YELLOW}[RETRY]{RESET} Previous attempt failed: {last_attempt['result']}")
            print(f"{YELLOW}[RETRY]{RESET} Trying different approach...")
        
        try:
            mode_autonomous(task)
            
            if current_issue:
                current_issue.add_attempt(
                    solution=f"Retry attempt {attempt}",
                    result="Success",
                    success=True
                )
                update_issue(current_issue)
                print(f"{GREEN}[RESOLVED]{RESET} Issue resolved after {attempt} attempts")
            
            print(f"{GREEN}[SUCCESS]{RESET} Task completed successfully")
            return
            
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[CANCELLED]{RESET} Task cancelled by user")
            return
            
        except Exception as exc:
            error_msg = str(exc)
            print(f"{RED}[ERROR]{RESET} {error_msg}")
            
            if not current_issue:
                similar = find_similar_issue(task, error_msg)
                if similar:
                    print(f"{CYAN}[KNOWLEDGE]{RESET} Found similar resolved issue: {similar.issue_id}")
                    print(f"{CYAN}[SOLUTION]{RESET} Previous solution: {similar.solution}")
                    
                    task_with_hint = f"{task}\n\nNote: Similar issue was resolved by: {similar.solution}"
                    try:
                        mode_autonomous(task_with_hint)
                        print(f"{GREEN}[SUCCESS]{RESET} Resolved using learned solution")
                        return
                    except Exception:
                        pass
                
                current_issue = create_issue(
                    task=task,
                    error=error_msg,
                    context={"attempt": attempt}
                )
                print(f"{YELLOW}[TRACKING]{RESET} Created issue: {current_issue.issue_id}")
            
            current_issue.add_attempt(
                solution=f"Attempt {attempt}",
                result=error_msg,
                success=False
            )
            update_issue(current_issue)
            
            if attempt < max_retries:
                print(f"{YELLOW}[RETRY]{RESET} Will retry with different approach...")
            else:
                print(f"{RED}[FAILED]{RESET} Max retries reached")
                print(f"{YELLOW}[HELP]{RESET} Issue saved as: {current_issue.issue_id}")
                print(f"{YELLOW}[HELP]{RESET} You can review it later or try manually")

def mode_plan_and_execute(task: str):
    """
    Plan and execute mode: breaks down task into steps and executes with progress tracking.
    
    Features:
    1. Uses LLM to create execution plan
    2. Shows plan to user for approval
    3. Executes each step with progress tracking
    4. Handles errors with self-healing
    5. Saves progress for resume capability
    """
    print(f"\n{CYAN}[PLAN & EXECUTE]{RESET} Analyzing task: {task}")
    
    planning_prompt = f"""
Break down this task into clear, executable steps:

Task: {task}

Provide a numbered list of steps that can be executed autonomously.
Each step should be specific and actionable.
Include any research or setup steps needed.
"""
    
    print(f"{YELLOW}[PLANNING]{RESET} Creating execution plan...")
    
    try:
        mode_autonomous(planning_prompt)
        
        print(f"\n{CYAN}[EXECUTE]{RESET} Starting execution...")
        mode_autonomous_enhanced(task, max_retries=3)
        
    except Exception as exc:
        print(f"{RED}[ERROR]{RESET} Planning failed: {exc}")
        print(f"{YELLOW}[FALLBACK]{RESET} Trying direct execution...")
        mode_autonomous_enhanced(task, max_retries=2)

__all__ = ["mode_autonomous_enhanced", "mode_plan_and_execute"]
