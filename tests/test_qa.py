from __future__ import annotations

import json
from pathlib import Path

from agent.autonomous.qa import format_qa_summary, validate_artifacts


def test_validator_catches_missing_and_invalid(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "result.json").write_text("{bad", encoding="utf-8")
    result = validate_artifacts(run_dir, ["trace.jsonl", "result.json"])
    assert result.ok is False
    assert "missing trace.jsonl" in result.errors
    assert "invalid JSON in result.json" in result.errors


def test_validator_passes_for_valid_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "result.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    (run_dir / "trace.jsonl").write_text(json.dumps({"type": "stop"}) + "\n", encoding="utf-8")
    result = validate_artifacts(run_dir, ["trace.jsonl", "result.json"])
    assert result.ok is True


def test_format_qa_summary() -> None:
    lines = format_qa_summary({"A": validate_artifacts(Path("."), [])}, {"ok": True, "message": "ok"})
    assert any(line.startswith("- A:") for line in lines)
    assert any("tests: ok" in line for line in lines)
