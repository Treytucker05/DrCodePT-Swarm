"""
Hybrid Executor - Event-driven UI automation with vision fallback.

This is the NEW architecture that replaces the vision-only approach.

Flow:
1. Try UI Automation first (fast, deterministic)
2. If element not found, fall back to vision (slow, but works on anything)
3. LLM decides WHAT to do, not WHERE to click

Key insight: The LLM should reason about actions, not pixels.

Enhanced with:
- Stop-Think-Replan pattern on failures
- ThrashGuard integration to detect stuck loops
- Precondition/postcondition verification
- Exploration policy (scroll/retry when element not found)
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Literal
from uuid import uuid4
from types import SimpleNamespace

from pydantic import BaseModel, Field

from agent.llm.json_enforcer import build_repair_prompt, enforce_json_response

logger = logging.getLogger(__name__)

# Import guard types for stuck loop detection
try:
    from .guards import ThrashGuard, ThrashDetection, EscalationAction, GuardConfig
    from .state import UnifiedAgentState, StepRecord, Observation
    GUARDS_AVAILABLE = True
except ImportError:
    GUARDS_AVAILABLE = False
    logger.debug("Guards module not available - stuck loop detection disabled")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from pydantic import ConfigDict
except Exception:  # pragma: no cover - pydantic v1 fallback
    ConfigDict = None


class UIActionModel(BaseModel):
    reasoning: str
    action: Literal[
        "launch",
        "click",
        "type",
        "scroll",
        "press",
        "wait",
        "done",
        "error",
        "ask_user",
    ]
    target_name: Optional[str] = None
    target_type: Optional[str] = None
    value: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


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
        self._disable_codex = False
        self.state = SimpleNamespace(active_window=None)
        self._browser_action = False

        # Reflection system (integrated)
        self.reflector = None
        try:
            from agent.autonomous.reflection import Reflector
            self.reflector = Reflector(llm=llm, pre_mortem_enabled=True)
            logger.debug("Reflector initialized with pre-mortem enabled")
        except Exception as e:
            logger.debug(f"Could not initialize Reflector: {e}")

        # Stuck loop detection (Gap #9)
        self._thrash_guard = None
        self._agent_state = None
        if GUARDS_AVAILABLE:
            # Lower thresholds for faster detection during UI automation
            config = GuardConfig(
                max_repeated_actions=2,  # Detect after 2 same actions
                max_file_reads=3,
                max_steps_no_progress=4,  # Detect after 4 failed steps
                max_same_errors=2,
                auto_escalate=True,
            )
            self._thrash_guard = ThrashGuard(config)

        # Exploration state (Gap #3 - exploration policy)
        self._exploration_attempts = 0
        self._max_exploration_attempts = 3  # Try scroll/wait before giving up

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
        if self.llm and not self._disable_codex:
            return self.llm

        # Prefer Codex if available - use if client creation succeeds (no auth check gate)
        if not self._disable_codex:
            try:
                from agent.llm.codex_cli_client import CodexCliClient

                client = CodexCliClient.from_env()
                # Client creation succeeded - use it (don't gate on auth check)
                self.llm = client
                self._log_llm_use(self.llm, "hybrid_executor")
                return self.llm
            except Exception as e:
                logger.debug(f"Codex not available: {e}")

        # Fall back to OpenRouter if configured
        if os.getenv("OPENROUTER_API_KEY"):
            try:
                from agent.llm.openrouter_client import OpenRouterClient        

                self.llm = OpenRouterClient.from_env()
                self._log_llm_use(self.llm, "hybrid_executor")
                return self.llm
            except Exception as e:
                logger.warning(f"OpenRouter not available: {e}")

        return None

    def _log_llm_use(self, llm: Any, purpose: str) -> None:
        provider = getattr(llm, "provider", getattr(llm, "provider_name", "unknown"))
        model = getattr(llm, "model", None) or "default"
        logger.info(f"[LLM] {purpose}: provider={provider} model={model}")

    def _call_llm(
        self,
        prompt: str,
        timeout: int = 30,
        *,
        llm_client: Optional[Any] = None,
    ) -> Optional[str]:
        """Call LLM for text reasoning (NOT vision)."""
        llm = llm_client or self._get_llm()
        if not llm:
            return None

        self._log_llm_use(llm, "ui_action")

        try:
            if hasattr(llm, "chat"):
                try:
                    return llm.chat(prompt, timeout_seconds=timeout)
                except TypeError:
                    return llm.chat(prompt)
            return None
        except Exception as e:
            error_str = str(e).lower()
            if "not authenticated" in error_str or "codex" in error_str:
                self._disable_codex = True
                if getattr(llm, "provider", "") == "codex_cli":
                    self.llm = None
                logger.warning(f"Codex failed, trying OpenRouter: {e}")
                try:
                    from agent.llm.openrouter_client import OpenRouterClient

                    fallback_llm = OpenRouterClient.from_env()
                    self.llm = fallback_llm
                    self._log_llm_use(fallback_llm, "ui_action_fallback")
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

    def _is_browser_window(self, ui_state: Dict[str, Any]) -> bool:
        title = (ui_state.get("window_title") or "").lower()
        class_name = (ui_state.get("window_class") or "").lower()
        tokens = ["chrome", "edge", "firefox", "brave", "arc", "chromium"]
        return any(token in title for token in tokens) or any(token in class_name for token in tokens)

    def _validate_action_data(
        self,
        data: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            if hasattr(UIActionModel, "model_validate"):
                model = UIActionModel.model_validate(data)  # type: ignore[attr-defined]
                return model.model_dump(), None  # type: ignore[attr-defined]
            model = UIActionModel.parse_obj(data)  # type: ignore[attr-defined]
            return model.dict(), None  # type: ignore[attr-defined]
        except Exception as exc:
            return None, str(exc)

    def _action_error(
        self,
        message: str,
        *,
        raw_response: Optional[str] = None,
        parse_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            from agent.autonomous.models import ToolResult

            metadata: Dict[str, Any] = {}
            if raw_response:
                metadata["raw_response"] = raw_response[:500]
            if parse_error:
                metadata["parse_error"] = parse_error
            tool_result = ToolResult(success=False, error=message, metadata=metadata)
            tool_payload = tool_result.model_dump() if hasattr(tool_result, "model_dump") else tool_result.dict()
        except Exception:
            tool_payload = {
                "success": False,
                "error": message,
                "metadata": {"parse_error": parse_error, "raw_response": (raw_response or "")[:200]},
            }

        return {
            "action": "error",
            "reasoning": message,
            "confidence": 0.0,
            "tool_result": tool_payload,
        }

    def _normalize_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        NORMALIZE LLM ACTIONS AFTER PARSING (Requirement #3).

        LLMs sometimes return {"action":"click","target":null}.
        This normalizes such cases to prevent crashes.

        Returns normalized action dict.
        """
        if not isinstance(action, dict):
            logger.warning(f"Action normalization received non-dict: {type(action)}")
            return action

        # Remove None target
        if action.get("target") is None:
            action.pop("target", None)
            logger.debug("Normalized: Removed null target")

        # Ensure target is a dict if present
        if "target" in action and not isinstance(action["target"], dict):
            logger.debug(f"Normalized: Converting non-dict target {type(action['target'])} to empty dict")
            action["target"] = {}

        return action

    def decide_next_action(self, objective: str, context: str = "", screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Use LLM to decide the next action based on UI STATE (text), not vision.

        This is the key insight: LLM reasons about WHAT to do,
        then we use UI automation to find and click the element.
        """
        ui_state = self.get_current_ui_state()

        self._browser_action = False
        if "error" in ui_state:
            # Fall back to vision if we can't read UI state
            if self.ui_controller:
                try:
                    window = self.ui_controller.get_active_window()
                    title = (window.title or "").lower() if window else ""
                    class_name = (window.class_name or "").lower() if window else ""
                    if "chrome" in title or "chrome" in class_name:
                        self._browser_action = True
                except Exception:
                    pass
            return self._decide_with_vision(objective, context)

        if self._is_browser_window(ui_state):
            # ALWAYS use vision for browser windows - web UIs are too complex for UI automation
            logger.info("Browser window detected - using vision executor")
            self._browser_action = True
            return self._decide_with_vision(objective, context)

        # Also check if the window has very few UI elements (likely a web page)
        elements = ui_state.get("elements", [])
        if len(elements) < 5:
            logger.info("Few UI elements detected - likely web content, using vision executor")
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
{f"SCREENSHOT: {screenshot_path}" if screenshot_path else ""}

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

        llm = self._get_llm()
        if not llm:
            return self._action_error("No LLM available for UI action selection")

        if hasattr(llm, "reason_json"):
            schema = (
                UIActionModel.model_json_schema()
                if hasattr(UIActionModel, "model_json_schema")
                else UIActionModel.schema()
            )
            # Codex response_format requires a required list containing all properties.
            props = schema.get("properties") or {}
            if props:
                schema["required"] = list(props.keys())
            schema_path = Path(tempfile.gettempdir()) / f"ui_action_schema_{uuid4().hex[:8]}.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")        
            try:
                error = None
                data: Dict[str, Any] = {}
                for attempt in range(3):
                    data = llm.reason_json(prompt, schema_path=schema_path, timeout_seconds=20)
                    validated, error = self._validate_action_data(data if isinstance(data, dict) else {})
                    if validated:
                        # NORMALIZE: Apply normalization before returning
                        return self._normalize_action(validated)
                    prompt = build_repair_prompt(schema, previous=json.dumps(data))
                return self._action_error(
                    "Invalid JSON from model after repair attempts",
                    raw_response=json.dumps(data),
                    parse_error=error,
                )
            except Exception as exc:
                logger.warning(f"LLM JSON action call failed: {exc}")
            finally:
                try:
                    schema_path.unlink()
                except Exception:
                    pass

        response = self._call_llm(prompt, timeout=20, llm_client=llm)
        if not response:
            return self._action_error("No response from LLM for UI action selection")

        # NORMALIZE: Apply normalization after parsing
        action = self._parse_action_response(response, llm_client=llm)
        return self._normalize_action(action)

    def _decide_with_vision(self, objective: str, context: str) -> Dict[str, Any]:
        """Fallback: Use vision to decide action when UI tree fails."""
        if not self.vision_executor:
            return {
                "action": "error",
                "reasoning": "Neither UI automation nor vision available",
                "confidence": 0.0,
            }

        # Take screenshot and analyze
        if self._browser_action and self.ui_controller:
            if not self._focus_chrome_window():
                return self._action_error("Could not focus Chrome window - ensure Chrome is running")
            time.sleep(0.2)
            try:
                bounds = self.ui_controller.get_chrome_window_bounds()
                self.state.active_window = {"app": "chrome", **bounds}
                region = (bounds["left"], bounds["top"], bounds["width"], bounds["height"])
                self.vision_executor.take_screenshot_region("hybrid_fallback", region)
            except Exception as e:
                return self._action_error(f"Chrome window not available: {e}")
        else:
            self.vision_executor.take_screenshot("hybrid_fallback")
        action = self.vision_executor.analyze_screen(objective, context)
        # NORMALIZE: Apply normalization to vision-decided actions too
        return self._normalize_action(action)

    def _parse_action_response(
        self,
        response: str,
        *,
        llm_client: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Parse LLM response into action dict with schema enforcement and repair."""
        data, error = enforce_json_response(
            response,
            model_cls=UIActionModel,
            retry_call=lambda prompt: self._call_llm(prompt, timeout=20, llm_client=llm_client),
            max_retries=2,
        )
        if data:
            # NORMALIZE: Apply normalization after successful parse
            return self._normalize_action(data)
        logger.warning(f"Failed to parse action response after repair: {error}")
        return self._action_error(
            "Invalid JSON from model after repair attempts",
            raw_response=response,
            parse_error=error,
        )

    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Execute an action using UI automation (or vision fallback).
        """
        action_type = action.get("action", "").lower()
        if action_type in {"open_url", "type", "press"} and self._browser_action:
            if not self._focus_chrome_window():
                return False, "Could not focus Chrome window - ensure Chrome is running"
            time.sleep(0.2)
        if action_type in {"click", "type", "scroll", "press"} and self._browser_action and self.ui_controller:
            try:
                bounds = self.ui_controller.get_chrome_window_bounds()
                self.state.active_window = {"app": "chrome", **bounds}
            except Exception as e:
                return False, f"Chrome window not available: {e}"

        # NULL-SAFE: Handle target being None or non-dict
        target_obj = action.get("target") or {}
        if not isinstance(target_obj, dict):
            target_obj = {}

        target_name = action.get("target_name") or target_obj.get("text")
        target_type = action.get("target_type")
        target_coords = target_obj
        value = action.get("value")

        try:
            # DETERMINISTIC: open_url bypasses all UI/vision logic
            if action_type == "open_url":
                return self._execute_open_url(value)

            if action_type == "launch":
                return self._execute_launch(value or target_name)

            elif action_type == "click":
                # Check if we have pixel coordinates from vision
                if isinstance(target_coords, dict) and "x" in target_coords and "y" in target_coords:
                    # Vision-guided click with pixel coordinates
                    return self._execute_click_at_coords(target_coords["x"], target_coords["y"])
                else:
                    # UI automation click by element name
                    return self._execute_click(target_name, target_type)

            elif action_type == "type":
                if not value:
                    return False, "No text to type"
                return self._execute_type(target_name, target_type, value)

            elif action_type == "scroll":
                return self._execute_scroll(value or "down")

            elif action_type == "press":
                return self._execute_press(value or "enter")

            elif action_type == "goto":
                return self._execute_open_url(value or target_name)

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

    def _execute_open_url(self, url: str) -> Tuple[bool, str]:
        """
        DETERMINISTIC URL opener - bypasses all UI/vision logic.

        Opens Chrome browser only (does NOT navigate). Navigation should be done
        via prepare_and_navigate_chrome() to guarantee correctness.
        """
        import subprocess
        import shutil
        import os

        try:
            self._focus_chrome_window()
            time.sleep(0.2)
            # Check for configured Chrome path
            chrome_path = os.getenv("TREYS_AGENT_CHROME_PATH")
            if chrome_path and os.path.exists(chrome_path):
                # Launch Chrome without URL - navigation will be done separately
                # Check if profile args are present (agent-controlled instance)
                user_data_dir = os.getenv("TREYS_AGENT_CHROME_USER_DATA_DIR")
                profile = os.getenv("TREYS_AGENT_CHROME_PROFILE")
                cmd = [chrome_path]
                if user_data_dir or profile:
                    cmd.append("--force-renderer-accessibility")
                    logger.info("[CHROME] Launched with forced accessibility")
                cmd.append("about:blank")
                subprocess.Popen(cmd)
                time.sleep(2)
                logger.info(f"Launched Chrome via configured path: {chrome_path}")
                return True, "Chrome launched"

            # Find Chrome in standard locations
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                shutil.which("chrome"),
            ]
            chrome = next((p for p in chrome_paths if p and os.path.exists(p)), None)

            if chrome:
                # Respect profile if configured
                user_data_dir = os.getenv("TREYS_AGENT_CHROME_USER_DATA_DIR")
                profile = os.getenv("TREYS_AGENT_CHROME_PROFILE")

                cmd = [chrome]
                if user_data_dir:
                    cmd.extend([f"--user-data-dir={user_data_dir}"])
                if profile:
                    cmd.extend([f"--profile-directory={profile}"])
                # Add accessibility flag for agent-controlled Chrome instances
                if user_data_dir or profile:
                    cmd.append("--force-renderer-accessibility")
                    logger.info("[CHROME] Launched with forced accessibility")
                # Launch Chrome without URL - navigation will be done separately
                cmd.append("about:blank")

                subprocess.Popen(cmd)
                time.sleep(2)
                logger.info("Launched Chrome")
                return True, "Chrome launched"
            else:
                # Fallback: system default browser
                import webbrowser
                webbrowser.open("about:blank")
                time.sleep(2)
                logger.info("Launched default browser")
                return True, "Browser launched"

        except Exception as e:
            logger.error(f"Failed to launch Chrome: {e}")
            return False, f"Failed to launch Chrome: {e}"

    def _execute_goto(self, url: str) -> Tuple[bool, str]:
        """
        DEPRECATED: Use open_url action instead.

        This is kept for backward compatibility but delegates to _execute_open_url.
        """
        return self._execute_open_url(url)

    def _check_precondition(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check preconditions before executing an action (Gap #4).

        This prevents actions that are doomed to fail.
        """
        # NULL-SAFE: Validate action is a dict
        if not isinstance(action, dict):
            return False, "Invalid action (not a dict)"

        action_type = action.get("action", "").lower()

        # NULL-SAFE: Handle target being None or non-dict
        target_obj = action.get("target") or {}
        if not isinstance(target_obj, dict):
            target_obj = {}

        target_name = action.get("target_name") or target_obj.get("text")
        target_coords = target_obj

        # open_url requires no target - it's deterministic
        if action_type == "open_url":
            if not action.get("value"):
                return False, "No URL specified for open_url action"
            return True, "Preconditions met"

        # For click/type actions, verify we have either a target name OR pixel coordinates
        if action_type in ("click", "type"):
            # Allow vision-guided actions with pixel coordinates (no target_name needed)
            has_pixel_coords = isinstance(target_coords, dict) and "x" in target_coords and "y" in target_coords

            if not target_name and not has_pixel_coords:
                return False, f"No target specified for {action_type} (need target_name or x,y coordinates)"

            # Only check for active window if using UI automation (target_name)
            if target_name and self.ui_controller:
                try:
                    window = self.ui_controller.get_active_window()
                    if not window:
                        return False, "No active window found - cannot interact with UI"
                except Exception as e:
                    logger.debug(f"Window check failed: {e}")

        # For type actions, verify we have text
        if action_type == "type":
            if not action.get("value"):
                return False, "No text specified for type action"

        return True, "Preconditions met"

    def _verify_postcondition(self, action: Dict[str, Any], result: Tuple[bool, str]) -> Tuple[bool, str]:
        """
        Verify postconditions after executing an action (Gap #4).

        This confirms the action had the intended effect.
        """
        success, message = result
        if not success:
            return result  # Already failed

        action_type = action.get("action", "").lower()

        # For type actions, we could verify text was entered (future enhancement)
        # For click actions, we could verify UI state changed

        # For now, trust the action result but log for future improvement
        logger.debug(f"Postcondition check passed for {action_type}: {message}")
        return result

    def _try_exploration(self, target_name: str, action_type: str) -> Tuple[bool, str, bool]:
        """
        Try exploration tactics when element not found (Gap #3 - exploration policy).

        Returns: (should_retry, message, element_found)
        """
        if self._exploration_attempts >= self._max_exploration_attempts:
            self._exploration_attempts = 0  # Reset for next action
            return False, "Max exploration attempts reached", False

        self._exploration_attempts += 1
        attempt = self._exploration_attempts

        logger.info(f"Exploration attempt {attempt}/{self._max_exploration_attempts} for '{target_name}'")

        if attempt == 1:
            # First: Try scrolling down to find the element
            try:
                import pyautogui
                pyautogui.scroll(-3)  # Scroll down
                time.sleep(0.5)
                return True, "Scrolled down to look for element", False
            except Exception as e:
                logger.debug(f"Scroll failed: {e}")

        elif attempt == 2:
            # Second: Try scrolling up
            try:
                import pyautogui
                pyautogui.scroll(3)  # Scroll up
                time.sleep(0.5)
                return True, "Scrolled up to look for element", False
            except Exception as e:
                logger.debug(f"Scroll failed: {e}")

        elif attempt == 3:
            # Third: Wait longer for element to appear (dynamic UI)
            time.sleep(1.5)
            return True, "Waited for element to appear", False

        return False, "Exploration exhausted", False

    def _execute_click_at_coords(self, x: float, y: float) -> Tuple[bool, str]:
        """Execute click at specific pixel coordinates (from vision executor)."""
        try:
            import pyautogui
            if self._browser_action:
                if not self._focus_chrome_window():
                    return False, "Could not focus Chrome window - ensure Chrome is running"
                time.sleep(0.2)
            click_x, click_y = x, y
            if self.state.active_window and self.state.active_window.get("app") == "chrome":
                click_x = self.state.active_window["left"] + x
                click_y = self.state.active_window["top"] + y
            pyautogui.click(click_x, click_y)
            time.sleep(0.5)  # Brief pause after click
            return True, f"Clicked at coordinates ({int(x)}, {int(y)})"
        except Exception as e:
            return False, f"Failed to click at ({int(x)}, {int(y)}): {e}"

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
                self._exploration_attempts = 0  # Reset on success
                return True, msg

            # Element not found - try exploration before giving up
            should_retry, explore_msg, _ = self._try_exploration(target_name, "click")
            if should_retry:
                # Retry after exploration
                success, msg = self.ui_controller.click_element(
                    name=target_name,
                    control_type=target_type,
                    timeout=2.0,
                )
                if success:
                    self._exploration_attempts = 0
                    return True, f"{msg} (after {explore_msg})"

            logger.info(f"UI automation click failed: {msg}, trying vision fallback")

        # Fall back to vision
        if self.vision_executor:
            if self._browser_action and self.state.active_window:
                bounds = self.state.active_window
                region = (bounds["left"], bounds["top"], bounds["width"], bounds["height"])
                self.vision_executor.take_screenshot_region("click_fallback", region)
            else:
                self.vision_executor.take_screenshot("click_fallback")
            analysis = self.vision_executor.analyze_screen(
                f"Click on '{target_name}'",
                f"Find and click the element named '{target_name}'"
            )
            if analysis.get("action") == "click" and analysis.get("target"):
                result = self.vision_executor.execute_action(analysis)
                if result[0]:
                    self._exploration_attempts = 0
                return result

        self._exploration_attempts = 0  # Reset for next action
        return False, f"Could not click '{target_name}' with UI automation or vision"

    def _execute_type(self, target_name: str, target_type: str, text: str) -> Tuple[bool, str]:
        """Type text into an element."""
        if self._browser_action:
            if not self._focus_chrome_window():
                return False, "Could not focus Chrome window - ensure Chrome is running"
            time.sleep(0.2)
        
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
            if self._browser_action:
                if not self._focus_chrome_window():
                    return False, "Could not focus Chrome window - ensure Chrome is running"
                time.sleep(0.2)
            pyautogui.press(key.lower())
            return True, f"Pressed {key}"
        except Exception as e:
            return False, f"Key press failed: {e}"

    def _focus_chrome_window(self) -> bool:
        """Bring Chrome to the foreground; launch if missing."""
        if not self.ui_controller:
            return False
        
        # Try to find Chrome window by title containing "Chrome"
        try:
            window = self.ui_controller.find_window(title_contains="Chrome")
            if window:
                # Restore if minimized, bring to foreground, set focus
                try:
                    if window._raw:
                        if hasattr(window._raw, "IsMinimized") and window._raw.IsMinimized:
                            if hasattr(window._raw, "Restore"):
                                window._raw.Restore()
                        if hasattr(window._raw, "SetFocus"):
                            window._raw.SetFocus()
                except Exception:
                    pass
                
                # Use focus_window method if available
                self.ui_controller.focus_window(window)
                
                # Get bounds for logging
                try:
                    bounds = self.ui_controller.get_chrome_window_bounds()
                    title = window.title or ""
                    logger.info(f"[FOCUS] Chrome focused: title={title}, rect=({bounds['left']},{bounds['top']},{bounds['width']},{bounds['height']})")
                    return True
                except Exception:
                    # Fallback: use window bounding box
                    left, top, right, bottom = window.bounding_box
                    width = right - left
                    height = bottom - top
                    title = window.title or ""
                    logger.info(f"[FOCUS] Chrome focused: title={title}, rect=({left},{top},{width},{height})")
                    return True
        except Exception:
            pass

        # Try get_chrome_window_bounds (which also handles restore/focus)
        try:
            bounds = self.ui_controller.get_chrome_window_bounds()
            title = ""
            try:
                window = self.ui_controller.get_active_window()
                title = window.title if window else ""
            except Exception:
                title = ""
            logger.info(f"[FOCUS] Chrome focused: title={title}, rect=({bounds['left']},{bounds['top']},{bounds['width']},{bounds['height']})")
            return True
        except Exception:
            pass

        # Launch Chrome if not found, then retry focus once
        try:
            import subprocess
            import shutil
            import os

            chrome_path = os.getenv("TREYS_AGENT_CHROME_PATH")
            if chrome_path and os.path.exists(chrome_path):
                subprocess.Popen([chrome_path, "about:blank"])
            else:
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    shutil.which("chrome"),
                ]
                chrome = next((p for p in chrome_paths if p and os.path.exists(p)), None)
                if chrome:
                    subprocess.Popen([chrome, "about:blank"])
                else:
                    return False
            
            # Wait for Chrome to launch, then retry focus
            time.sleep(2)
            
            # Retry finding Chrome window
            try:
                window = self.ui_controller.find_window(title_contains="Chrome")
                if window:
                    try:
                        if window._raw:
                            if hasattr(window._raw, "IsMinimized") and window._raw.IsMinimized:
                                if hasattr(window._raw, "Restore"):
                                    window._raw.Restore()
                            if hasattr(window._raw, "SetFocus"):
                                window._raw.SetFocus()
                    except Exception:
                        pass
                    self.ui_controller.focus_window(window)
                    bounds = self.ui_controller.get_chrome_window_bounds()
                    title = window.title or ""
                    logger.info(f"[FOCUS] Chrome focused: title={title}, rect=({bounds['left']},{bounds['top']},{bounds['width']},{bounds['height']})")
                    return True
            except Exception:
                pass
            
            # Fallback: try get_chrome_window_bounds after launch
            try:
                bounds = self.ui_controller.get_chrome_window_bounds()
                title = ""
                try:
                    window = self.ui_controller.get_active_window()
                    title = window.title if window else ""
                except Exception:
                    title = ""
                logger.info(f"[FOCUS] Chrome focused: title={title}, rect=({bounds['left']},{bounds['top']},{bounds['width']},{bounds['height']})")
                return True
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Failed to launch/focus Chrome: {e}")
        
        return False

    def prepare_and_navigate_chrome(self, url: str) -> Tuple[bool, str]:
        """
        Prepare Chrome for navigation and navigate to URL.
        
        Exact order:
        1) Focus Chrome window
        2) Maximize Chrome window
        3) Send Ctrl+L to focus address bar
        4) Copy URL to clipboard and paste (Ctrl+V)
        5) Append a single space to defeat autocomplete
        6) Press Enter
        7) Sleep 2.0s
        """
        import pyautogui
        
        # Step 1: Focus Chrome window
        if not self._focus_chrome_window():
            return False, "Could not focus Chrome window - ensure Chrome is running"
        
        # Step 2: Maximize Chrome window
        try:
            if self.ui_controller:
                window = self.ui_controller.find_window(title_contains="Chrome")
                if window and window._raw:
                    try:
                        if hasattr(window._raw, "Maximize"):
                            window._raw.Maximize()
                        elif hasattr(window._raw, "maximize"):
                            window._raw.maximize()
                    except Exception:
                        # Fallback: Win+Up hotkey
                        pyautogui.hotkey("win", "up")
                else:
                    # Fallback: Win+Up hotkey
                    pyautogui.hotkey("win", "up")
            else:
                # Fallback: Win+Up hotkey
                pyautogui.hotkey("win", "up")
        except Exception:
            # Fallback: Win+Up hotkey
            try:
                pyautogui.hotkey("win", "up")
            except Exception:
                pass
        time.sleep(0.2)
        
        # Step 3: Send Ctrl+L to focus address bar
        logger.info(f"[NAV] Navigating Chrome to: {url}")
        pyautogui.hotkey("ctrl", "l")
        time.sleep(0.1)
        
        # Step 4: Copy URL to clipboard and paste
        try:
            import pyperclip
            pyperclip.copy(url)
        except ImportError:
            # Fallback: if pyperclip not available, type the URL
            pyautogui.write(url, interval=0.05)
        else:
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.1)
        
        # Step 5: Append a single space to defeat autocomplete
        pyautogui.write(" ", interval=0.01)
        time.sleep(0.1)
        
        # Step 6: Press Enter
        pyautogui.press("enter")
        
        # Step 7: Sleep 2.0s
        time.sleep(2.0)
        
        logger.info("[NAV] Address bar paste complete; submitted")
        return True, f"Navigated to: {url}"

    def _update_agent_state(self, action: Dict[str, Any], success: bool, message: str) -> None:
        """Update the unified agent state for ThrashGuard tracking."""
        if not GUARDS_AVAILABLE or not self._agent_state:
            return

        try:
            # Import Observation from models if we need to create one
            from .models import Observation as ObsModel

            # Create observation
            observation = ObsModel(
                raw=message,
                source="hybrid_executor",
                errors=[message] if not success else [],
                success=success,
            )

            # Record step using the correct API
            self._agent_state.record_step(
                action=action.get("action", "unknown"),
                action_input=action,
                reasoning=action.get("reasoning", ""),
                observation=observation,
            )
        except Exception as e:
            logger.debug(f"Could not update agent state: {e}")

    def _check_stuck_loop(self) -> Tuple[bool, str]:
        """
        Check if we're stuck in a loop using ThrashGuard (Gap #9).

        Returns: (is_stuck, message)
        """
        if not self._thrash_guard or not self._agent_state:
            return False, ""

        try:
            detection = self._thrash_guard.check(self._agent_state)
            if detection.detected:
                action, message = self._thrash_guard.get_escalation(detection)
                suggestion = self._thrash_guard.get_recovery_suggestion(detection)

                if action in (EscalationAction.STOP, EscalationAction.ASK_USER):
                    return True, f"{detection.details}. {suggestion}"

                # Log warning but continue for less severe cases
                logger.warning(f"Thrash detected: {detection.details}")

            return False, ""
        except Exception as e:
            logger.debug(f"Thrash check failed: {e}")
            return False, ""

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
        5. STOPS on failures and reflects before retrying
        6. Queries past reflexions to avoid repeating mistakes
        7. Detects stuck loops and escalates early (Gap #9)
        8. Checks preconditions before actions (Gap #4)
        """
        if not self._initialized:
            ok, err = self.initialize()
            if not ok:
                return {"success": False, "summary": err, "steps_taken": 0}

        # Initialize agent state for ThrashGuard tracking
        if GUARDS_AVAILABLE:
            try:
                self._agent_state = UnifiedAgentState(goal=objective)
            except Exception as e:
                logger.debug(f"Could not initialize agent state: {e}")
                self._agent_state = None

        # LEARN FROM THE PAST: Query reflexion memory for relevant lessons
        past_lessons = self._get_relevant_reflexions(objective)
        if past_lessons:
            context = f"{context}\n\nLESSONS FROM PAST ATTEMPTS:\n{past_lessons}"
            logger.info(f"Found relevant past lessons for: {objective[:50]}...")

        self.action_history = []
        steps_taken = 0
        consecutive_failures = 0  # Track failures for early stopping

        while steps_taken < self.max_steps:
            steps_taken += 1

            # ============================================================
            # CHECK FOR STUCK LOOP (Gap #9)
            # Early detection prevents wasted cycles
            # ============================================================
            is_stuck, stuck_msg = self._check_stuck_loop()
            if is_stuck:
                logger.warning(f"Stuck loop detected: {stuck_msg}")
                # Ask user for help before giving up
                if on_user_input:
                    user_help = on_user_input(
                        f"I'm stuck in a loop: {stuck_msg}\nWhat should I try instead?"
                    )
                    if user_help:
                        context = f"{context}\n\nSTUCK LOOP RECOVERY - User guidance: {user_help}"
                        # Reset state tracking
                        if self._agent_state:
                            self._agent_state = UnifiedAgentState(goal=objective)
                        consecutive_failures = 0
                        continue  # Try again with user guidance
                # No user help - stop with failure
                return {
                    "success": False,
                    "summary": f"Stuck in loop: {stuck_msg}",
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                    "stuck_loop": True,
                }

            # Decide next action (uses UI state text, not vision)
            screenshot_path = None
            if self.vision_executor:
                try:
                    state = self.vision_executor.take_screenshot("ui_state")
                    screenshot_path = str(state.screenshot_path)
                    logger.info(f"Captured UI screenshot: {screenshot_path}")
                except Exception as e:
                    return {
                        "success": False,
                        "summary": f"Failed to take UI screenshot: {e}",
                        "steps_taken": steps_taken,
                        "actions": self.action_history,
                    }
            action = self.decide_next_action(objective, context, screenshot_path=screenshot_path)

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
                self._update_agent_state(action, True, "Task completed")
                return {
                    "success": True,
                    "summary": action.get("reasoning", "Task completed"),
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                }

            # Handle error
            if action_type == "error":
                self._update_agent_state(action, False, action.get("reasoning", "Error"))
                return {
                    "success": False,
                    "summary": action.get("reasoning", "Error occurred"),
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                }

            # Handle ask_user (vision fallback or clarification)
            if action_type == "ask_user":
                question = action.get("value") or action.get("reasoning") or "Need user input"
                if on_user_input:
                    user_help = on_user_input(question)
                    self.action_history[-1]["result"] = "User input received"
                    self._update_agent_state(action, True, "User input received")
                    if user_help:
                        context = f"{context}\n\nUSER INPUT: {user_help}"
                        consecutive_failures = 0
                        continue
                    return {
                        "success": False,
                        "summary": "User did not provide input",
                        "steps_taken": steps_taken,
                        "actions": self.action_history,
                    }
                return {
                    "success": False,
                    "summary": f"Need user input: {question}",
                    "steps_taken": steps_taken,
                    "actions": self.action_history,
                }

            # ============================================================
            # PRECONDITION CHECK (Gap #4)
            # Verify action can succeed before attempting
            # ============================================================
            precond_ok, precond_msg = self._check_precondition(action)
            if not precond_ok:
                logger.warning(f"Precondition failed: {precond_msg}")
                self.action_history[-1]["result"] = f"Precondition failed: {precond_msg}"
                self.action_history[-1]["error"] = precond_msg
                self._update_agent_state(action, False, precond_msg)
                consecutive_failures += 1

                # Quick stop if 3 consecutive precondition failures
                if consecutive_failures >= 3:
                    return {
                        "success": False,
                        "summary": f"Multiple precondition failures: {precond_msg}",
                        "steps_taken": steps_taken,
                        "actions": self.action_history,
                    }
                continue

            # Execute action
            success, message = self.execute_action(action)
            self.action_history[-1]["result"] = message

            # ============================================================
            # POSTCONDITION CHECK (Gap #4)
            # Verify action had intended effect
            # ============================================================
            success, message = self._verify_postcondition(action, (success, message))

            # Update agent state for ThrashGuard tracking
            self._update_agent_state(action, success, message)

            if not success:
                consecutive_failures += 1
                # ============================================================
                # STOP - THINK - REPLAN pattern
                # Don't just continue blindly - reflect and learn!
                # ============================================================
                logger.warning(f"Step {steps_taken} failed: {message}")

                # STOP: Log the failure
                self.action_history[-1]["error"] = message

                # Check if we should stop early (too many consecutive failures)
                if consecutive_failures >= 4:
                    logger.error(f"Too many consecutive failures ({consecutive_failures})")
                    return {
                        "success": False,
                        "summary": f"Too many consecutive failures. Last error: {message}",
                        "steps_taken": steps_taken,
                        "actions": self.action_history,
                        "consecutive_failures": consecutive_failures,
                    }

                # THINK: Reflect on why it failed
                reflection = self._reflect_on_failure(
                    objective=objective,
                    action=action,
                    error=message,
                    context=context,
                )

                # LEARN: Save to reflexion memory
                self._save_reflexion(objective, action, message, reflection)

                # REPLAN: Get new approach from LLM
                new_approach = self._replan_after_failure(
                    objective=objective,
                    failed_action=action,
                    error=message,
                    reflection=reflection,
                    context=context,
                )

                if new_approach:
                    # Update context with reflection and new plan
                    context = f"{context}\n\nFAILURE ANALYSIS:\n{reflection}\n\nNEW APPROACH:\n{new_approach}"
                    logger.info(f"Replanning after failure: {new_approach[:100]}...")
                else:
                    # If we can't replan, ask user for help (if callback available)
                    if on_user_input:
                        user_help = on_user_input(
                            f"I tried to {action.get('reasoning', 'do something')} but it failed: {message}\n"
                            f"What should I try instead?"
                        )
                        if user_help:
                            context = f"{context}\nUser guidance: {user_help}"
                            consecutive_failures = 0  # Reset on user help
                    else:
                        # No replan possible and no user help - stop with failure
                        return {
                            "success": False,
                            "summary": f"Failed and could not recover: {message}",
                            "steps_taken": steps_taken,
                            "actions": self.action_history,
                            "last_error": message,
                            "reflection": reflection,
                        }
            else:
                # Success - reset consecutive failure counter
                consecutive_failures = 0

            # Small delay between actions
            time.sleep(0.3)

        return {
            "success": False,
            "summary": f"Max steps ({self.max_steps}) reached",
            "steps_taken": steps_taken,
            "actions": self.action_history,
        }

    def _reflect_on_failure(
        self,
        objective: str,
        action: Dict[str, Any],
        error: str,
        context: str,
    ) -> str:
        """
        THINK step: Analyze why an action failed using Reflector.

        This is crucial for learning - we need to understand the failure
        to avoid repeating it and to inform the replan.
        """
        # Use Reflector if available
        if self.reflector:
            try:
                from agent.autonomous.models import Step, ToolResult, Observation

                # Create Step from action
                step = Step(
                    action=action.get('action', 'unknown'),
                    action_input=action,
                    reasoning=action.get('reasoning', ''),
                    tool_name=action.get('action', 'unknown'),
                    tool_args=[]
                )

                # Create ToolResult for failure
                tool_result = ToolResult(
                    success=False,
                    error=error,
                    metadata={"context": context[:500]}
                )

                # Create Observation
                observation = Observation(
                    raw=error,
                    source="hybrid_executor",
                    errors=[error],
                    success=False
                )

                # Use Reflector to analyze
                reflection = self.reflector.reflect(
                    task=objective,
                    step=step,
                    tool_result=tool_result,
                    observation=observation
                )

                # Build response from reflection
                response = f"Status: {reflection.status}\n"
                response += f"Explanation: {reflection.explanation_short}\n"
                if reflection.next_hint:
                    response += f"Next Hint: {reflection.next_hint}\n"
                if reflection.lesson:
                    response += f"Lesson: {reflection.lesson}\n"

                return response

            except Exception as e:
                logger.debug(f"Reflector failed, falling back to manual reflection: {e}")

        # Fallback: Manual reflection if Reflector unavailable
        prompt = f"""An action failed during task execution. Analyze WHY it failed.

OBJECTIVE: {objective}

ATTEMPTED ACTION:
- Type: {action.get('action')}
- Target: {action.get('target_name', 'N/A')}
- Value: {action.get('value', 'N/A')}
- Reasoning: {action.get('reasoning', 'N/A')}

ERROR: {error}

CONTEXT: {context[:500]}

Analyze the failure and respond with:
1. ROOT CAUSE: Why did this specific action fail?
2. LESSON: What should be remembered to avoid this in the future?
3. SUGGESTION: What alternative approach might work?

Be specific and actionable. Keep response under 200 words."""

        response = self._call_llm(prompt, timeout=15)
        if response:
            return response
        return f"Action '{action.get('action')}' failed with error: {error}"

    def _replan_after_failure(
        self,
        objective: str,
        failed_action: Dict[str, Any],
        error: str,
        reflection: str,
        context: str,
    ) -> Optional[str]:
        """
        REPLAN step: Generate a new approach after failure.

        Uses the reflection to inform a better strategy.
        """
        prompt = f"""A task action failed. Create a NEW approach to achieve the objective.

OBJECTIVE: {objective}

WHAT FAILED:
- Action: {failed_action.get('action')} on '{failed_action.get('target_name', 'unknown')}'
- Error: {error}

ANALYSIS OF FAILURE:
{reflection}

CONTEXT: {context[:300]}

Based on this failure, suggest a DIFFERENT approach. Consider:
1. Is there another way to achieve the same goal?
2. Is there a prerequisite step we missed?
3. Should we try a different element or method?

Respond with a brief (1-2 sentence) new approach to try, or "CANNOT_REPLAN" if stuck."""

        response = self._call_llm(prompt, timeout=15)
        if response and "CANNOT_REPLAN" not in response.upper():
            return response.strip()
        return None

    def _save_reflexion(
        self,
        objective: str,
        action: Dict[str, Any],
        error: str,
        reflection: str,
    ) -> None:
        """
        LEARN step: Save the failure to reflexion memory.

        This allows the agent to learn from past mistakes and
        retrieve relevant lessons for future similar tasks.
        """
        try:
            from agent.autonomous.memory.reflexion import ReflexionEntry, write_reflexion
            from uuid import uuid4
            from datetime import datetime, timezone

            entry = ReflexionEntry(
                id=f"hybrid_{uuid4().hex[:8]}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                objective=objective,
                context_fingerprint=f"ui_action_{action.get('action', 'unknown')}",
                phase="execution",
                tool_calls=[{
                    "action": action.get("action"),
                    "target": action.get("target_name"),
                    "value": action.get("value"),
                }],
                errors=[error],
                reflection=reflection,
                fix=f"Try alternative approach for: {action.get('reasoning', objective)[:100]}",
                outcome="failure",
                tags=["hybrid_executor", action.get("action", "unknown")],
            )
            write_reflexion(entry)
            logger.info(f"Saved reflexion entry: {entry.id}")
        except Exception as e:
            logger.warning(f"Could not save reflexion: {e}")

    def _get_relevant_reflexions(self, objective: str) -> Optional[str]:
        """
        Query past reflexions for lessons relevant to the current objective.

        This is the key to learning - we retrieve past failures and their
        lessons so the agent doesn't repeat the same mistakes.
        """
        try:
            from agent.autonomous.memory.reflexion import retrieve_reflexions

            # Get up to 3 most relevant past lessons
            entries = retrieve_reflexions(objective, error_signature=None, k=3)

            if not entries:
                return None

            lessons = []
            for entry in entries:
                lesson = f"- When trying '{entry.objective[:50]}...': {entry.reflection[:150]}"
                if entry.fix:
                    lesson += f" FIX: {entry.fix[:100]}"
                lessons.append(lesson)

            return "\n".join(lessons)

        except Exception as e:
            logger.debug(f"Could not retrieve reflexions: {e}")
            return None


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
