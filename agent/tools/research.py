from __future__ import annotations

"""Lightweight research tool using web_search + web_fetch and Codex CLI summarization (optional)."""

import json
from pathlib import Path
from typing import Any, Dict, List

from agent.autonomous.config import RunContext
from agent.autonomous.tools.builtins import WebFetchArgs, WebSearchArgs, web_fetch, web_search
from agent.llm import CodexCliClient, schemas as llm_schemas
from .base import ToolAdapter, ToolResult


def _gather_sources(query: str, ctx: RunContext, *, max_results: int = 6) -> List[Dict[str, Any]]:
    search = web_search(ctx, WebSearchArgs(query=query, max_results=max_results))
    if not search.success:
        return []
    output = search.output or {}
    results = output.get("results") or []
    sources: List[Dict[str, Any]] = []
    for item in results:
        title = (item or {}).get("title") or "Untitled"
        url = (item or {}).get("url") or ""
        snippet = (item or {}).get("snippet") or ""
        excerpt = ""
        if url:
            fetched = web_fetch(ctx, WebFetchArgs(url=url, strip_html=True))
            if fetched.success:
                text = (fetched.output or {}).get("text") or ""
                excerpt = text.strip()[:1500]
        sources.append(
            {
                "title": title,
                "url": url,
                "snippet": snippet,
                "excerpt": excerpt,
            }
        )
    return sources


class ResearchTool(ToolAdapter):
    tool_name = "research"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        query = inputs.get("query") or getattr(task, "goal", None) or getattr(task, "name", None)
        run_path = Path(inputs.get("run_path") or Path("runs") / "research")
        max_results = inputs.get("max_results") or 6
        try:
            max_results = int(max_results)
        except Exception:
            max_results = 6

        if not query:
            return ToolResult(False, error="No research query provided")

        ctx = RunContext(
            run_id="manual",
            run_dir=run_path,
            workspace_dir=run_path,
            profile=None,
            usage=None,
        )
        sources = _gather_sources(query, ctx, max_results=max_results)

        if not sources:
            return ToolResult(False, error="No sources fetched")

        try:
            try:
                llm = CodexCliClient.from_env()
                prompt = (
                    "Summarize the following sources into a concise Markdown report.\n"
                    "Return JSON only.\n\n"
                    f"SOURCES_JSON:\n{json.dumps(sources)[:12000]}\n"
                )
                summary = llm.reason_json(prompt, schema_path=llm_schemas.RESEARCH_SUMMARY)
                summary.setdefault("model_used", llm.model or "default")
            except Exception:
                summary = {
                    "summary_md": "\n".join(
                        [
                            f"- {s.get('title')}: {s.get('url')}\n  - {str(s.get('excerpt') or s.get('snippet') or '')[:400]}..."
                            for s in sources
                        ]
                    ),
                    "key_findings": [],
                    "citations": [
                        {"url": s.get("url"), "title": s.get("title")} for s in sources if s.get("url")
                    ],
                    "model_used": None,
                }

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
