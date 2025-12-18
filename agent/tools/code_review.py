from __future__ import annotations

"""Code review tool powered by Ollama."""

from pathlib import Path
from typing import Dict, Any

from agent.learning import ollama_client
from .base import ToolAdapter, ToolResult


class CodeReviewTool(ToolAdapter):
    tool_name = "code_review"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        code = inputs.get("code") or getattr(task, "code", None)
        filepath = inputs.get("path") or inputs.get("file_path") or getattr(task, "path", None)

        if filepath and not code:
            path_obj = Path(filepath)
            if not path_obj.exists():
                return ToolResult(False, error=f"File not found: {filepath}")
            code = path_obj.read_text(encoding="utf-8")

        if not code:
            return ToolResult(False, error="No code provided for review")

        try:
            review = ollama_client.review_code(code)
            improved_code = review.get("improved_code") or code
            changes = review.get("changes") or []
            explanation = review.get("explanation") or ""

            if filepath:
                path_obj = Path(filepath)
                backup = path_obj.with_suffix(path_obj.suffix + ".backup")
                path_obj.rename(backup)
                path_obj.write_text(improved_code, encoding="utf-8")

            return ToolResult(
                success=True,
                output={
                    "improved_code": improved_code,
                    "changes": changes,
                    "explanation": explanation,
                    "model_used": review.get("model_used"),
                    "backup": str(backup) if filepath else None,
                },
            )
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))


__all__ = ["CodeReviewTool"]
