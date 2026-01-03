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
import re
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Literal

from pydantic import BaseModel, Field

from agent.llm.json_enforcer import enforce_json_response

logger = logging.getLogger(__name__)

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = REPO_ROOT / "agent" / "screenshots"
EVIDENCE_DIR = REPO_ROOT / "evidence"

try:
    from pydantic import ConfigDict
except Exception:  # pragma: no cover - pydantic v1 fallback
    ConfigDict = None


class PixelTarget(BaseModel):
    x: float
    y: float

    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class TextTarget(BaseModel):
    text: str

    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class BoundingBox(BaseModel):
    left: float
    top: float
    right: float
    bottom: float
    confidence: Optional[float] = None

    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


class VisionActionModel(BaseModel):
    observation: str
    reasoning: str
    action: Literal["click", "type", "scroll", "press", "goto", "wait", "done", "ask_user", "error"]
    target: Optional[Union[PixelTarget, TextTarget]] = None
    bbox: Optional[BoundingBox] = None
    value: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)

    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:
        class Config:
            extra = "forbid"


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
        self._ocr_cache: Optional[Dict[str, Any]] = None  # Cache OCR results per screenshot
        self.successful_patterns: List[Dict[str, Any]] = []  # Store successful coordinate patterns

        # Retry and offset configuration (can be tuned or overridden in tests)
        # Offsets tried in pixels (ordered by priority)
        self.retry_offsets: List[Tuple[int, int]] = [
            (0, -5), (0, 5), (-5, 0), (5, 0),  # up, down, left, right
            (-3, -3), (3, 3), (-3, 3), (3, -3),  # diagonals
            (0, -10), (0, 10), (-10, 0), (10, 0),  # further offsets
        ]
        # Maximum number of nearby attempts (not counting the initial click)
        self.retry_budget: int = int(os.getenv("TREYS_AGENT_UI_CLICK_RETRY_BUDGET", "8"))

        # Pattern persistence path (can be overridden for tests)
        self.patterns_path: Path = EVIDENCE_DIR / "successful_patterns.json"
        # Load persisted patterns
        try:
            self._load_successful_patterns()
        except Exception as e:
            logger.debug(f"Failed to load patterns at init: {e}")

        # Multi-tier model strategy for speed
        self.consecutive_failures = 0  # Track when to escalate to reasoning
        self.use_reasoning = False  # Whether to use deep reasoning model
        self._coordinate_origin: Tuple[int, int] = (0, 0)

    def initialize(self) -> Tuple[bool, str]:
        """Initialize the executor."""
        pyautogui, err = _import_pyautogui()
        if not pyautogui:
            return False, err
        self.pyautogui = pyautogui

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        return True, "Initialized"

    def _validate_action_data(
        self,
        data: Dict[str, Any],
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            if hasattr(VisionActionModel, "model_validate"):
                model = VisionActionModel.model_validate(data)  # type: ignore[attr-defined]
                return model.model_dump(), None  # type: ignore[attr-defined]
            model = VisionActionModel.parse_obj(data)  # type: ignore[attr-defined]
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
            "observation": message,
            "reasoning": message,
            "action": "error",
            "value": parse_error or message,
            "confidence": 0.0,
            "tool_result": tool_payload,
        }

    def _log_llm_use(self, llm: Any, purpose: str) -> None:
        provider = getattr(llm, "provider", getattr(llm, "provider_name", "unknown"))
        model = getattr(llm, "model", None) or "default"
        logger.info(f"[LLM] {purpose}: provider={provider} model={model}")

    def take_screenshot(self, name: str = "screen") -> ScreenState:
        """Take a screenshot of the current screen."""
        if not self.pyautogui:
            self.initialize()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = SCREENSHOTS_DIR / f"{name}_{ts}.png"

        img = self.pyautogui.screenshot()
        img.save(path)

        self.current_state = ScreenState(path, ts)
        self._coordinate_origin = (0, 0)
        # Clear OCR cache when screenshot changes
        self._ocr_cache = None
        return self.current_state

    def take_screenshot_region(
        self,
        name: str,
        region: Tuple[int, int, int, int],
    ) -> ScreenState:
        """Take a screenshot of a specific region (left, top, width, height)."""
        if not self.pyautogui:
            self.initialize()

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = SCREENSHOTS_DIR / f"{name}_{ts}.png"

        img = self.pyautogui.screenshot(region=region)
        img.save(path)

        self.current_state = ScreenState(path, ts)
        self._coordinate_origin = (region[0], region[1])
        # Clear OCR cache when screenshot changes
        self._ocr_cache = None
        return self.current_state

    def _to_screen_coords(self, x: float, y: float) -> Tuple[int, int]:
        origin_x, origin_y = self._coordinate_origin
        return int(x + origin_x), int(y + origin_y)

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
            response = self._call_vision_llm(prompt, self.current_state)
            if response is None:
                return self._action_error("Vision LLM returned no response")
            return self._parse_vision_response(response, self.current_state)
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return self._action_error("Vision analysis failed", parse_error=str(e))

    def _build_vision_prompt(self, objective: str, context: str) -> str:
        """Build the prompt for vision analysis."""
        history_text = ""
        if self.action_history:
            recent = self.action_history[-5:]  # Last 5 actions
            history_text = "Recent actions:\n" + "\n".join(
                f"- {a['action']}: {a.get('description', '')}" for a in recent
            )

        screen_width = self.current_state.width if self.current_state else 1920
        screen_height = self.current_state.height if self.current_state else 1080

        schema_text = (
            "Respond ONLY with a JSON object matching this schema (example):\n"
            "{\n"
            "  \"observation\": \"string\",\n"
            "  \"reasoning\": \"string\",\n"
            "  \"action\": \"click|type|scroll|press|goto|wait|done|ask_user|error\",\n"
            "  \"target\": {\"x\": <number>, \"y\": <number>} (or null),\n"
            "  \"bbox\": { \"left\": <number>, \"top\": <number>, \"right\": <number>, \"bottom\": <number> } (optional),\n"
            "  \"value\": <string|null>,\n"
            "  \"confidence\": <0.0-1.0>\n"
            "}\n\n"
            "If you are uncertain, include the optional 'bbox' object and show calculation steps."
        )

        return f"""You are a desktop automation agent. Analyze this screenshot and decide the next action.

OBJECTIVE: {objective}

{f"CONTEXT: {context}" if context else ""}

{history_text}

Screen size: {screen_width}x{screen_height}

{schema_text}

STEP 1: OBSERVE
Look at the screenshot carefully. Identify:
- What UI elements are visible?
- Where is the element you need to interact with?
- What is its approximate position (top/middle/bottom, left/center/right)?

STEP 2: ESTIMATE COORDINATES (CRITICAL FOR ACCURACY)
To find precise coordinates, use this systematic approach:

1. VISUAL GRID METHOD:
   - Divide screen into a 10x10 grid mentally
   - Each grid cell is {screen_width//10}px wide x {screen_height//10}px tall
   - Identify which grid cell(s) contain your target element
   - Example: If element is in column 3 (0-indexed), x ≈ 3 * {screen_width//10} = {3*screen_width//10}
   - Example: If element is in row 2 (0-indexed), y ≈ 2 * {screen_height//10} = {2*screen_height//3}

2. BOUNDING BOX METHOD (MORE ACCURATE):
   - First, estimate the element's bounding box: [left, top, right, bottom]
   - Visualize where the element starts and ends
   - Calculate CENTER: x = (left + right) / 2, y = (top + bottom) / 2
   - When possible, include the bounding box in your "reasoning" field in this exact format: [left, top, right, bottom]
   - Show your calculation steps (e.g., left=100, right=200 -> x=(100+200)/2 = 150)
   - If you are unsure (confidence < 0.6), emphasize the bounding box in your reasoning and explicitly note you are uncertain; the system may use the bounding box to compute the click center instead of your point estimate
   - If uncertain, ALSO include a small JSON object in your response (either in reasoning or at the end) with the bounding box and confidence so the executor can use it directly. Example (literal JSON shown):
     {{"bbox": {{"left": 100, "top": 50, "right": 200, "bottom": 80}}, "center": {{"x": 150, "y": 65}}, "confidence": 0.65}}
   - Allowed formats: either top-level keys {{"left", "top", "right", "bottom"}} or nested under "bbox" as shown above; the executor will parse either form.
   - This is more accurate than guessing a single point

3. REFERENCE POINTS:
   - Top-left corner: (0, 0)
   - Center of screen: ({screen_width//2}, {screen_height//2})
   - Bottom-right: ({screen_width}, {screen_height})
   - Use these as anchors to estimate relative positions

4. SHOW YOUR WORK:
   - In "reasoning", explain: "Element appears at [left, top, right, bottom], center is (x, y)"
   - Include your calculation steps
   - This helps verify accuracy

STEP 3: VALIDATE & CALIBRATE CONFIDENCE
Before responding, verify:
- Coordinates within bounds? (0-{screen_width}, 0-{screen_height})
- Clicking the CENTER of the element, not the edge?
- Element is clearly visible and identifiable?

CONFIDENCE CALIBRATION (be honest):
- 0.9-1.0: Element is large, clearly visible, unambiguous (e.g., large button in center)
- 0.7-0.9: Element is visible but may be small or near similar elements
- 0.5-0.7: Element is partially visible, obscured, or you're estimating from context
- 0.3-0.5: Element is hard to see, very small, or you're making educated guesses
- <0.3: You're not confident - consider using "ask_user" or "wait" to get better view

IMPORTANT: Lower confidence is OK - just be accurate about it. The system will handle low confidence appropriately.

STEP 4: RESPOND

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
- goto: Open URL in browser (value: the URL - use this when you need to navigate to a different page)
- wait: Wait for something to load (value: seconds as string)
- done: Task is complete (value: summary of what was accomplished)
- ask_user: ONLY use if truly stuck after multiple attempts (value: question to ask)
- error: ONLY use for unexpected failures (value: error description)

CRITICAL RULES:
1. For click actions, you MUST provide exact x,y pixel coordinates - NOT text descriptions
2. Estimate coordinates by looking at where elements are in the image
3. The origin (0,0) is the top-left corner of the screen
4. Look carefully at the screenshot to identify where to click
5. For buttons/links, aim for the CENTER of the element
6. If you're on the wrong page, use "goto" action to navigate to the correct URL
7. For Google Cloud Console tasks:
   - APIs & Services: https://console.cloud.google.com/apis/library
   - OAuth consent: https://console.cloud.google.com/apis/credentials/consent
   - Credentials: https://console.cloud.google.com/apis/credentials
8. NEVER use "ask_user" or "error" unless you've tried multiple approaches
9. If the objective is complete or you see what you need, use "done" action

EXAMPLES WITH CALCULATIONS:

Example 1: Button in center of screen
- Observation: "I see a blue 'Submit' button in the center of the page"
- Reasoning: "Button appears in center region. Screen is {screen_width}x{screen_height}, so center is approximately ({screen_width//2}, {screen_height//2}). Button bounding box estimated as [{screen_width//2-50}, {screen_height//2-15}, {screen_width//2+50}, {screen_height//2+15}]. Center: ({screen_width//2}, {screen_height//2})"
- Target: {{"x": {screen_width//2}, "y": {screen_height//2}}}
- Confidence: 0.85

Example 2: Left sidebar menu
- Observation: "Left sidebar has menu items, I need to click 'Settings'"
- Reasoning: "Sidebar is typically 200px wide. Menu item 'Settings' appears to be 3rd item down. Each item is ~40px tall. Top of sidebar is ~100px from top. So: left = 100 (center of 200px sidebar), top = 100 + (3 * 40) = 220, bottom = 220 + 40 = 260. Center: (100, 240)"
- Target: {{"x": 100, "y": 240}}
- Confidence: 0.75

Example 3: Top navigation bar
- Observation: "Search bar at top of page"
- Reasoning: "Search bar is typically centered horizontally. Screen width {screen_width}, so center x ≈ {screen_width//2}. Top navigation is typically 50-80px from top, so y ≈ 65. Search bar bounding box: [{screen_width//2-200}, 50, {screen_width//2+200}, 80]. Center: ({screen_width//2}, 65)"
- Target: {{"x": {screen_width//2}, "y": 65}}
- Confidence: 0.9

NAVIGATION EXAMPLES:
- Wrong page? Use goto: {{"action": "goto", "value": "https://console.cloud.google.com/apis/library", "target": null, "confidence": 1.0}}
- Need to click address bar? Estimate: {{"action": "click", "target": {{"x": {screen_width//2}, "y": 35}}, "confidence": 0.8}}
"""

    # Preferred model hints to improve behavior on different providers
    MODEL_PREFERRED = {
        "openai": ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"],
        "openrouter": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o"],
    }

    # Small prompt adjustments per provider/model
    MODEL_PROMPT_HINTS = {
        "openai": "Be concise and return JSON bounding boxes when uncertain; include calculation steps.",
        "openrouter": "Prefer brief JSON responses with bounding box details when unsure.",
    }

    def _select_vision_model(self) -> Optional[str]:
        """Select the best vision-capable model for the configured LLM provider.

        Priority order per provider is defined in MODEL_PREFERRED. An environment override
        `TREYS_AGENT_VISION_MODEL` can force a particular model.
        """
        env_override = os.getenv("TREYS_AGENT_VISION_MODEL")
        if env_override:
            return env_override

        if not self.llm or not hasattr(self.llm, "provider_name"):
            return None

        provider = self.llm.provider_name
        prefs = self.MODEL_PREFERRED.get(provider, [])
        # Return first available preference
        return prefs[0] if prefs else None

    def _call_vision_llm(self, prompt: str, state: ScreenState) -> Optional[str]:
        """Call the LLM with the screenshot for analysis.

        Behavior:
        - Prefer vision-capable models using `_select_vision_model`
        - Use lower temperature for coordinate tasks (0.1-0.2) and slightly higher for reasoning
        - Add small, provider-specific prompt hints to improve JSON/bbox output
        """
        if self.llm and hasattr(self.llm, "chat_with_image"):
            self._log_llm_use(self.llm, "vision_action")

            # Use lower temperature for better coordinate accuracy
            temperature = 0.15 if not self.use_reasoning else 0.25

            # Select preferred model if available
            model = self._select_vision_model()

            # Apply provider-specific prompt hints (non-intrusive)
            hint = None
            try:
                provider = self.llm.provider_name
                hint = self.MODEL_PROMPT_HINTS.get(provider)
            except Exception:
                hint = None

            prompt_with_hint = f"{prompt}\n\n{hint}" if hint else prompt

            try:
                return self.llm.chat_with_image(
                    prompt_with_hint,
                    state.screenshot_path,
                    temperature=temperature,
                    timeout=90,  # Vision tasks take longer
                    model=model,
                )
            except Exception as e:
                logger.warning(f"Vision API call failed, trying without model override: {e}")
                # Fallback: try without model specification
                return self.llm.chat_with_image(
                    prompt_with_hint,
                    state.screenshot_path,
                    temperature=temperature,
                    timeout=90,
                )

        try:
            return self._call_codex_vision(prompt, state)
        except Exception as e:
            logger.error(f"Codex vision call failed: {e}")
            return None

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

        timeout = 90  # Vision takes longer

        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            raise RuntimeError(f"Codex failed: {result.stderr[:500]}")

        return result.stdout

    def _parse_vision_response(self, response: str, state: ScreenState) -> Dict[str, Any]:
        """Parse the LLM response into an action dict with schema enforcement and repair."""
        data, error = enforce_json_response(
            response,
            model_cls=VisionActionModel,
            retry_call=lambda prompt: self._call_vision_llm(prompt, state),
            max_retries=2,
        )
        if data:
            # If the model returned a bounding box but not a target point, compute the center
            try:
                if isinstance(data, dict) and "bbox" in data and not data.get("target"):
                    bb = data.get("bbox") or {}
                    left = float(bb.get("left"))
                    top = float(bb.get("top"))
                    right = float(bb.get("right"))
                    bottom = float(bb.get("bottom"))
                    cx = (left + right) / 2.0
                    cy = (top + bottom) / 2.0
                    data["target"] = {"x": cx, "y": cy}
                    # Promote bbox confidence if present
                    bb_conf = bb.get("confidence")
                    if bb_conf is not None and (data.get("confidence") is None or float(data.get("confidence")) < float(bb_conf)):
                        data["confidence"] = float(bb_conf)
            except Exception as e:
                logger.debug(f"Failed to convert bbox to target: {e}")

            validated, validation_error = self._validate_action_data(data)
            if validated:
                return validated
            return self._action_error(
                "Vision response failed schema validation",
                raw_response=json.dumps(data),
                parse_error=validation_error,
            )
        logger.warning(f"Failed to parse vision response after repair: {error}")
        return self._action_error(
            "Invalid JSON from vision model after repair attempts",
            raw_response=response,
            parse_error=error,
        )

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
                confidence = float(action.get("confidence", 1.0) or 1.0)
                # Try to extract expected text from reasoning or observation
                expected_text = None
                reasoning = action.get("reasoning", "")
                observation = action.get("observation", "")
                # Look for quoted text or button names in reasoning
                text_matches = re.findall(r'["\']([^"\']+)["\']', reasoning + " " + observation)
                if text_matches:
                    expected_text = text_matches[0]  # Use first quoted text
                return self._do_click(target, confidence, expected_text)

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

    def _validate_coordinates(self, x: float, y: float) -> Tuple[bool, Optional[str]]:
        """Validate coordinates are within screen bounds and reasonable.
        
        Returns:
            (is_valid, error_message)
        """
        if not self.current_state:
            return True, None  # Can't validate without screen state
        
        screen_width = self.current_state.width
        screen_height = self.current_state.height
        
        # Check bounds
        if x < 0 or y < 0:
            return False, f"Coordinates ({x}, {y}) are negative - must be positive"
        
        if x >= screen_width or y >= screen_height:
            return False, f"Coordinates ({x}, {y}) exceed screen bounds ({screen_width}x{screen_height})"
        
        # Warn if coordinates are very close to edges (might be inaccurate)
        margin = 10
        if x < margin or y < margin or x > screen_width - margin or y > screen_height - margin:
            logger.warning(f"Coordinates ({x}, {y}) are near screen edge - may be inaccurate")
        
        return True, None

    def _request_bounding_box(self, x: float, y: float, confidence: float) -> Optional[Dict[str, Any]]:
        """Ask the vision LLM for a bounding box around an element near (x,y).

        Returns:
            dict with keys 'left','top','right','bottom','confidence' or None on failure
        """
        if not self.llm or not hasattr(self.llm, "chat_with_image") or not self.current_state:
            return None

        prompt = (
            f"You previously suggested clicking near ({x},{y}) with confidence {confidence:.2f}.\n"
            "Please analyze the screenshot and return a JSON object with a bounding box."
            " Prefer format: {\"bbox\": {\"left\": <int>, \"top\": <int>, \"right\": <int>, \"bottom\": <int>}, \"confidence\": <0.0-1.0>}"
            " You may also return the bounding box as top-level keys {\"left\", \"top\", \"right\", \"bottom\"}."
            " Return ONLY the JSON object."
        )

        try:
            resp = self._call_vision_llm(prompt, self.current_state)
            if not resp:
                return None
            import re, json
            m = re.search(r"\{[\s\S]*\}", resp)
            if not m:
                return None
            obj = json.loads(m.group())

            # Support nested 'bbox' or top-level bbox keys
            if "bbox" in obj and isinstance(obj["bbox"], dict):
                bb = obj["bbox"]
                if all(k in bb for k in ("left", "top", "right", "bottom")):
                    return {
                        "left": float(bb["left"]),
                        "top": float(bb["top"]),
                        "right": float(bb["right"]),
                        "bottom": float(bb["bottom"]),
                        "confidence": float(obj.get("confidence") or bb.get("confidence") or 0.0),
                    }

            if all(k in obj for k in ("left", "top", "right", "bottom")):
                return {
                    "left": float(obj["left"]),
                    "top": float(obj["top"]),
                    "right": float(obj["right"]),
                    "bottom": float(obj["bottom"]),
                    "confidence": float(obj.get("confidence") or 0.0),
                }
        except Exception as e:
            logger.debug(f"Bounding box request failed: {e}")
        return None
    def _refine_coordinates(self, x: float, y: float, confidence: float) -> Tuple[float, float]:
        """Refine coordinates based on confidence and screen state.

        If confidence is low, try to request a bounding box from the vision LLM and use its center.
        """
        # If confidence is low, try to ask LLM for a bounding box
        if confidence < 0.6:
            bbox = self._request_bounding_box(x, y, confidence)
            if bbox:
                try:
                    left = float(bbox["left"])
                    top = float(bbox["top"])
                    right = float(bbox["right"])
                    bottom = float(bbox["bottom"])
                    cx = round((left + right) / 2)
                    cy = round((top + bottom) / 2)
                    logger.info(f"Refined coordinates using bounding box: ({cx},{cy}) from bbox {bbox}")
                    return float(cx), float(cy)
                except Exception:
                    logger.debug("Failed to parse bounding box from vision LLM")

        # Default behavior: round to integers
        x = round(x)
        y = round(y)
        return float(x), float(y)

    def _do_click(self, target: Any, confidence: float = 1.0, expected_text: Optional[str] = None) -> Tuple[bool, str]:
        """Execute a click action with validation, refinement, and OCR verification."""
        if isinstance(target, dict):
            if "x" in target and "y" in target:
                x, y = float(target["x"]), float(target["y"])
                
                # If confidence is low and we have expected text, try OCR first
                if confidence < 0.6 and expected_text:
                    ocr_coords = self._find_text_with_ocr(expected_text)
                    if ocr_coords:
                        ocr_x, ocr_y = ocr_coords
                        # Check distance between vision and OCR coordinates
                        distance = ((ocr_x - x) ** 2 + (ocr_y - y) ** 2) ** 0.5
                        if distance > 30:  # More than 30px difference
                            logger.info(f"OCR found '{expected_text}' at ({ocr_x}, {ocr_y}), vision said ({x}, {y}), using OCR")
                            x, y = float(ocr_x), float(ocr_y)
                            confidence = 0.8  # Boost confidence when OCR confirms
                
                # Refine coordinates
                x, y = self._refine_coordinates(x, y, confidence)
                
                # Validate coordinates
                is_valid, error_msg = self._validate_coordinates(x, y)
                if not is_valid:
                    return False, error_msg or f"Invalid coordinates ({x}, {y})"
                
                # Optional: Verify with OCR if expected text provided
                if expected_text and confidence < 0.8:
                    verified, verify_msg = self._verify_coordinates_with_ocr(x, y, expected_text)
                    if not verified:
                        logger.warning(f"OCR verification failed: {verify_msg}")
                        # Don't fail, but log warning
                
                # Convert to integers for clicking
                x_int, y_int = int(x), int(y)
                screen_x, screen_y = self._to_screen_coords(x_int, y_int)
                
                # Log the click for debugging
                logger.info(f"Clicking at ({x_int}, {y_int}) with confidence {confidence:.2f}")
                
                try:
                    self.pyautogui.click(screen_x, screen_y)
                    # Save a debug screenshot highlighting click point (best-effort)
                    try:
                        self._save_debug_click_image(x_int, y_int)
                    except Exception:
                        pass

                    # Success - reset failure counter and store pattern
                    if self.consecutive_failures > 0:
                        self.consecutive_failures = 0
                    # Store successful pattern for learning
                    if expected_text:
                        self.successful_patterns.append({
                            "text": expected_text,
                            "coords": (x_int, y_int),
                            "confidence": confidence,
                            "timestamp": datetime.now().isoformat(),
                        })
                        # Keep only last 20 patterns
                        if len(self.successful_patterns) > 20:
                            self.successful_patterns.pop(0)
                    return True, f"Clicked at ({x_int}, {y_int})"
                except Exception as e:
                    # Failure - increment counter and try nearby coordinates
                    self.consecutive_failures += 1
                    return self._try_nearby_coordinates(x_int, y_int, expected_text, str(e))
            elif "text" in target:
                # Try OCR-based click
                text = target["text"]
                return self._click_text(text)
        elif target is None:
            return False, "No click target provided - need x,y coordinates"
        return False, f"Invalid click target format: {target}. Expected {{\"x\": number, \"y\": number}}"

    def _find_text_with_ocr(self, text_query: str, screenshot_path: Optional[Path] = None) -> Optional[Tuple[int, int]]:
        """Find text on screen using OCR and return its center coordinates.

        This version caches OCR results per screenshot to avoid repeated processing.
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            logger.debug("pytesseract or PIL not available for OCR")
            return None

        # Use provided screenshot or current state
        img_path = screenshot_path or (self.current_state.screenshot_path if self.current_state else None)
        if not img_path or not img_path.exists():
            return None

        cache_key = str(img_path)
        if self._ocr_cache is None:
            self._ocr_cache = {}

        # If we haven't run OCR on this screenshot yet, do it and cache results
        if cache_key not in self._ocr_cache:
            mapping: Dict[str, Tuple[Tuple[int, int], float]] = {}
            try:
                img = Image.open(img_path)
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                n_boxes = len(data.get('text', []))
                for i in range(n_boxes):
                    raw_text = data['text'][i].strip()
                    if not raw_text:
                        continue
                    key = raw_text.lower()
                    conf_raw = data['conf'][i]
                    try:
                        conf = float(conf_raw) if conf_raw != -1 else 0.0
                    except Exception:
                        conf = 0.0
                    x = int((data['left'][i] + data['width'][i] / 2))
                    y = int((data['top'][i] + data['height'][i] / 2))
                    existing = mapping.get(key)
                    if not existing or conf > existing[1]:
                        mapping[key] = ((x, y), conf)
            except Exception as e:
                logger.debug(f"OCR run failed: {e}")
                mapping = {}

            self._ocr_cache[cache_key] = mapping

        mapping = self._ocr_cache.get(cache_key, {})
        text_query_lower = text_query.lower().strip()

        # Direct exact match
        if text_query_lower in mapping:
            coords, conf = mapping[text_query_lower]
            logger.info(f"OCR found '{text_query}' at {coords} (confidence: {conf:.1f})")
            return coords

        # Partial/substring match
        best = None
        best_conf = 0.0
        for key, (coords, conf) in mapping.items():
            if text_query_lower in key or key in text_query_lower:
                if conf > best_conf:
                    best = coords
                    best_conf = conf

        if best:
            logger.info(f"OCR fuzzy matched '{text_query}' to '{key}' at {best} (confidence: {best_conf:.1f})")
            return best

        return None

    def _verify_coordinates_with_ocr(self, x: float, y: float, expected_text: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Verify that coordinates point to expected text using OCR.
        
        Args:
            x, y: Coordinates to verify
            expected_text: Optional text that should be near these coordinates
            
        Returns:
            (is_valid, message)
        """
        if not expected_text or not self.current_state:
            return True, None  # Can't verify without text or screenshot
        
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return True, None  # OCR not available, skip verification
        
        try:
            img = Image.open(self.current_state.screenshot_path)
            
            # Extract text in a small region around the coordinates
            margin = 50
            x_int, y_int = int(x), int(y)
            region = img.crop((
                max(0, x_int - margin),
                max(0, y_int - margin),
                min(img.width, x_int + margin),
                min(img.height, y_int + margin)
            ))
            
            # Run OCR on region
            ocr_text = pytesseract.image_to_string(region).lower()
            expected_lower = expected_text.lower()
            
            # Check if expected text appears in OCR result
            if expected_lower in ocr_text or any(word in ocr_text for word in expected_lower.split()):
                return True, f"OCR verified '{expected_text}' near coordinates"
            
            return False, f"OCR did not find '{expected_text}' near coordinates ({x_int}, {y_int})"
            
        except Exception as e:
            logger.debug(f"OCR verification failed: {e}")
            return True, None  # Don't fail on OCR errors

    def _post_click_verify(self, x: int, y: int, expected_text: str) -> Tuple[bool, Optional[str]]:
        """After clicking, update the screenshot and verify that the expected text appears near coordinates.

        Returns (verified, message)
        """
        try:
            # Take a fresh screenshot to capture UI changes
            self.take_screenshot("post_click_verify")
            return self._verify_coordinates_with_ocr(x, y, expected_text)
        except Exception as e:
            logger.debug(f"Post-click verification failed: {e}")
            return True, None

    def _try_nearby_coordinates(self, x: int, y: int, expected_text: Optional[str], error: str) -> Tuple[bool, str]:
        """Try clicking at nearby coordinates if initial click failed or verification failed.

        Uses configured offsets and a retry budget. Performs post-click verification when expected_text
        is provided and persists successful patterns.
        """
        offsets = list(self.retry_offsets)
        attempts = 0

        for offset_x, offset_y in offsets:
            if attempts >= self.retry_budget:
                break
            new_x = x + offset_x
            new_y = y + offset_y
            attempts += 1

            # Validate new coordinates
            is_valid, _ = self._validate_coordinates(new_x, new_y)
            if not is_valid:
                continue

            try:
                logger.info(f"Trying nearby coordinates ({new_x}, {new_y}) after failed click at ({x}, {y})")
                screen_x, screen_y = self._to_screen_coords(new_x, new_y)
                self.pyautogui.click(screen_x, screen_y)
                # Post-click verification if expected text provided
                if expected_text:
                    verified, msg = self._post_click_verify(new_x, new_y, expected_text)
                    if not verified:
                        logger.warning(f"Verification failed at nearby coords ({new_x},{new_y}): {msg}")
                        continue

                # Success with nearby coordinates
                self.consecutive_failures = 0
                # Persist success pattern
                if expected_text:
                    self.successful_patterns.append({
                        "text": expected_text,
                        "coords": (new_x, new_y),
                        "confidence": 0.8,
                        "timestamp": datetime.now().isoformat(),
                    })
                    if len(self.successful_patterns) > 20:
                        self.successful_patterns.pop(0)
                    try:
                        self._save_successful_patterns()
                    except Exception:
                        pass

                return True, f"Clicked at nearby coordinates ({new_x}, {new_y}) after initial failure"
            except Exception:
                continue

        # If OCR is available and we have expected text, try OCR-based click
        if expected_text:
            ocr_coords = self._find_text_with_ocr(expected_text)
            if ocr_coords:
                ocr_x, ocr_y = ocr_coords
                distance = ((ocr_x - x) ** 2 + (ocr_y - y) ** 2) ** 0.5
                if distance > 20:  # Significant difference
                    try:
                        logger.info(f"Trying OCR coordinates ({ocr_x}, {ocr_y}) after coordinate click failed")
                        screen_x, screen_y = self._to_screen_coords(ocr_x, ocr_y)
                        self.pyautogui.click(screen_x, screen_y)
                        self.consecutive_failures = 0
                        # Persist OCR success
                        self.successful_patterns.append({
                            "text": expected_text,
                            "coords": (ocr_x, ocr_y),
                            "confidence": 0.9,
                            "timestamp": datetime.now().isoformat(),
                        })
                        try:
                            self._save_successful_patterns()
                        except Exception:
                            pass
                        return True, f"Clicked using OCR coordinates ({ocr_x}, {ocr_y}) after coordinate click failed"
                    except Exception:
                        pass

        # All retries exhausted
        return False, f"Click failed at ({x}, {y}) and nearby coordinates: {error}"

    def _save_debug_click_image(self, x: int, y: int, radius: int = 30) -> Optional[str]:
        """Save a debug screenshot highlighting clicked area."""
        if not self.current_state:
            return None
        try:
            from PIL import Image, ImageDraw
            img = Image.open(self.current_state.screenshot_path).convert("RGBA")
            draw = ImageDraw.Draw(img)
            left = max(0, x - radius)
            top = max(0, y - radius)
            right = min(img.width, x + radius)
            bottom = min(img.height, y + radius)
            draw.rectangle([left, top, right, bottom], outline="red", width=3)
            fname = EVIDENCE_DIR / f"click_debug_{self.current_state.timestamp}_{x}_{y}.png"
            img.save(fname)
            logger.debug(f"Saved debug click image {fname}")
            return str(fname)
        except Exception as e:
            logger.debug(f"Failed to save debug click image: {e}")
            return None

    def _load_successful_patterns(self) -> None:
        """Load persisted successful patterns from disk if available."""
        try:
            if self.patterns_path.exists():
                import json
                with open(self.patterns_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.successful_patterns = data
        except Exception as e:
            logger.debug(f"Failed to load successful patterns: {e}")

    def _save_successful_patterns(self) -> None:
        """Persist successful patterns to disk (best-effort)."""
        try:
            self.patterns_path.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(self.patterns_path, "w", encoding="utf-8") as f:
                json.dump(self.successful_patterns[-100:], f)
        except Exception as e:
            logger.debug(f"Failed to save successful patterns: {e}")
    def _click_text(self, text: str) -> Tuple[bool, str]:
        """Try to click on text found on screen using OCR."""
        coords = self._find_text_with_ocr(text)
        if coords:
            x, y = coords
            try:
                screen_x, screen_y = self._to_screen_coords(x, y)
                self.pyautogui.click(screen_x, screen_y)
                self.consecutive_failures = 0
                return True, f"Clicked on '{text}' at ({x}, {y}) using OCR"
            except Exception as e:
                return False, f"Failed to click OCR coordinates ({x}, {y}): {e}"
        return False, f"Could not find '{text}' on screen using OCR. Please provide x,y coordinates."

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
        low_conf_threshold = float(os.getenv("TREYS_AGENT_UI_CONFIDENCE_MIN", "0.35"))
        low_conf_steps = int(os.getenv("TREYS_AGENT_UI_LOW_CONFIDENCE_STEPS", "2"))
        stall_steps = int(os.getenv("TREYS_AGENT_UI_STALL_STEPS", "3"))
        low_conf_count = 0
        stall_count = 0
        last_observation = ""

        while steps_taken < self.max_steps:
            steps_taken += 1

            # Take screenshot
            state = self.take_screenshot(f"step_{steps_taken}")

            # Analyze screen
            analysis = self.analyze_screen(objective, context)

            # Confidence / stall guard -> ask for human correction
            confidence = float(analysis.get("confidence", 1.0) or 0.0)
            observation = (analysis.get("observation") or "").strip().lower()
            if observation and observation == last_observation:
                stall_count += 1
            else:
                stall_count = 0
                last_observation = observation

            if confidence < low_conf_threshold:
                low_conf_count += 1
            else:
                low_conf_count = 0

            if analysis.get("action") not in {"done", "ask_user", "error"} and on_user_input:
                if low_conf_count >= low_conf_steps or stall_count >= stall_steps:
                    analysis = {
                        "observation": analysis.get("observation", ""),
                        "reasoning": "Low confidence or stalled; requesting user guidance.",
                        "action": "ask_user",
                        "target": None,
                        "value": "I'm not confident about the next UI action. What should I do next? You can say: click <target>, type <text>, open <url>.",
                        "confidence": confidence,
                    }
                    low_conf_count = 0
                    stall_count = 0

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
                # Escalate to reasoning if not already using it
                self.consecutive_failures += 1
                if self.consecutive_failures >= 2 and not self.use_reasoning:
                    logger.info("ask_user detected - escalating to reasoning model")
                    self.use_reasoning = True
                    # Try again with reasoning model instead of asking user
                    continue

                if on_user_input:
                    answer = on_user_input(analysis.get("value", "Need input"))
                    context = f"{context}\nUser said: {answer}"
                    self.consecutive_failures = 0  # Reset after getting help
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
                # Escalate to reasoning if not already using it
                self.consecutive_failures += 1
                if self.consecutive_failures >= 2 and not self.use_reasoning:
                    logger.info("error detected - escalating to reasoning model")
                    self.use_reasoning = True
                    # Try again with reasoning model
                    context = f"{context}\nPrevious attempt returned error: {analysis.get('value')}"
                    continue

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
                # Visual feedback: analyze what went wrong
                self.consecutive_failures += 1
                
                # If we've failed multiple times, take a new screenshot and analyze
                if self.consecutive_failures >= 2:
                    logger.warning(f"Multiple failures ({self.consecutive_failures}), taking new screenshot to analyze")
                    new_state = self.take_screenshot(f"failure_analysis_{steps_taken}")
                    
                    # Add failure context for next analysis
                    context = f"{context}\nPrevious action failed: {message}\nAttempted: {analysis.get('action')} at {analysis.get('target')}"
                    
                    # If we have successful patterns, try to use them
                    if self.successful_patterns and analysis.get("target"):
                        # Look for similar patterns
                        target_text = analysis.get("observation", "")
                        for pattern in self.successful_patterns[-5:]:  # Check recent patterns
                            if pattern["text"].lower() in target_text.lower():
                                logger.info(f"Found successful pattern for '{pattern['text']}': {pattern['coords']}")
                
                # Add error to context and retry
                context = f"{context}\nPrevious action failed: {message}"
                logger.warning(f"Action failed: {message}")

                # Escalate to reasoning model after 2 consecutive failures
                if self.consecutive_failures >= 2 and not self.use_reasoning:
                    logger.info("Escalating to reasoning model after repeated failures")
                    self.use_reasoning = True
            else:
                # Success! Reset failure counter and go back to fast mode
                self.consecutive_failures = 0
                if self.use_reasoning:
                    logger.info("Action succeeded - returning to fast model")
                    self.use_reasoning = False

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
