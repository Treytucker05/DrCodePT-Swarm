from __future__ import annotations

import json
from pathlib import Path

from agent.autonomous.manifest import write_run_manifest
from agent.autonomous.config import RunnerConfig
from agent.config.profile import resolve_profile


def test_run_manifest_written(tmp_path: Path) -> None:
    profile = resolve_profile("fast")
    cfg = RunnerConfig(max_steps=5, timeout_seconds=30)
    write_run_manifest(
        tmp_path,
        run_id="test-run",
        profile=profile,
        runner_cfg=cfg,
        workers=2,
        mode="swarm",
    )
    manifest_path = tmp_path / "run_manifest.json"
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["profile"] == "fast"
    assert data["workers"] == 2
