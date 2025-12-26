from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent.autonomous.config import RunContext
from agent.autonomous.tools.builtins import WebSearchArgs, web_search


class _Resp:
    def __init__(self, content: bytes):
        self.content = content
        self.encoding = "utf-8"


def test_web_search_no_results(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    def _fake_get(*args, **kwargs):
        html = b"<html><body>No results</body></html>"
        return _Resp(html)

    monkeypatch.setattr("agent.autonomous.tools.builtins.requests.get", _fake_get)

    ctx = RunContext(run_id="t", run_dir=tmp_path, workspace_dir=tmp_path)
    args = WebSearchArgs(query="nothing", max_results=3)
    result = web_search(ctx, args)
    assert result.success is False
    assert result.error == "no_results"
    assert isinstance(result.output, dict)
    assert result.output.get("warning") == "no_results"


def test_web_search_filters_domains(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    def _fake_get(*args, **kwargs):
        html = b"""
        <html>
          <a class="result__a" href="https://en.wikipedia.org/wiki/Agent">Wikipedia</a>
          <a class="result__a" href="https://www.nih.gov/health">NIH</a>
          <span class="result__snippet">Wiki snippet</span>
          <span class="result__snippet">NIH snippet</span>
        </html>
        """
        return _Resp(html)

    monkeypatch.setattr("agent.autonomous.tools.builtins.requests.get", _fake_get)
    monkeypatch.setenv("TREYS_AGENT_WEB_ALLOWLIST", "nih.gov")
    monkeypatch.setenv("TREYS_AGENT_WEB_BLOCKLIST", "wikipedia.org")

    ctx = RunContext(run_id="t", run_dir=tmp_path, workspace_dir=tmp_path)
    args = WebSearchArgs(query="agents", max_results=5)
    result = web_search(ctx, args)
    assert result.success is True
    output = result.output or {}
    results = output.get("results") or []
    assert len(results) == 1
    assert "nih.gov" in (results[0].get("url") or "")
