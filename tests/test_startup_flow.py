"""Tests for startup flow."""

import pytest
from agent.autonomous.startup_flow import StartupFlow, ExecutionMode, AnalysisDepth

def test_startup_flow_initialization():
    """Test startup flow initialization."""
    flow = StartupFlow()
    assert flow.task is None
    assert flow.mode is None
    assert flow.depth is None

def test_plan_generation():
    """Test plan generation."""
    flow = StartupFlow()
    responses = {
        "scope": "single_analysis",
        "execution_mode": ExecutionMode.TEAM,
        "depth": AnalysisDepth.DEEP,
        "focus_areas": ["performance", "security"],
    }
    
    plan = flow.generate_plan(responses)
    
    assert plan["mode"] == "team"
    assert plan["depth"] == "deep"
    assert "performance" in plan["focus_areas"]
    assert "security" in plan["focus_areas"]
    assert len(plan["specialists"]) > 0

def test_specialist_selection():
    """Test specialist selection."""
    flow = StartupFlow()
    
    specialists = flow._select_specialists(["quality"], ExecutionMode.SOLO)
    assert specialists == ["general_analyst"]
    
    specialists = flow._select_specialists(
        ["performance", "security", "quality"],
        ExecutionMode.TEAM
    )
    assert "performance_specialist" in specialists
    assert "security_specialist" in specialists
    assert "quality_specialist" in specialists

def test_time_estimation():
    """Test time estimation."""
    flow = StartupFlow()
    
    time_est = flow._estimate_time(ExecutionMode.SOLO, AnalysisDepth.FAST)
    assert "5-10 min" in time_est
    
    time_est = flow._estimate_time(ExecutionMode.TEAM, AnalysisDepth.AUDIT)
    assert "25-40 min" in time_est

def test_cost_estimation():
    """Test cost estimation."""
    flow = StartupFlow()
    
    cost_est = flow._estimate_cost(ExecutionMode.SOLO, AnalysisDepth.FAST)
    assert "$" in cost_est
    
    cost_est = flow._estimate_cost(ExecutionMode.SWARM, AnalysisDepth.AUDIT)
    assert "$" in cost_est
