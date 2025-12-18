from __future__ import annotations

"""Lightweight research tool using simple HTTP fetch + Ollama summarization."""

import json
from pathlib import Path
from typing import Dict, Any, List

import requests

from agent.learning import ollama_client
from .base import ToolAdapter, ToolResult


def _fetch_wikipedia(query: str) -> Dict[str, Any]:
    try:
        resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}",
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                "content": data.get("extract"),
                "source": "wikipedia",
            }
    except Exception:
        pass
    return {}


def _fetch_duckduckgo(query: str) -> Dict[str, Any]:
    try:
        resp = requests.get("https://duckduckgo.com/html/", params={"q": query}, timeout=10)
        if resp.status_code == 200:
            return {
                "title": "DuckDuckGo results",
                "url": resp.url,
                "content": resp.text[:4000],
                "source": "duckduckgo",
            }
    except Exception:
        pass
    return {}


def _fetch_wikipedia_search(query: str) -> Dict[str, Any]:
    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "opensearch", "search": query, "limit": 1, "format": "json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data[1]:
                return {
                    "title": data[1][0],
                    "url": data[3][0] if data[3] else "",
                    "content": "; ".join(data[1]),
                    "source": "wikipedia-search",
                }
    except Exception:
        pass
    return {}


class ResearchTool(ToolAdapter):
    tool_name = "research"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        query = inputs.get("query") or getattr(task, "goal", None) or getattr(task, "name", None)
        run_path = Path(inputs.get("run_path") or Path("runs") / "research")

        if not query:
            return ToolResult(False, error="No research query provided")

        sources: List[Dict[str, Any]] = []
        for fetcher in (_fetch_duckduckgo, _fetch_wikipedia, _fetch_wikipedia_search):
            result = fetcher(query)
            if result:
                sources.append(result)

        if not sources:
            return ToolResult(False, error="No sources fetched")

        try:
            summary = ollama_client.summarize_research(sources)
            report_md = summary.get("summary_md") or ""
            report_dir = Path(run_path) / "research"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / "research_report.md"
            report_path.write_text(report_md, encoding="utf-8")

            return ToolResult(
                success=True,
                output={
                    "report": str(report_path),
                    "findings": summary.get("key_findings", []),
                    "citations": summary.get("citations", []),
                    "model_used": summary.get("model_used"),
                },
            )
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))


__all__ = ["ResearchTool"]
