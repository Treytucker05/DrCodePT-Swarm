import json
from datetime import datetime, timezone
from pathlib import Path

from agent.autonomous.memory.reflexion import ReflexionEntry, retrieve_reflexions


def test_reflexion_retrieval_matches_objective_and_error(tmp_path, monkeypatch):
    runs_root = tmp_path / "runs"
    run_dir = runs_root / "team" / "run1"
    run_dir.mkdir(parents=True, exist_ok=True)
    entry = ReflexionEntry(
        id="r1",
        timestamp=datetime.now(timezone.utc).isoformat(),
        objective="Fix failing tests",
        context_fingerprint="abc",
        phase="REFLECT",
        tool_calls=[],
        errors=["AssertionError in tests"],
        reflection="Tests failed on missing fixture",
        fix="Add fixture or update test",
        outcome="failure",
        tags=["tests"],
    )
    (run_dir / "reflexion.jsonl").write_text(
        json.dumps(entry.model_dump()) + "\n", encoding="utf-8"
    )

    monkeypatch.setenv("REFLEXION_BASE_DIR", str(runs_root))
    results = retrieve_reflexions("Fix failing tests", "AssertionError", k=3)
    assert results
    assert results[0].objective == "Fix failing tests"
