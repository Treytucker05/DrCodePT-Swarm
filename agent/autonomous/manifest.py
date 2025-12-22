from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from agent.autonomous.config import RunnerConfig
from agent.config.profile import ProfileConfig


def write_run_manifest(
    run_dir: Path,
    *,
    run_id: str,
    profile: Optional[ProfileConfig],
    runner_cfg: RunnerConfig,
    workers: int,
    mode: str,
) -> None:
    budgets: Dict[str, Any] = {}
    if profile is not None:
        budgets = {
            "max_files_to_read": profile.max_files_to_read,
            "max_total_bytes_to_read": profile.max_total_bytes_to_read,
            "max_glob_results": profile.max_glob_results,
            "max_web_sources": profile.max_web_sources,
        }
    payload = {
        "run_id": run_id,
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "profile": profile.name if profile else None,
        "workers": int(workers),
        "budgets": budgets,
        "timeouts": {
            "timeout_seconds": runner_cfg.timeout_seconds,
            "plan_timeout_seconds": runner_cfg.llm_plan_timeout_seconds,
            "plan_retry_timeout_seconds": runner_cfg.llm_plan_retry_timeout_seconds,
            "heartbeat_seconds": runner_cfg.llm_heartbeat_seconds,
            "llm_max_retries": runner_cfg.llm_max_retries,
            "tool_max_retries": runner_cfg.tool_max_retries,
        },
    }
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run_manifest.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        return
