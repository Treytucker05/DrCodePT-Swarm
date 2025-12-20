from __future__ import annotations

from typing import Any, Dict, Optional

from .models import Observation, ToolResult


class Perceptor:
    def tool_result_to_observation(self, tool_name: str, result: ToolResult) -> Observation:
        errors = [result.error] if result.error else []
        parsed: Optional[Dict[str, Any]] = None
        if isinstance(result.output, dict):
            parsed = result.output
        if isinstance(result.metadata, dict) and result.metadata.get("ui_snapshot"):
            if parsed is None:
                parsed = {}
            parsed["ui_snapshot"] = result.metadata.get("ui_snapshot")
        salient = []
        if result.success:
            salient.append(f"{tool_name} succeeded")
        else:
            salient.append(f"{tool_name} failed")
        if result.error:
            salient.append(f"error: {result.error}")
        return Observation(source=f"tool:{tool_name}", raw=result.output, parsed=parsed, errors=errors, salient_facts=salient)

    def text_to_observation(self, source: str, text: str) -> Observation:
        return Observation(source=source, raw=text, parsed={"text": text}, salient_facts=[text[:200]])
