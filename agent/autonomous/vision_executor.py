"""
Vision-Guided Desktop Executor

Uses screenshots + LLM vision to understand the screen and execute actions.
Inspired by Claude Computer Use and WebVoyager.

The executor:
1. Takes a screenshot
2. Asks the LLM "what do you see? what should I click?"
3. Executes the action
4. Takes another screenshot to verify
5. Loops until task complete or error
"""
from __future__ import annotations

import base64
import json
import logging
import os
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = REPO_ROOT / "agent" / "screenshots"
EVIDENCE_DIR = REPO_ROOT / "evidence"


def _import_pyautogui():
    """Import PyAutoGUI for desktop control."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
        return pyautogui, None
    except ImportError as e:
        return None, f"PyAutoGUI not installed: {e}"


class ScreenState:
    """Represents the current state of the screen."""

    def __init__(self, screenshot_path: Path, timestamp: str):
        self.screenshot_path = screenshot_path
        self.timestamp = timestamp
        self.width: int = 0
        self.height: int = 0

        # Load image dimensions
        try:
            from PIL import Image
            with Image.open(screenshot_path) as img:
                self.width, self.height = img.size
        except Exception:
            pass

    def to_base64(self) -> str:
        """Convert screenshot to base64 for LLM."""
        with open(self.screenshot_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")


class VisionExecutor:
    """
    Executes tasks using vision-guided desktop automation.

    The executor looks at the screen, decides what to do, and acts.
    It uses an LLM to understand screenshots and generate actions.
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.pyautogui = None
        self.current_state: Optional[ScreenState] = None
        self.action_history: List[Dict[str, Any]] = []
        self.max_steps = 50
        self.step_delay = 0.5  # seconds between actions

    def initialize(self) -> Tuple[bool, str]:
        """Initialize the executor."""
        pyautogui, err = _import_pyautogui()
        if not pyautogui:
            return False, err
        self.pyautogui = pyautogui

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        return True, "Initialized"

    def take_screenshot(self, name: str = "screen") -> ScreenState:
        """Take a screenshot of the current screen."""
        if not self.pyautogui:
            self.initialize()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = SCREENSHOTS_DIR / f"{name}_{ts}.png"

        img = self.pyautogui.screenshot()
        img.save(path)

        self.current_state = ScreenState(path, ts)
        return self.current_state

    def analyze_screen(self, objective: str, context: str = "") -> Dict[str, Any]:
        """
        Use LLM to analyze the current screen and decide next action.

        Returns:
            {
                "observation": "what I see on screen",
                "reasoning": "why I should take this action",
                "action": "click|type|scroll|press|goto|done|error",
                "target": {"x": 100, "y": 200} or {"text": "button text"},
                "value": "text to type" (for type action),
                "confidence": 0.0-1.0
            }
        """
        if not self.current_state:
            self.take_screenshot("analysis")

        # Build prompt for vision analysis
        prompt = self._build_vision_prompt(objective, context)

        # Call LLM with screenshot
        try:
            result = self._call_vision_llm(prompt, self.current_state)
            return result
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return {
                "observation": f"Error analyzing screen: {e}",
                "reasoning": "Analysis failed",
                "action": "error",
                "confidence": 0.0,
            }

    def _build_vision_prompt(self, objective: str, context: str) -> str:
        """Build the prompt for vision analysis."""
        history_text = ""
        if self.action_history:
            recent = self.action_history[-5:]  # Last 5 actions
            history_text = "Recent actions:\n" + "\n".join(
                f"- {a['action']}: {a.get('description', '')}" for a in recent
            )

        return f"""You are a desktop automation agent. Analyze this screenshot and decide the next action.

OBJECTIVE: {objective}

{f"CONTEXT: {context}" if context else ""}

{history_text}

Screen size: {self.current_state.width if self.current_state else 1920}x{self.current_state.height if self.current_state else 1080}

Analyze the screenshot and respond with a JSON object:
{{
    "observation": "Brief description of what you see on screen",
    "reasoning": "Why you're taking this action to achieve the objective",
    "action": "click|type|scroll|press|goto|wait|done|ask_user|error",
    "target": {{"x": <number>, "y": <number>}},
    "value": "<text to type>" or "<key to press>" or "<url to goto>" or null,
    "confidence": <0.0 to 1.0>
}}

Actions:
- click: Click at specific x,y coordinates (REQUIRED: you must provide exact pixel coordinates)
- type: Type text (first click on target, then type)
- scroll: Scroll up/down (value: "up" or "down")
- press: Press a key (value: key name like "enter", "tab", "escape")
- goto: Open URL in browser (value: the URL)
- wait: Wait for something to load (value: seconds as string)
- done: Task is complete (value: summary of what was accomplished)
- ask_user: Need user input (value: question to ask)
- error: Something went wrong (value: error description)

CRITICAL RULES:
1. For click actions, you MUST provide exact x,y pixel coordinates - NOT text descriptions
2. Estimate coordinates by looking at where elements are in the image
3. The origin (0,0) is the top-left corner of the screen
4. Look carefully at the screenshot to identify where to click
5. For buttons/links, aim for the CENTER of the element
6. Common locations on Google Cloud Console:
   - Left sidebar navigation: x is typically 100-200
   - Main content area: x is typically 400-800
   - Top navigation: y is typically 50-100
7. If the objective is complete or you see what you need, use "done" action
8. If you truly cannot determine coordinates, use "ask_user" to get help

EXAMPLES:
- To click a menu item on the left sidebar: {{"x": 150, "y": 300}}
- To click a button in the main area: {{"x": 600, "y": 400}}
- To click the search bar at top: {{"x": 500, "y": 60}}
"""

    def _call_vision_llm(self, prompt: str, state: ScreenState) -> Dict[str, Any]:
        """Call the LLM with the screenshot for analysis."""
        # Try using Codex with vision
        if self.llm and hasattr(self.llm, "chat_with_image"):
            response = self.llm.chat_with_image(prompt, state.screenshot_path)
            return self._parse_vision_response(response)

        # Fallback: Use Codex CLI directly with image
        try:
            response = self._call_codex_vision(prompt, state)
            return self._parse_vision_response(response)
        except Exception as e:
            logger.error(f"Codex vision call failed: {e}")

        # Last resort: Ask user
        return {
            "observation": "Could not analyze screen with LLM",
            "reasoning": "Vision analysis not available",
            "action": "ask_user",
            "value": "Please describe what you see and what I should click",
            "confidence": 0.0,
        }

    def _call_codex_vision(self, prompt: str, state: ScreenState) -> str:
        """Call Codex CLI with an image."""
        # Find codex binary
        codex_paths = [
            shutil.which("codex"),
            r"C:\Users\treyt\AppData\Roaming\npm\node_modules\@openai\codex\vendor\x86_64-pc-windows-msvc\codex\codex.exe",
        ]
        codex_bin = next((p for p in codex_paths if p and os.path.exists(p)), None)

        if not codex_bin:
            raise RuntimeError("Codex CLI not found")

        # Note: -i goes with exec subcommand, not before it
        cmd = [
            codex_bin,
            "--dangerously-bypass-approvals-and-sandbox",
            "exec",
            "--skip-git-repo-check",
            "-i", str(state.screenshot_path),  # Image input (after exec)
            "-",  # Read prompt from stdin
        ]

        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=90,  # Vision takes longer
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            raise RuntimeError(f"Codex failed: {result.stderr[:500]}")

        return result.stdout

    def _parse_vision_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into an action dict."""
        # Try to extract JSON from response
        try:
            # Look for JSON block
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response and "}" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                raise ValueError("No JSON found in response")

            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse vision response: {e}")
            return {
                "observation": response[:500],
                "reasoning": "Could not parse structured response",
                "action": "error",
                "value": f"Parse error: {e}",
                "confidence": 0.0,
            }

    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute an action on the desktop."""
        if not self.pyautogui:
            ok, err = self.initialize()
            if not ok:
                return False, err

        action_type = action.get("action", "").lower()
        target = action.get("target")
        value = action.get("value")

        try:
            if action_type == "click":
                return self._do_click(target)

            elif action_type == "type":
                if not value:
                    return False, "No text to type"
                self.pyautogui.write(str(value), interval=0.02)
                return True, f"Typed: {value[:50]}..."

            elif action_type == "scroll":
                direction = str(value or "down").lower()
                clicks = -3 if direction == "down" else 3
                self.pyautogui.scroll(clicks)
                return True, f"Scrolled {direction}"

            elif action_type == "press":
                key = str(value or "enter").lower()
                self.pyautogui.press(key)
                return True, f"Pressed {key}"

            elif action_type == "goto":
                return self._do_goto(value)

            elif action_type == "wait":
                seconds = float(value or 2)
                time.sleep(seconds)
                return True, f"Waited {seconds}s"

            elif action_type == "done":
                return True, f"Task complete: {value}"

            elif action_type == "ask_user":
                # This will be handled by the caller
                return True, f"NEED_USER_INPUT: {value}"

            elif action_type == "error":
                return False, f"Agent reported error: {value}"

            else:
                return False, f"Unknown action: {action_type}"

        except Exception as e:
            return False, f"Action failed: {e}"

    def _do_click(self, target: Any) -> Tuple[bool, str]:
        """Execute a click action."""
        if isinstance(target, dict):
            if "x" in target and "y" in target:
                x, y = int(target["x"]), int(target["y"])
                # Validate coordinates are within screen bounds
                if x < 0 or y < 0:
                    return False, f"Invalid coordinates ({x}, {y}) - coordinates must be positive"
                if self.current_state and (x > self.current_state.width or y > self.current_state.height):
                    logger.warning(f"Coordinates ({x}, {y}) may be outside screen bounds ({self.current_state.width}x{self.current_state.height})")
                self.pyautogui.click(x, y)
                return True, f"Clicked at ({x}, {y})"
            elif "text" in target:
                # Text targets are not supported - provide helpful error
                text = target["text"]
                return False, f"RETRY_WITH_COORDINATES: Cannot click on '{text}' by text. Look at the screenshot and provide exact x,y pixel coordinates for this element."
        elif target is None:
            return False, "No click target provided - need x,y coordinates"
        return False, f"Invalid click target format: {target}. Expected {{\"x\": number, \"y\": number}}"

    def _click_text(self, text: str) -> Tuple[bool, str]:
        """Try to click on text found on screen - NOT IMPLEMENTED, needs coordinates."""
        # Text search is not implemented - LLM must provide coordinates
        return False, f"RETRY_WITH_COORDINATES: Look at the screenshot and provide the x,y pixel coordinates for '{text}'"

    def _do_goto(self, url: str) -> Tuple[bool, str]:
        """Open a URL in the browser."""
        if not url:
            return False, "No URL provided"

        # Find Chrome
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            shutil.which("chrome"),
        ]
        chrome = next((p for p in chrome_paths if p and os.path.exists(p)), None)

        if chrome:
            subprocess.Popen([chrome, url])
            time.sleep(2)  # Wait for browser
            return True, f"Opened {url}"
        else:
            # Try webbrowser module
            import webbrowser
            webbrowser.open(url)
            time.sleep(2)
            return True, f"Opened {url} in default browser"

    def run_task(
        self,
        objective: str,
        context: str = "",
        on_step: Optional[callable] = None,
        on_user_input: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Run a complete task using vision-guided execution.

        Args:
            objective: What to accomplish
            context: Additional context (e.g., from research)
            on_step: Callback for each step (receives step dict)
            on_user_input: Callback to get user input (receives question, returns answer)

        Returns:
            {
                "success": bool,
                "summary": str,
                "steps_taken": int,
                "actions": list,
                "final_screenshot": str,
            }
        """
        ok, err = self.initialize()
        if not ok:
            return {"success": False, "summary": err, "steps_taken": 0}

        self.action_history = []
        steps_taken = 0

        while steps_taken < self.max_steps:
            steps_taken += 1

            # Take screenshot
            state = self.take_screenshot(f"step_{steps_taken}")

            # Analyze screen
            analysis = self.analyze_screen(objective, context)

            # Callback
            if on_step:
                on_step({
                    "step": steps_taken,
                    "screenshot": str(state.screenshot_path),
                    "analysis": analysis,
                })

            # Log
            self.action_history.append({
                "step": steps_taken,
                "action": analysis.get("action"),
                "description": analysis.get("observation"),
                "timestamp": datetime.now().isoformat(),
            })

            action_type = analysis.get("action", "error")

            # Handle completion
            if action_type == "done":
                return {
                    "success": True,
                    "summary": analysis.get("value", "Task completed"),
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                    "final_screenshot": str(state.screenshot_path),
                }

            # Handle user input needed
            if action_type == "ask_user":
                if on_user_input:
                    answer = on_user_input(analysis.get("value", "Need input"))
                    context = f"{context}\nUser said: {answer}"
                    continue
                else:
                    return {
                        "success": False,
                        "summary": f"Need user input: {analysis.get('value')}",
                        "steps_taken": steps_taken,
                        "actions": self.action_history,
                        "final_screenshot": str(state.screenshot_path),
                    }

            # Handle error
            if action_type == "error":
                return {
                    "success": False,
                    "summary": analysis.get("value", "Error occurred"),
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                    "final_screenshot": str(state.screenshot_path),
                }

            # Execute action
            success, message = self.execute_action(analysis)

            if not success:
                # Add error to context and retry
                context = f"{context}\nPrevious action failed: {message}"
                logger.warning(f"Action failed: {message}")

            # Delay before next step
            time.sleep(self.step_delay)

        # Max steps reached
        return {
            "success": False,
            "summary": f"Max steps ({self.max_steps}) reached without completing objective",
            "steps_taken": steps_taken,
            "actions": self.action_history,
            "final_screenshot": str(self.current_state.screenshot_path) if self.current_state else None,
        }


# Singleton instance
_executor: Optional[VisionExecutor] = None


def get_vision_executor(llm=None) -> VisionExecutor:
    """Get the singleton vision executor instance."""
    global _executor
    if _executor is None:
        _executor = VisionExecutor(llm)
    return _executor


__all__ = [
    "VisionExecutor",
    "ScreenState",
    "get_vision_executor",
]
