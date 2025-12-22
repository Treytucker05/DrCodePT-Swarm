"""Tests for QA integration."""

import pytest
import tempfile
import json
from pathlib import Path
from agent.autonomous.runner import AgentRunner
from agent.autonomous.config import RunnerConfig, AgentConfig, PlannerConfig


def test_qa_validation_integration():
    """Test QA validation integration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir)
        
        # Create mock result
        result = {
            "status": "success",
            "task_id": "test_task",
            "output": "test output",
        }
        
        # Create artifacts directory
        artifacts_dir = run_dir / "artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "data.json").write_text(json.dumps({"key": "value"}))
        
        # Create runner and run QA
        cfg = RunnerConfig()
        agent_cfg = AgentConfig()
        planner_cfg = PlannerConfig()
        
        # Mock LLM
        from agent.autonomous.llm.stub import StubLLM
        llm = StubLLM(responses=[])
        
        runner = AgentRunner(cfg, agent_cfg, planner_cfg, llm)
        qa_report = runner.run_qa_validation(result, run_dir)
        
        assert "result_validation" in qa_report
        assert "artifact_validation" in qa_report
        assert "qa_summary" in qa_report
        
        # Verify QA report was saved
        qa_report_path = run_dir / "qa_report.json"
        assert qa_report_path.exists()
