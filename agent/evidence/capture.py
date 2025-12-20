from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def bundle_evidence(run_path: str | Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal evidence bundler.

    In v1 this simply returns the payload and ensures the evidence folder exists.
    """
    p = Path(run_path)
    evidence_dir = p / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return {"run_path": str(p), **(payload or {})}


__all__ = ["bundle_evidence"]

