"""
Hybrid Executor - Event-driven UI automation with vision fallback.

This is the NEW architecture that replaces the vision-only approach.

Flow:
1. Try UI Automation first (fast, deterministic)
2. If element not found, fall back to vision (slow, but works on anything)
3. LLM decides WHAT to do, not WHERE to click

Key insight: The LLM should reason about actions, not pixels.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class HybridExecutor:
    """
    Executes UI tasks using a hybrid approach:
    1. UI Automation (preferred) - Click by element name, not coordinates
    2. Vision (fallback) - When UI tree doesn't help

    The LLM is used for REASONING, not for pixel estimation.
    """

    def __init__(self, llm=None):
        self.llm = llm
        self.ui_controller = None
        self.vision_executor = None  # Fallback only
        self.action_history: List[Dict[str, Any]] = []
        self.max_steps = 50
        self._initialized = False

    def initialize(self) -> Tuple[bool, str]:
        """Initialize both UI automation and vision systems."""
        errors = []

        # Primary: UI Automation
        try:
            from agent.autonomous.windows_ui import get_ui_controller
            self.ui_controller = get_ui_controller()
            ok, msg = self.ui_controller.initialize()
            if not ok:
                errors.append(f"UI Automation: {msg}")
        except Exception as e:
            errors.append(f"UI Automation: {e}")

        # Fallback: Vision (only used when UI automation fails)
        try:
            from agent.autonomous.vision_executor import get_vision_executor
            self.vision_executor = get_vision_executor(self.llm)
            self.vision_executor.initialize()
        except Exception as e:
            errors.append(f"Vision: {e}")

        if self.ui_controller is None and self.vision_executor is None:
            return False, f"No execution method available: {'; '.join(errors)}"

        self._initialized = True
        return True, "Hybrid executor initialized"

    def _get_llm(self):
        """Get or create LLM client."""
        if self.llm:
            return self.llm

        # Try Codex first
        try:
            from agent.llm.codex_cli_client import CodexCliClient
            self.llm = CodexCliClient.from_env()
            return self.llm
        except Exception as e:
            logger.debug(f"Codex not available: {e}")

        # Fall back to OpenRouter
        try:
            from agent.llm.openrouter_client import OpenRouterClient
            self.llm = OpenRouterClient.from_env()
            logger.info("Using OpenRouter for hybrid executor")
            return self.llm
        except Exception as e:
            logger.warning(f"OpenRouter not available: {e}")

        return None

    def _call_llm(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """Call LLM for text reasoning (NOT vision)."""
        llm = self._get_llm()
        if not llm:
            return None

        try:
            # Try Codex-style call first
            if hasattr(llm, 'chat'):
                try:
                    return llm.chat(prompt, timeout_seconds=timeout)
                except TypeError:
                    # OpenRouter doesn't take timeout_seconds
                    return llm.chat(prompt)
            return None
        except Exception as e:
            error_str = str(e).lower()
            # If Codex failed, try OpenRouter as fallback
            if "not authenticated" in error_str or "codex" in error_str:
                logger.warning(f"Codex failed, trying OpenRouter: {e}")
                try:
                    from agent.llm.openrouter_client import OpenRouterClient
                    fallback_llm = OpenRouterClient.from_env()
                    return fallback_llm.chat(prompt)
                except Exception as fallback_e:
                    logger.error(f"OpenRouter fallback failed: {fallback_e}")
            else:
                logger.error(f"LLM call failed: {e}")
            return None

    def get_current_ui_state(self) -> Dict[str, Any]:
        """
        Get the current UI state as TEXT (not screenshot).

        This is passed to the LLM for reasoning.
        """
        if not self.ui_controller:
            return {"error": "UI controller not available"}

        try:
            window = self.ui_controller.get_active_window()
            if not window:
                return {"error": "No active window"}

            tree = self.ui_controller.get_element_tree(window, max_depth=4)
            return {
                "window_title": window.title,
                "window_class": window.class_name,
                "elements": tree.get("elements", [])[:50],  # Limit for token efficiency
            }
        except Exception as e:
            return {"error": str(e)}

    def decide_next_action(self, objective: str, context: str = "") -> Dict[str, Any]:
        """
        Use LLM to decide the next action based on UI STATE (text), not vision.

        This is the key insight: LLM reasons about WHAT to do,
        then we use UI automation to find and click the element.
        """
        ui_state = self.get_current_ui_state()

        if "error" in ui_state:
            # Fall back to vision if we can't read UI state
            return self._decide_with_vision(objective, context)

        # Format UI state for LLM
        elements_text = "\n".join([
            f"- [{e.get('type', 'Unknown')}] \"{e.get('name', '')}\" (enabled={e.get('enabled', True)})"
            for e in ui_state.get("elements", [])
            if e.get("name")  # Only show named elements
        ])

        history_text = ""
        if self.action_history:
            recent = self.action_history[-5:]
            history_text = "Recent actions:\n" + "\n".join(
                f"- {a.get('action')}: {a.get('target', '')} -> {a.get('result', '')}"
                for a in recent
            )

        prompt = f"""You are a UI automation agent. Decide the next action to achieve the objective.

