from __future__ import annotations

"""
Notification helper and tool.
- Desktop toast on Windows via win10toast
- Optional Pushover push if PUSHOVER_USER_KEY & PUSHOVER_API_TOKEN present
"""

import os
import json
import threading
from typing import Any, Dict

import requests

from .base import ToolAdapter, ToolResult


def _toast(title: str, message: str, duration: int = 5, threaded: bool = True):
    try:
        from win10toast import ToastNotifier
    except ImportError:
        return False, "win10toast not installed. Run: pip install win10toast"
    try:
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=duration, threaded=threaded)
        return True, None
    except Exception as exc:
        return False, str(exc)


def _pushover(title: str, message: str, priority: int = 0):
    user = os.getenv("PUSHOVER_USER_KEY")
    token = os.getenv("PUSHOVER_API_TOKEN")
    if not user or not token:
        return False, "Pushover keys not set"
    try:
        resp = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={"token": token, "user": user, "title": title, "message": message, "priority": priority},
            timeout=10,
        )
        if resp.status_code == 200:
            return True, None
        return False, f"Pushover error {resp.status_code}: {resp.text}"
    except Exception as exc:
        return False, str(exc)


def notify(title: str, message: str, urgent: bool = False) -> Dict[str, Any]:
    """Fire toast + optional Pushover; returns status dict."""
    results = {}
    ok, err = _toast(title, message, duration=10 if urgent else 5)
    results["toast"] = {"success": ok, "error": err}

    push_ok, push_err = _pushover(title, message, priority=1 if urgent else 0)
    results["pushover"] = {"success": push_ok, "error": push_err}
    return results


class NotifyTool(ToolAdapter):
    tool_name = "notify"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        title = inputs.get("title") or getattr(task, "title", "Notification")
        message = inputs.get("message") or getattr(task, "message", "")
        urgent = bool(inputs.get("urgent") or getattr(task, "urgent", False))

        try:
            result = notify(title, message, urgent)
            if not any(v.get("success") for v in result.values()):
                return ToolResult(False, output=result, error="Notification failed")
            return ToolResult(True, output=result)
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))


__all__ = ["notify", "NotifyTool"]
