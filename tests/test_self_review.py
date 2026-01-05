from __future__ import annotations

from pathlib import Path

from agent.autonomous.config import RunContext
from agent.autonomous.tools.self_review import SelfReviewArgs, self_review


def test_self_review_writes_report(tmp_path: Path) -> None:
    ctx = RunContext(run_id="test", run_dir=tmp_path, workspace_dir=tmp_path)
    report_path = tmp_path / "self_review.md"
    args = SelfReviewArgs(run_tests=False, report_path=str(report_path))
    result = self_review(ctx, args)

    assert result.success is True
    assert result.output is not None
    assert Path(result.output["report_path"]).is_file()
    content = report_path.read_text(encoding="utf-8")
    assert "Self Review Report" in content
