from __future__ import annotations

"""
Desktop control tool built on PyAutoGUI.
Supports mouse actions (move, click, drag), keyboard (type, hotkey, press), and screenshots.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .base import ToolAdapter, ToolResult


def _import_pyautogui():
    try:
        import pyautogui
    except ImportError as exc:
        return None, f"PyAutoGUI not installed: {exc}. Run: pip install pyautogui"
    pyautogui.FAILSAFE = False  # avoid abrupt aborts on corner hits
    return pyautogui, None


def _coords(inputs: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    x = inputs.get("x")
    y = inputs.get("y")
    if x is None or y is None:
        return None
    try:
        return int(x), int(y)
    except Exception:
        return None


class DesktopTool(ToolAdapter):
    tool_name = "desktop"

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        action = inputs.get("action") or getattr(task, "action", None)
        if not action:
            return ToolResult(False, error="No desktop action provided")

        pyautogui, err = _import_pyautogui()
        if not pyautogui:
            return ToolResult(False, error=err)

        try:
            if action == "move":
                coords = _coords(inputs)
                if not coords:
                    return ToolResult(False, error="move requires x and y")
                duration = float(inputs.get("duration", 0.0))
                pyautogui.moveTo(coords[0], coords[1], duration=duration)
                return ToolResult(True, output={"moved_to": coords})

            if action == "click":
                coords = _coords(inputs)
                clicks = int(inputs.get("clicks", 1))
                button = inputs.get("button", "left")
                if coords:
                    pyautogui.click(x=coords[0], y=coords[1], clicks=clicks, button=button)
                else:
                    pyautogui.click(clicks=clicks, button=button)
                return ToolResult(True, output={"clicked": coords or "current", "button": button, "clicks": clicks})

            if action == "drag":
                start = _coords(inputs) or tuple(pyautogui.position())
                end = inputs.get("to")
                if isinstance(end, (list, tuple)) and len(end) == 2:
                    end_x, end_y = int(end[0]), int(end[1])
                else:
                    end_x, end_y = inputs.get("to_x"), inputs.get("to_y")
                if end_x is None or end_y is None:
                    return ToolResult(False, error="drag requires to_x/to_y or to=[x,y]")
                duration = float(inputs.get("duration", 0.2))
                pyautogui.moveTo(start[0], start[1])
                pyautogui.dragTo(end_x, end_y, duration=duration, button=inputs.get("button", "left"))
                return ToolResult(True, output={"dragged_from": start, "to": (end_x, end_y)})

            if action == "type":
                text = inputs.get("text", "")
                interval = float(inputs.get("interval", 0.02))
                pyautogui.write(str(text), interval=interval)
                return ToolResult(True, output={"typed": text})

            if action == "hotkey":
                keys = inputs.get("keys") or inputs.get("hotkeys")
                if not keys or not isinstance(keys, (list, tuple)):
                    return ToolResult(False, error="hotkey requires keys list")
                pyautogui.hotkey(*[str(k) for k in keys])
                return ToolResult(True, output={"hotkey": keys})

            if action == "press":
                key = inputs.get("key")
                if not key:
                    return ToolResult(False, error="press requires key")
                presses = int(inputs.get("presses", 1))
                pyautogui.press(key, presses=presses)
                return ToolResult(True, output={"pressed": key, "presses": presses})

            if action == "screenshot":
                path = inputs.get("path")
                if path:
                    path = Path(path)
                else:
                    path = Path(tempfile.gettempdir()) / f"desktop_ss.png"
                img = pyautogui.screenshot()
                img.save(path)
                return ToolResult(True, output={"screenshot_path": str(path)})

            return ToolResult(False, error=f"Unsupported desktop action '{action}'")
        except Exception as exc:  # pragma: no cover - runtime safety
            return ToolResult(False, error=str(exc))
