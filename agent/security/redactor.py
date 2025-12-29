"""
Redactor - Secret removal from logs and traces.

This module ensures secrets are never exposed in:
- Log output
- JSONL traces
- Error messages
- LLM prompts

It identifies and redacts sensitive patterns like:
- API keys
- Tokens
- Passwords
- Connection strings
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Pattern, Set

logger = logging.getLogger(__name__)


# Patterns to detect and redact
SECRET_PATTERNS: List[tuple[str, Pattern]] = [
    # API Keys
    ("api_key", re.compile(r'(sk-[a-zA-Z0-9]{20,})')),
    ("api_key", re.compile(r'(sk-or-[a-zA-Z0-9-]{30,})')),
    ("api_key", re.compile(r'(sk-ant-[a-zA-Z0-9-]{30,})')),
    ("api_key", re.compile(r'(xoxb-[a-zA-Z0-9-]+)')),  # Slack
    ("api_key", re.compile(r'(ghp_[a-zA-Z0-9]{36})')),  # GitHub

    # OAuth Tokens
    ("token", re.compile(r'(ya29\.[a-zA-Z0-9_-]{50,})')),  # Google OAuth
    ("token", re.compile(r'(bearer\s+[a-zA-Z0-9._-]{20,})', re.IGNORECASE)),

    # Passwords in URLs
    ("password", re.compile(r'(://[^:]+:)([^@]+)(@)', re.IGNORECASE)),

    # Generic patterns
    ("secret", re.compile(r'(?i)(api[_-]?key|api[_-]?secret|password|token|secret[_-]?key)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?')),

    # Base64-encoded secrets (commonly OAuth tokens)
    ("encoded", re.compile(r'(eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,})')),  # JWT

    # Connection strings
    ("connection", re.compile(r'(mongodb://[^@]+):([^@]+)(@)')),
    ("connection", re.compile(r'(postgres://[^@]+):([^@]+)(@)')),
]

# Replacement text
REDACTED = "[REDACTED]"


class Redactor:
    """
    Redactor for removing secrets from text.

    Usage:
        redactor = Redactor()

        # Redact a string
        safe_text = redactor.redact("API key is sk-abc123...")

        # Add known secrets to always redact
        redactor.add_secret("my-api-key-value")
    """

    def __init__(self, replacement: str = REDACTED):
        """
        Initialize redactor.

        Args:
            replacement: Text to replace secrets with
        """
        self.replacement = replacement
        self._known_secrets: Set[str] = set()
        self._patterns = SECRET_PATTERNS.copy()

    def add_secret(self, secret: str) -> None:
        """
        Add a known secret to always redact.

        Args:
            secret: The secret value to redact
        """
        if secret and len(secret) >= 4:
            self._known_secrets.add(secret)

    def add_pattern(self, name: str, pattern: Pattern) -> None:
        """
        Add a custom pattern to detect.

        Args:
            name: Name for logging
            pattern: Regex pattern to match
        """
        self._patterns.append((name, pattern))

    def redact(self, text: str) -> str:
        """
        Redact secrets from text.

        Args:
            text: Text that may contain secrets

        Returns:
            Text with secrets replaced
        """
        if not text:
            return text

        result = text

        # Redact known secrets first
        for secret in self._known_secrets:
            if secret in result:
                result = result.replace(secret, self.replacement)

        # Apply pattern-based redaction
        for name, pattern in self._patterns:
            try:
                # For patterns with groups, replace the secret part
                def replacer(match):
                    groups = match.groups()
                    if len(groups) == 1:
                        return self.replacement
                    elif len(groups) == 2:
                        # Pattern like "password=xxx" - redact the value
                        return f"{groups[0]}{self.replacement}"
                    elif len(groups) == 3:
                        # Pattern like ":user:password@" - redact password
                        return f"{groups[0]}{self.replacement}{groups[2]}"
                    return self.replacement

                result = pattern.sub(replacer, result)
            except Exception as e:
                logger.debug(f"Redaction pattern {name} failed: {e}")

        return result

    def redact_dict(self, data: Dict[str, Any], depth: int = 10) -> Dict[str, Any]:
        """
        Redact secrets from a dictionary recursively.

        Args:
            data: Dictionary to redact
            depth: Maximum recursion depth

        Returns:
            Redacted copy of the dictionary
        """
        if depth <= 0:
            return data

        result = {}
        for key, value in data.items():
            # Check if key suggests a secret
            key_lower = key.lower()
            if any(s in key_lower for s in ["password", "secret", "token", "key", "credential"]):
                result[key] = self.replacement
            elif isinstance(value, str):
                result[key] = self.redact(value)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value, depth - 1)
            elif isinstance(value, list):
                result[key] = [
                    self.redact(v) if isinstance(v, str)
                    else self.redact_dict(v, depth - 1) if isinstance(v, dict)
                    else v
                    for v in value
                ]
            else:
                result[key] = value

        return result


# Global instance
_default_redactor: Optional[Redactor] = None


def get_redactor() -> Redactor:
    """Get the default redactor instance."""
    global _default_redactor
    if _default_redactor is None:
        _default_redactor = Redactor()
    return _default_redactor


def redact_secrets(text: str) -> str:
    """
    Convenience function to redact secrets from text.

    Args:
        text: Text that may contain secrets

    Returns:
        Text with secrets replaced
    """
    return get_redactor().redact(text)


def add_known_secret(secret: str) -> None:
    """Add a known secret to always redact."""
    get_redactor().add_secret(secret)


class RedactingHandler(logging.Handler):
    """
    Logging handler that redacts secrets from log messages.

    Usage:
        handler = RedactingHandler(underlying_handler)
        logger.addHandler(handler)
    """

    def __init__(self, underlying_handler: logging.Handler):
        super().__init__()
        self.underlying_handler = underlying_handler
        self.redactor = get_redactor()

    def emit(self, record: logging.LogRecord) -> None:
        # Redact the message
        record.msg = self.redactor.redact(str(record.msg))

        # Redact any args
        if record.args:
            if isinstance(record.args, dict):
                record.args = self.redactor.redact_dict(record.args)
            else:
                record.args = tuple(
                    self.redactor.redact(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )

        self.underlying_handler.emit(record)
