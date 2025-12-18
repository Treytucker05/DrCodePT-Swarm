"""
Self-Healing Module with LLM-Powered Error Analysis

This module analyzes task failures and generates corrected plans using an LLM.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


def analyze_failure_with_llm(
    task_goal: str,
    error_message: str,
    task_yaml: str,
    execution_log: Dict[str, Any],
    model: str = "gpt-4.1-mini"
) -> Optional[Dict[str, Any]]:
    """
    Analyze a task failure using an LLM and generate a corrected plan.
    
    Args:
        task_goal: The original task goal
        error_message: The error that occurred
        task_yaml: The YAML of the failed task
        execution_log: Log of what happened during execution
        model: LLM model to use for analysis
        
    Returns:
        Dictionary with:
        - analysis: Root cause analysis
        - fix_strategy: Recommended fix approach
        - corrected_yaml: New YAML plan (if fixable)
        - confidence: Confidence score (0-1)
    """
    try:
        from openai import OpenAI
        client = OpenAI()  # API key from environment
        
        # Build the analysis prompt
        prompt = f"""You are an expert at debugging autonomous agent tasks.

TASK GOAL:
{task_goal}

FAILED YAML PLAN:
{task_yaml}

ERROR MESSAGE:
{error_message}

EXECUTION LOG:
{json.dumps(execution_log, indent=2)}

Analyze this failure and provide:
1. Root cause analysis (what went wrong and why)
2. Fix strategy (how to correct it)
3. Corrected YAML plan (if fixable)
4. Confidence score (0.0 to 1.0)

Respond in JSON format:
{{
  "analysis": "detailed root cause analysis",
  "fix_strategy": "step-by-step fix approach",
  "corrected_yaml": "the corrected YAML plan or null if not fixable",
  "confidence": 0.85,
  "is_fixable": true
}}
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at debugging autonomous agent tasks. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"[WARNING] LLM analysis failed: {e}")
        return None


def apply_self_healing(
    run_path: Path,
    task_def,
    error_message: str,
    execution_log: Dict[str, Any]
) -> Optional[str]:
    """
    Apply self-healing to a failed task.
    
    Args:
        run_path: Path to the run directory
        task_def: The TaskDefinition object
        error_message: The error that occurred
        execution_log: Log of execution events
        
    Returns:
        Path to corrected YAML file if healing succeeded, None otherwise
    """
    # Read the original YAML
    yaml_path = run_path / "original_task.yaml"
    if not yaml_path.exists():
        return None
        
    task_yaml = yaml_path.read_text()
    
    # Analyze with LLM
    analysis = analyze_failure_with_llm(
        task_goal=task_def.goal,
        error_message=error_message,
        task_yaml=task_yaml,
        execution_log=execution_log
    )
    
    if not analysis or not analysis.get("is_fixable"):
        return None
        
    # Save the analysis
    analysis_path = run_path / "self_healing_analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2))
    
    # Save the corrected YAML
    if analysis.get("corrected_yaml"):
        corrected_path = run_path / "corrected_task.yaml"
        corrected_path.write_text(analysis["corrected_yaml"])
        return str(corrected_path)
        
    return None


def log_healing_attempt(
    run_path: Path,
    attempt_number: int,
    success: bool,
    details: Dict[str, Any]
):
    """Log a self-healing attempt."""
    log_path = run_path / "healing_log.jsonl"
    
    entry = {
        "attempt": attempt_number,
        "timestamp": str(Path(run_path).stat().st_mtime),
        "success": success,
        "details": details
    }
    
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    # Test the module
    test_analysis = analyze_failure_with_llm(
        task_goal="Create a file named test.txt",
        error_message="Permission denied",
        task_yaml="id: test\nname: Test\ntype: shell\ngoal: Create file\ncommand: touch /root/test.txt",
        execution_log={"error": "Permission denied"}
    )
    
    if test_analysis:
        print("Self-healing analysis:")
        print(json.dumps(test_analysis, indent=2))
    else:
        print("Analysis failed")
