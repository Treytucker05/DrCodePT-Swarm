"""
Windows Computer Use Execution Layer

Central router for desktop automation with UIA-first, keyboard fallback,
vision coordinates as last resort. Includes anti-thrash guards and download watching.
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable

logger = logging.getLogger(__name__)


class ActionStrategy(Enum):
    """Strategies for executing UI actions."""
    UIA = "uia"  # UI Automation (element-based)
    KEYBOARD = "keyboard"  # Keyboard navigation (Ctrl+F, Tab, Enter)
    VISION = "vision"  # Vision-guided coordinates
    ASK_USER = "ask_user"  # Request user help


class GoogleConsoleState(Enum):
    """States in Google Console OAuth setup flow."""
    UNKNOWN = "unknown"
    CREDENTIALS_PAGE = "credentials_page"
    CONSENT_SCREEN = "consent_screen"
    OAUTH_CLIENT_FORM = "oauth_client_form"
    CLIENT_CREATED_MODAL = "client_created_modal"
    DONE = "done"
    ERROR = "error"


@dataclass
class ActionResult:
    """Result of a UI action attempt."""
    success: bool
    strategy: ActionStrategy
    message: str
    screenshot_path: Optional[Path] = None
    state: Optional[GoogleConsoleState] = None


@dataclass
class ScreenshotHash:
    """Hash of a screenshot for change detection."""
    hash_value: str
    timestamp: float
    path: Path


class AntiThrashGuard:
    """Prevents infinite loops by detecting visual stalls."""

    def __init__(self, max_identical: int = 2, max_retries_per_step: int = 3):
        self.max_identical = max_identical
        self.max_retries_per_step = max_retries_per_step
        self.screenshot_history: List[ScreenshotHash] = []
        self.retry_counts: Dict[str, int] = {}

    def compute_hash(self, screenshot_path: Path) -> str:
        """Compute perceptual hash of screenshot."""
        try:
            from PIL import Image
            # Resize to 8x8 and convert to grayscale for perceptual hash
            img = Image.open(screenshot_path).convert('L').resize((8, 8))
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            bits = ''.join('1' if p > avg else '0' for p in pixels)
            return hashlib.md5(bits.encode()).hexdigest()[:16]
        except Exception as e:
            logger.warning(f"Failed to compute screenshot hash: {e}")
            # Fallback: use file size + partial content
            return hashlib.md5(screenshot_path.read_bytes()[:1024]).hexdigest()[:16]

    def check_stalled(self, screenshot_path: Path) -> Tuple[bool, str]:
        """Check if UI is stalled (no visual progress)."""
        current_hash = self.compute_hash(screenshot_path)
        current = ScreenshotHash(current_hash, time.time(), screenshot_path)

        # Add to history
        self.screenshot_history.append(current)

        # Keep only recent history
        if len(self.screenshot_history) > 5:
            self.screenshot_history.pop(0)

        # Check for identical screenshots
        if len(self.screenshot_history) >= self.max_identical:
            recent_hashes = [s.hash_value for s in self.screenshot_history[-self.max_identical:]]
            if len(set(recent_hashes)) == 1:
                return True, f"Stalled: {self.max_identical} identical screenshots"

        return False, ""

    def check_retry_limit(self, step_id: str) -> Tuple[bool, str]:
        """Check if retry limit exceeded for this step."""
        count = self.retry_counts.get(step_id, 0)
        if count >= self.max_retries_per_step:
            return True, f"Retry limit exceeded: {count}/{self.max_retries_per_step}"
        return False, ""

    def increment_retry(self, step_id: str):
        """Increment retry counter for a step."""
        self.retry_counts[step_id] = self.retry_counts.get(step_id, 0) + 1

    def reset_retry(self, step_id: str):
        """Reset retry counter for a step."""
        self.retry_counts[step_id] = 0


class DownloadWatcher:
    """Watches for downloaded files."""

    def __init__(self, download_dir: Optional[Path] = None):
        self.download_dir = download_dir or Path.home() / "Downloads"
        self.initial_files: set[Path] = set()

    def start_watching(self):
        """Record initial state of download directory."""
        if self.download_dir.exists():
            self.initial_files = set(self.download_dir.glob("*"))
        else:
            self.initial_files = set()
        logger.info(f"Started watching {self.download_dir} ({len(self.initial_files)} existing files)")

    def wait_for_download(
        self,
        pattern: str = "client_secret*.json",
        timeout: float = 30.0,
        poll_interval: float = 0.5
    ) -> Optional[Path]:
        """Wait for a new file matching pattern to appear."""
        logger.info(f"Waiting for download: {pattern} (timeout: {timeout}s)")
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not self.download_dir.exists():
                time.sleep(poll_interval)
                continue

            current_files = set(self.download_dir.glob(pattern))
            new_files = current_files - self.initial_files

            if new_files:
                # Return the newest file
                newest = max(new_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"Download detected: {newest}")
                return newest

            time.sleep(poll_interval)

        logger.warning(f"Download timeout after {timeout}s")
        return None

    def move_and_verify(
        self,
        source: Path,
        dest: Path,
        required_keys: List[str] = None
    ) -> Tuple[bool, str]:
        """Move file and verify contents."""
        try:
            # Create parent directory
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Read and verify if JSON
            if required_keys and source.suffix == '.json':
                import json
                with source.open('r') as f:
                    data = json.load(f)

                # Check for required keys
                missing = [k for k in required_keys if k not in str(data)]
                if missing:
                    return False, f"Missing required keys: {missing}"

            # Move file
            if dest.exists():
                dest.unlink()  # Remove old file

            source.rename(dest)
            logger.info(f"Moved {source.name} → {dest}")
            return True, f"Successfully saved to {dest}"

        except Exception as e:
            return False, f"Failed to move/verify file: {e}"


class ComputerUseRouter:
    """
    Central router for computer use actions.

    Tries strategies in order:
    1. UIA (element-based)
    2. Keyboard navigation
    3. Vision coordinates
    4. Ask user (after retries)
    """

    def __init__(self):
        self.ui_controller = None
        self.vision_executor = None
        self.anti_thrash = AntiThrashGuard()
        self.download_watcher = DownloadWatcher()
        self._pyautogui = None
        self._initialized = False

    def initialize(self) -> Tuple[bool, str]:
        """Initialize all components."""
        if self._initialized:
            return True, "Already initialized"

        errors = []

        # Initialize UI controller
        try:
            from agent.autonomous.windows_ui import get_ui_controller
            self.ui_controller = get_ui_controller()
            ok, msg = self.ui_controller.initialize()
            if not ok:
                errors.append(f"UI: {msg}")
        except Exception as e:
            errors.append(f"UI: {e}")

        # Initialize vision executor
        try:
            from agent.autonomous.vision_executor import get_vision_executor
            self.vision_executor = get_vision_executor()
            ok, msg = self.vision_executor.initialize()
            if not ok:
                errors.append(f"Vision: {msg}")
        except Exception as e:
            errors.append(f"Vision: {e}")

        # Initialize PyAutoGUI
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0.1
            self._pyautogui = pyautogui
        except Exception as e:
            errors.append(f"PyAutoGUI: {e}")

        if self.ui_controller is None and self.vision_executor is None:
            return False, f"No automation method available: {'; '.join(errors)}"

        self._initialized = True
        return True, "Computer use router initialized"

    def click(
        self,
        target: str = None,
        x: float = None,
        y: float = None,
        screenshot_path: Path = None,
        step_id: str = "click"
    ) -> ActionResult:
        """
        Route click action through strategies.

        Args:
            target: Text label of element to click (for UIA/keyboard)
            x, y: Pixel coordinates (for direct clicking)
            screenshot_path: Current screenshot for vision analysis
            step_id: Unique step identifier for retry tracking
        """
        if not self._initialized:
            ok, msg = self.initialize()
            if not ok:
                return ActionResult(False, ActionStrategy.ASK_USER, msg)

        # Check retry limit
        exceeded, msg = self.anti_thrash.check_retry_limit(step_id)
        if exceeded:
            return ActionResult(False, ActionStrategy.ASK_USER, msg)

        # If coordinates provided, use them directly
        if x is not None and y is not None:
            return self._click_coordinates(x, y, ActionStrategy.VISION)

        # Try UIA first if target label provided
        if target and self.ui_controller:
            result = self._try_uia_click(target)
            if result.success:
                self.anti_thrash.reset_retry(step_id)
                return result
            logger.debug(f"UIA failed: {result.message}")

        # Try keyboard navigation
        if target:
            result = self._try_keyboard_click(target)
            if result.success:
                self.anti_thrash.reset_retry(step_id)
                return result
            logger.debug(f"Keyboard failed: {result.message}")

        # Try vision coordinates
        if screenshot_path and self.vision_executor:
            result = self._try_vision_click(target or "element", screenshot_path)
            if result.success:
                self.anti_thrash.reset_retry(step_id)
                return result
            logger.debug(f"Vision failed: {result.message}")

        # All strategies failed
        self.anti_thrash.increment_retry(step_id)
        return ActionResult(
            False,
            ActionStrategy.ASK_USER,
            f"All strategies failed for: {target or f'({x}, {y})'}"
        )

    def _try_uia_click(self, target: str) -> ActionResult:
        """Try clicking via UI Automation."""
        try:
            # Try by name first
            element = self.ui_controller.find_element(name=target)
            if element and element.click():
                time.sleep(0.5)
                return ActionResult(True, ActionStrategy.UIA, f"Clicked '{target}' via UIA")

            # Try by button role
            element = self.ui_controller.find_element(role="button", name=target)
            if element and element.click():
                time.sleep(0.5)
                return ActionResult(True, ActionStrategy.UIA, f"Clicked button '{target}' via UIA")

            return ActionResult(False, ActionStrategy.UIA, f"Element '{target}' not found")
        except Exception as e:
            return ActionResult(False, ActionStrategy.UIA, f"UIA error: {e}")

    def _try_keyboard_click(self, target: str) -> ActionResult:
        """Try clicking via keyboard navigation (Ctrl+F search)."""
        if not self._pyautogui:
            return ActionResult(False, ActionStrategy.KEYBOARD, "PyAutoGUI not available")

        try:
            # Ctrl+F to open find dialog
            self._pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.3)

            # Type search term
            self._pyautogui.write(target, interval=0.05)
            time.sleep(0.3)

            # Press Enter to find
            self._pyautogui.press('enter')
            time.sleep(0.2)

            # Press Escape to close find dialog
            self._pyautogui.press('escape')
            time.sleep(0.2)

            # Press Tab to focus found element, then Space/Enter to activate
            self._pyautogui.press('tab')
            time.sleep(0.1)
            self._pyautogui.press('space')
            time.sleep(0.5)

            return ActionResult(True, ActionStrategy.KEYBOARD, f"Activated '{target}' via keyboard")
        except Exception as e:
            return ActionResult(False, ActionStrategy.KEYBOARD, f"Keyboard error: {e}")

    def _try_vision_click(self, target: str, screenshot_path: Path) -> ActionResult:
        """Try clicking via vision-guided coordinates."""
        if not self.vision_executor:
            return ActionResult(False, ActionStrategy.VISION, "Vision executor not available")

        try:
            # Analyze screenshot
            analysis = self.vision_executor.analyze_screen(
                objective=f"Click on '{target}'",
                context="Find the element and provide exact coordinates"
            )

            if analysis.get("action") != "click":
                return ActionResult(False, ActionStrategy.VISION, f"Vision returned: {analysis.get('action')}")

            # Extract coordinates
            target_coords = analysis.get("target", {})
            if isinstance(target_coords, dict) and "x" in target_coords and "y" in target_coords:
                x, y = target_coords["x"], target_coords["y"]
                return self._click_coordinates(x, y, ActionStrategy.VISION)

            return ActionResult(False, ActionStrategy.VISION, "No coordinates in vision response")
        except Exception as e:
            return ActionResult(False, ActionStrategy.VISION, f"Vision error: {e}")

    def _click_coordinates(self, x: float, y: float, strategy: ActionStrategy) -> ActionResult:
        """Click at specific coordinates."""
        if not self._pyautogui:
            return ActionResult(False, strategy, "PyAutoGUI not available")

        try:
            self._pyautogui.click(x, y)
            time.sleep(0.5)
            return ActionResult(True, strategy, f"Clicked at ({int(x)}, {int(y)})")
        except Exception as e:
            return ActionResult(False, strategy, f"Click error: {e}")

    def type_text(self, text: str, use_keyboard: bool = True) -> ActionResult:
        """Type text via keyboard."""
        if not self._pyautogui:
            return ActionResult(False, ActionStrategy.KEYBOARD, "PyAutoGUI not available")

        try:
            if use_keyboard:
                self._pyautogui.write(text, interval=0.05)
            else:
                self._pyautogui.typewrite(text, interval=0.05)
            time.sleep(0.3)
            return ActionResult(True, ActionStrategy.KEYBOARD, f"Typed: {text[:50]}...")
        except Exception as e:
            return ActionResult(False, ActionStrategy.KEYBOARD, f"Type error: {e}")

    def navigate_to_url(self, url: str) -> ActionResult:
        """Navigate to URL via address bar."""
        if not self._pyautogui:
            return ActionResult(False, ActionStrategy.KEYBOARD, "PyAutoGUI not available")

        try:
            # Ctrl+L to focus address bar
            self._pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)

            # Type URL
            self._pyautogui.write(url, interval=0.05)
            time.sleep(0.3)

            # Press Enter
            self._pyautogui.press('enter')
            time.sleep(2.0)  # Wait for page load

            return ActionResult(True, ActionStrategy.KEYBOARD, f"Navigated to: {url}")
        except Exception as e:
            return ActionResult(False, ActionStrategy.KEYBOARD, f"Navigation error: {e}")

    def take_screenshot(self, name: str = "screen") -> Optional[Path]:
        """Take a screenshot."""
        if self.vision_executor:
            return self.vision_executor.take_screenshot(name).screenshot_path
        elif self._pyautogui:
            from datetime import datetime
            screenshots_dir = Path(__file__).parent.parent.parent / "agent" / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = screenshots_dir / f"{name}_{ts}.png"
            img = self._pyautogui.screenshot()
            img.save(path)
            return path
        return None


# Singleton instance
_router: Optional[ComputerUseRouter] = None


def get_computer_use_router() -> ComputerUseRouter:
    """Get the singleton router instance."""
    global _router
    if _router is None:
        _router = ComputerUseRouter()
        _router.initialize()
    return _router


__all__ = [
    "ComputerUseRouter",
    "ActionStrategy",
    "GoogleConsoleState",
    "ActionResult",
    "AntiThrashGuard",
    "DownloadWatcher",
    "get_computer_use_router",
]
