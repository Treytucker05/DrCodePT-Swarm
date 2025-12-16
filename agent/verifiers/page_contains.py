from __future__ import annotations

from typing import Dict

from .base import Verifier, VerifyResult


class PageContainsVerifier(Verifier):
    def verify(self, context: Dict) -> VerifyResult:
        text = self.args.get("text")
        if text is None:
            return VerifyResult(False, "Missing text to search for")

        html = context.get("html") or context.get("page_html") or ""
        found = text in html
        return VerifyResult(found, f"Page contains '{text}': {found}", {"searched_text": text})

