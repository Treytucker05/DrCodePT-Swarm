from __future__ import annotations


class InteractionRequiredError(RuntimeError):
    """Raised when an interactive tool is requested but interaction is disallowed."""

