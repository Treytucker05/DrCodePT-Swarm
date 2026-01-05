"""Codex CLI smoke test."""
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.llm.codex_cli_client import CodexCliClient

pytestmark = pytest.mark.integration


def run_codex_smoke() -> dict:
    client = CodexCliClient(profile_reason="fast")
    prompt = 'Return JSON: {"test": "hello", "status": "working"}'
    print("[TEST] Calling Codex with simple prompt...")
    return client.reason_json(
        prompt,
        schema_path=Path("agent/llm/schemas/chat_response.schema.json"),
        timeout_seconds=3600,
    )


def test_codex_smoke():
    result = run_codex_smoke()
    assert isinstance(result, dict)


if __name__ == "__main__":
    result = run_codex_smoke()
    print(f"[TEST] Result: {result}")
