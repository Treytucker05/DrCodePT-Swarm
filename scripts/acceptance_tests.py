from __future__ import annotations

import os
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.core.unified_agent import UnifiedAgent


class _NoOpLLM:
    """Fallback LLM that should not be used in fast-path tests."""

    def chat(self, *args, **kwargs):  # pragma: no cover - should not be called
        raise RuntimeError("LLM should not be called in fast-path acceptance tests")


def _run_case(agent: UnifiedAgent, request: str, cwd: Path) -> str:
    os.chdir(cwd)
    result = agent.run(request)
    assert result.success, f"Request failed: {request} -> {result.summary}"
    return result.summary or ""


def main() -> int:
    # Disable any attempt to open files during tests.
    os.environ.setdefault("TREYS_AGENT_OPEN_CREATED_FILE", "0")
    os.environ.setdefault("TREYS_AGENT_STATUS_LINES", "0")
    logging.getLogger("agent.core.intelligent_orchestrator").setLevel(logging.ERROR)

    agent = UnifiedAgent(
        llm_client=_NoOpLLM(),
        on_status=lambda _: None,
        on_user_input=lambda q: "",
        approval_required=False,
    )

    with TemporaryDirectory() as tmp_dir:
        cwd = Path(tmp_dir)
        original_cwd = Path.cwd()

        # Test 1: fast create/write
        _run_case(
            agent,
            'Create a file named test.txt and put "hello world" inside it.',
            cwd,
        )
        created = cwd / "test.txt"
        assert created.exists(), "test.txt was not created"
        assert created.read_text(encoding="utf-8") == "hello world", "test.txt content mismatch"

        # Test 2: read-or-create with default text
        _run_case(
            agent,
            'Read the file missing2.txt and tell me its contents. If it doesn\'t exist, create it with the text "alpha beta".',
            cwd,
        )
        created2 = cwd / "missing2.txt"
        assert created2.exists(), "missing2.txt was not created"
        assert created2.read_text(encoding="utf-8") == "alpha beta", "missing2.txt content mismatch"

        # Test 3: read existing file and confirm content in summary
        summary = _run_case(
            agent,
            "Read the file missing2.txt and tell me its contents.",
            cwd,
        )
        assert "alpha beta" in summary, "read summary missing expected content"

        os.chdir(original_cwd)

    print("Acceptance tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
