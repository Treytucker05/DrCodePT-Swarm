from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_MEMORY_EMBED_BACKEND", "hash")
    monkeypatch.setenv("AGENT_MEMORY_FAISS_DISABLE", "1")
    monkeypatch.setenv("AUTO_PLANNER_MODE", "react")
    yield
