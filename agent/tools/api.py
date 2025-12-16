from __future__ import annotations

"""REST API tool using requests."""

from typing import Any, Dict

import requests

from .base import ToolAdapter, ToolResult


class ApiTool(ToolAdapter):
    tool_name = "api"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        endpoint = getattr(task, "endpoint", None) or inputs.get("endpoint")
        method = getattr(task, "method", None) or inputs.get("method") or "GET"
        if not endpoint:
            return ToolResult(False, error="No endpoint provided for api task")

        data = inputs.get("data")
        headers = inputs.get("headers") or {}
        params = inputs.get("params") or {}

        try:
            resp = requests.request(method, endpoint, json=data, params=params, headers=headers, timeout=getattr(task, "timeout_seconds", 20))
            return ToolResult(
                success=resp.ok,
                output={"status_code": resp.status_code, "headers": dict(resp.headers), "body": resp.text},
                error=None if resp.ok else f"HTTP {resp.status_code}",
            )
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))

