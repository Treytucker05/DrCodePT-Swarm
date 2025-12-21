from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(password|passwd|pwd|token|access[_-]?token|refresh[_-]?token|api[_-]?key|secret|authorization|cookie|set-cookie)"
)
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_URL_PARAM_RE = re.compile(
    r"(?i)(acrumb|sessionindex|access_token|refresh_token|token|code)=([^&\s]+)"
)


def _redact_string(value: str) -> str:
    value = _URL_PARAM_RE.sub(lambda m: f"{m.group(1)}=<REDACTED>", value)
    value = _EMAIL_RE.sub("<REDACTED_EMAIL>", value)
    return value


def redact(value: Any) -> Any:
    """Best-effort redaction for logs (keeps structure, removes secrets/PII)."""
    if value is None:
        return None

    if isinstance(value, str):
        return _redact_string(value)

    if isinstance(value, Path):
        return _redact_string(str(value))

    if isinstance(value, bytes):
        return "<REDACTED_BYTES>"

    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, child in value.items():
            if isinstance(key, str) and _SENSITIVE_KEY_RE.search(key):
                redacted[key] = "<REDACTED>"
                continue
            redacted[key] = redact(child)
        return redacted

    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]

    return value

