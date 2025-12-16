from __future__ import annotations

"""
Vision tool: screenshots + GPT-4o vision for description and element localization.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .base import ToolAdapter, ToolResult


def _import_pyautogui():
    try:
        import pyautogui
    except ImportError as exc:
        return None, f"PyAutoGUI not installed: {exc}. Run: pip install pyautogui"
    pyautogui.FAILSAFE = False
    return pyautogui, None


def take_screenshot(path: Optional[str] = None) -> Path:
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        raise RuntimeError(err)
    out = Path(path) if path else Path(tempfile.gettempdir()) / "vision_screenshot.png"
    img = pyautogui.screenshot()
    img.save(out)
    return out


class VisionTool(ToolAdapter):
    tool_name = "vision"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        action = inputs.get("action") or getattr(task, "action", None)
        try:
            if action == "screenshot":
                shot = take_screenshot(inputs.get("path"))
                return ToolResult(True, output={"screenshot_path": str(shot)})

            if action == "describe":
                shot = inputs.get("screenshot_path") or str(take_screenshot())
                return ToolResult(False, error="Vision reasoning requires human input", evidence={"screenshot_path": shot})

            if action == "find":
                shot = inputs.get("screenshot_path") or str(take_screenshot())
                return ToolResult(False, error="Vision reasoning requires human input", evidence={"screenshot_path": shot})

            return ToolResult(False, error=f"Unsupported vision action '{action}'")
        except Exception as exc:  # pragma: no cover
            return ToolResult(False, error=str(exc))
