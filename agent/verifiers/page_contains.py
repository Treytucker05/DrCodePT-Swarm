from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .base import VerifierAdapter, VerifierResult


def _load_html_from_context(context: Dict[str, Any]) -> str:
    html = context.get("html")
    if isinstance(html, str) and html:
        return html

    last = context.get("last_result") or {}
    if isinstance(last, dict):
        for key in ("html", "text", "dom_snapshot"):
            v = last.get(key)
            if isinstance(v, str) and v:
                return v

    evidence = context.get("evidence") or {}
    if isinstance(evidence, dict):
        html_path = evidence.get("html")
        if isinstance(html_path, str) and html_path:
            p = Path(html_path)
            if p.exists():
                return p.read_text(encoding="utf-8", errors="replace")

    return ""


class PageContainsVerifier(VerifierAdapter):
    verifier_id = "page_contains"

    def verify(self, context: Dict[str, Any]) -> VerifierResult:
        text = self.args.get("text")
        if text is None:
            return VerifierResult(id=self.verifier_id, passed=False, details="page_contains requires args.text")

        html = _load_html_from_context(context)
        passed = str(text) in html if html else False
        return VerifierResult(id=self.verifier_id, passed=passed, details="found" if passed else "not_found")


__all__ = ["PageContainsVerifier"]