OBJECTIVE: {objective}

{f"CONTEXT: {context}" if context else ""}

CURRENT WINDOW: {ui_state.get('window_title', 'Unknown')}

AVAILABLE UI ELEMENTS:
{elements_text}

{history_text}

Based on the available elements, decide what to do next.
Respond with JSON:
{{
    "reasoning": "Why I'm taking this action",
    "action": "launch|click|type|scroll|press|wait|done|error",
    "target_name": "Exact name of element to interact with (from the list above)",
    "target_type": "Button|Link|Edit|MenuItem|etc",
    "value": "text to type, key to press, or app name to launch",
    "confidence": 0.0-1.0
}}

RULES:
1. If you need to open an application that's not visible, use action="launch" with value="app_name" (e.g., "notepad", "chrome")
2. Use EXACT element names from the list above
3. If the element you need isn't in the list, use action="scroll" or action="error"
4. If objective is complete, use action="done"
5. For typing, first click the Edit field, then type
"""

        response = self._call_llm(prompt, timeout=20)
        if not response:
            return self._decide_with_vision(objective, context)

        return self._parse_action_response(response)

    def _decide_with_vision(self, objective: str, context: str) -> Dict[str, Any]:
        """Fallback: Use vision to decide action when UI tree fails."""
        if not self.vision_executor:
            return {
                "action": "error",
                "reasoning": "Neither UI automation nor vision available",
                "confidence": 0.0,
            }

        # Take screenshot and analyze
        self.vision_executor.take_screenshot("hybrid_fallback")
        return self.vision_executor.analyze_screen(objective, context)

    def _parse_action_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into action dict."""
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response and "}" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                raise ValueError("No JSON found")

            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse action response: {e}")
            return {
                "action": "error",
                "reasoning": f"Failed to parse: {response[:200]}",
                "confidence": 0.0,
            }

    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Execute an action using UI automation (or vision fallback).
        """
        action_type = action.get("action", "").lower()
        target_name = action.get("target_name") or action.get("target", {}).get("text")
        target_type = action.get("target_type")
        value = action.get("value")

        try:
            if action_type == "launch":
                return self._execute_launch(value or target_name)

            elif action_type == "click":
                return self._execute_click(target_name, target_type)

            elif action_type == "type":
                if not value:
                    return False, "No text to type"
                return self._execute_type(target_name, target_type, value)

            elif action_type == "scroll":
                return self._execute_scroll(value or "down")

            elif action_type == "press":
                return self._execute_press(value or "enter")

            elif action_type == "wait":
                seconds = float(value or 2)
                time.sleep(seconds)
                return True, f"Waited {seconds}s"

            elif action_type == "done":
                return True, f"Task complete: {action.get('reasoning', 'Done')}"

            elif action_type == "error":
                return False, f"Agent error: {action.get('reasoning', 'Unknown error')}"

            else:
                return False, f"Unknown action: {action_type}"

        except Exception as e:
            return False, f"Action failed: {e}"

    def _execute_launch(self, app_name: str) -> Tuple[bool, str]:
        """Launch an application by name."""
        import subprocess
        import shutil
        import os
        import tempfile

        app_name_lower = app_name.lower().strip()

        try:
            # Special handling for Notepad - create a new file to avoid "file not found" dialogs
            if "notepad" in app_name_lower:
                # Create a temp file so Notepad opens cleanly
                temp_file = os.path.join(tempfile.gettempdir(), "agent_notepad_temp.txt")
                with open(temp_file, "w") as f:
                    f.write("")  # Empty file
                subprocess.Popen(["notepad.exe", temp_file])
                time.sleep(1.5)
                return True, f"Launched Notepad with new document"

            # Common application mappings
            app_paths = {
                "calculator": "calc.exe",
                "chrome": None,  # Will search for it
                "firefox": None,
                "edge": "msedge.exe",
                "explorer": "explorer.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "code": None,  # VS Code
                "vscode": None,
            }

            # Check if it's a known app
            if app_name_lower in app_paths:
                exe = app_paths[app_name_lower]
                if exe:
                    subprocess.Popen([exe], shell=True)
                    time.sleep(1)
                    return True, f"Launched {app_name}"

            # Try to find Chrome
            if "chrome" in app_name_lower:
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ]
                for path in chrome_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        time.sleep(2)
                        return True, "Launched Chrome"

            # Try to find the app in PATH
            exe_path = shutil.which(app_name_lower) or shutil.which(app_name_lower + ".exe")
            if exe_path:
                subprocess.Popen([exe_path])
                time.sleep(1)
                return True, f"Launched {app_name}"

            # Last resort: try Start Menu search via shell
            subprocess.Popen(f'start "" "{app_name}"', shell=True)
            time.sleep(2)
            return True, f"Attempted to launch {app_name}"

        except Exception as e:
            return False, f"Failed to launch {app_name}: {e}"

    def _execute_click(self, target_name: str, target_type: str = None) -> Tuple[bool, str]:
        """Execute click using UI automation, fall back to vision if needed."""
        if not target_name:
            return False, "No target specified for click"

        # Try UI automation first
        if self.ui_controller:
            success, msg = self.ui_controller.click_element(
                name=target_name,
                control_type=target_type,
                timeout=3.0,
            )
            if success:
                return True, msg

            logger.info(f"UI automation click failed: {msg}, trying vision fallback")

        # Fall back to vision
        if self.vision_executor:
            self.vision_executor.take_screenshot("click_fallback")
            analysis = self.vision_executor.analyze_screen(
                f"Click on '{target_name}'",
                f"Find and click the element named '{target_name}'"
            )
            if analysis.get("action") == "click" and analysis.get("target"):
                return self.vision_executor.execute_action(analysis)

        return False, f"Could not click '{target_name}' with UI automation or vision"

    def _execute_type(self, target_name: str, target_type: str, text: str) -> Tuple[bool, str]:
        """Type text into an element."""
        if self.ui_controller:
            success, msg = self.ui_controller.type_into_element(
                text=text,
                name=target_name,
                control_type=target_type or "Edit",
                timeout=3.0,
            )
            if success:
                return True, msg

        # Fallback: click then type with pyautogui
        try:
            import pyautogui
            # Try to click first
            if target_name:
                self._execute_click(target_name, target_type)
                time.sleep(0.2)
            pyautogui.write(text, interval=0.02)
            return True, f"Typed: {text[:30]}..."
        except Exception as e:
            return False, f"Type failed: {e}"

    def _execute_scroll(self, direction: str) -> Tuple[bool, str]:
        """Scroll the active window."""
        try:
            import pyautogui
            clicks = -3 if direction.lower() == "down" else 3
            pyautogui.scroll(clicks)
            return True, f"Scrolled {direction}"
        except Exception as e:
            return False, f"Scroll failed: {e}"

    def _execute_press(self, key: str) -> Tuple[bool, str]:
        """Press a keyboard key."""
        try:
            import pyautogui
            pyautogui.press(key.lower())
            return True, f"Pressed {key}"
        except Exception as e:
            return False, f"Key press failed: {e}"

    def run_task(
        self,
        objective: str,
        context: str = "",
        on_step: Optional[Callable] = None,
        on_user_input: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Run a complete task using the hybrid approach.

        Unlike the vision-only executor, this:
        1. Reads UI state as TEXT (fast)
        2. Uses LLM for REASONING (not pixel guessing)
        3. Executes with UI automation (deterministic)
        4. Falls back to vision only when needed
        """
        if not self._initialized:
            ok, err = self.initialize()
            if not ok:
                return {"success": False, "summary": err, "steps_taken": 0}

        self.action_history = []
        steps_taken = 0

        while steps_taken < self.max_steps:
            steps_taken += 1

            # Decide next action (uses UI state text, not vision)
            action = self.decide_next_action(objective, context)

            # Log
            self.action_history.append({
                "step": steps_taken,
                "action": action.get("action"),
                "target": action.get("target_name"),
                "result": None,
                "timestamp": datetime.now().isoformat(),
            })

            # Callback
            if on_step:
                on_step({
                    "step": steps_taken,
                    "action": action,
                    "method": "ui_automation" if self.ui_controller else "vision",
                })

            action_type = action.get("action", "error")

            # Handle completion
            if action_type == "done":
                return {
                    "success": True,
                    "summary": action.get("reasoning", "Task completed"),
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                }

            # Handle error
            if action_type == "error":
                return {
                    "success": False,
                    "summary": action.get("reasoning", "Error occurred"),
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                }

            # Execute action
            success, message = self.execute_action(action)
            self.action_history[-1]["result"] = message

            if not success:
                # Add error to context and retry
                context = f"{context}\nPrevious action failed: {message}"
                logger.warning(f"Step {steps_taken} failed: {message}")

            # Small delay between actions
            time.sleep(0.3)

        return {
            "success": False,
            "summary": f"Max steps ({self.max_steps}) reached",
            "steps_taken": steps_taken,
            "actions": self.action_history,
        }


# Singleton
_executor: Optional[HybridExecutor] = None


def get_hybrid_executor(llm=None) -> HybridExecutor:
    """Get the singleton hybrid executor instance."""
    global _executor
    if _executor is None:
        _executor = HybridExecutor(llm)
    return _executor


__all__ = [
    "HybridExecutor",
    "get_hybrid_executor",
]
