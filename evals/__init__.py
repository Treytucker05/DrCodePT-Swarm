"""
Eval Framework for DrCodePT-Swarm.

This module provides scenario-based testing for the agent.
It runs predefined scenarios and validates the outcomes.

Usage:
    from evals import run_eval, run_all_evals

    # Run a single eval
    result = run_eval("check_calendar")

    # Run all evals
    results = run_all_evals()
"""

from .runner import EvalRunner, EvalResult, run_eval, run_all_evals

__all__ = [
    "EvalRunner",
    "EvalResult",
    "run_eval",
    "run_all_evals",
]
