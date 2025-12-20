from __future__ import annotations

"""
HTTP API tool using requests.

Safe-by-default: non-GET methods should be gated by unsafe_mode by the supervisor.
"""

from typing import Any, Dict

import requests

from .base import ToolAdapter, ToolResult


class ApiTool(ToolAdapter):
    tool_name = "api"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        url = inputs.get("url") or inputs.get("endpoint") or getattr(task, "endpoint", None) or getattr(task, "url", None)
        if not url:
            return ToolResult(False, error="api requires endpoint/url")

        method = (inputs.get("method") or getattr(task, "method", None) or "GET").upper()
        headers = inputs.get("headers") or getattr(task, "headers", None) or {}
        params = inputs.get("params") or getattr(task, "params", None) or {}
        body: Any = inputs.get("body") if "body" in inputs else getattr(task, "body", None)
        timeout_seconds = inputs.get("timeout_seconds") or getattr(task, "timeout_seconds", None) or 15

        try:
            resp = requests.request(method, url, headers=headers, params=params, json=body, timeout=int(timeout_seconds))
            text = resp.text
            return ToolResult(
                success=200 <= resp.status_code < 300,
                output={
                    "url": resp.url,
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "text": text[:200000],
                },
                error=None if 200 <= resp.status_code < 300 else f"HTTP {resp.status_code}",
            )
        except requests.RequestException as exc:
            return ToolResult(False, error=str(exc), retryable=True)


__all__ = ["ApiTool"]

