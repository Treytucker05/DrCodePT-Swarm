from __future__ import annotations

"""LLM-assisted code review tool (Codex CLI backend)."""

import os
from pathlib import Path
from typing import Dict, Any

from agent.llm import CodexCliClient, schemas as llm_schemas
from .base import ToolAdapter, ToolResult


class CodeReviewTool(ToolAdapter):
    tool_name = "code_review"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        code = inputs.get("code") or getattr(task, "code", None)
        filepath = inputs.get("path") or inputs.get("file_path") or getattr(task, "path", None)
        write_back = bool(inputs.get("write_back", False))
        unsafe_mode = os.getenv("AGENT_UNSAFE_MODE", "").strip().lower() in {"1", "true", "yes", "y", "on"}

        if filepath and not code:
            path_obj = Path(filepath)
            if not path_obj.exists():
                return ToolResult(False, error=f"File not found: {filepath}")
            code = path_obj.read_text(encoding="utf-8")

        if not code:
            return ToolResult(False, error="No code provided for review")

        try:
            llm = CodexCliClient.from_env()
            prompt = (
                "You are a senior code reviewer.\n"
                "Return JSON only.\n\n"
                f"CODE:\n{code}\n"
            )
            review = llm.complete_json(prompt, schema_path=llm_schemas.CODE_REVIEW)

            improved_code = (review.get("improved_code") or "").strip() or code
            changes = review.get("changes") or []
            explanation = (review.get("explanation") or "").strip()

            backup = None
            if filepath and write_back:
                if not unsafe_mode:
                    return ToolResult(
                        False,
                        error="Write-back blocked. Set AGENT_UNSAFE_MODE=true and pass write_back=true to apply changes.",
                    )
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
                    "model_used": llm.model or "default",
                    "backup": str(backup) if backup else None,
                },
            )
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))


__all__ = ["CodeReviewTool"]
