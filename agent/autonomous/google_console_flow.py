"""
Google Console OAuth Setup State Machine

Deterministic flow for creating OAuth client credentials.
No free-form planning - uses explicit state detection and action table.
"""
from __future__ import annotations

import glob
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent.autonomous.computer_use import (
    ComputerUseRouter,
    GoogleConsoleState,
    ActionResult,
    ActionStrategy,
    get_computer_use_router,
)

logger = logging.getLogger(__name__)


# Canonical URLs for Google Console
GOOGLE_CONSOLE_URLS = {
    "credentials": "https://console.cloud.google.com/apis/credentials",
    "consent": "https://console.cloud.google.com/apis/credentials/consent",
    "api_library": "https://console.cloud.google.com/apis/library",
    "calendar_api": "https://console.cloud.google.com/apis/library/calendar-json.googleapis.com",
}


class GoogleConsoleStateMachine:
    """State machine for Google Console OAuth setup."""

    def __init__(self, router: Optional[ComputerUseRouter] = None):
        self.router = router or get_computer_use_router()
        self.current_state = GoogleConsoleState.UNKNOWN
        self.max_steps = 30
        self.screenshots_dir = Path(__file__).parent.parent.parent / "agent" / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._download_initiated = False  # Track when download button is clicked
        # Stall escalation tracking
        self.last_recovery_action: Optional[str] = None
        self.consecutive_recovery_count = 0
        self.navigation_used_as_recovery = False
        # Progress tracking for escalation
        self._nav_attempts_to_credentials = 0
        self._same_state_count = 0
        self._no_click_count = 0
        self._last_state = GoogleConsoleState.UNKNOWN
        self._last_progress_state = GoogleConsoleState.UNKNOWN

    def _detect_state_keywords(self, screenshot_path: Path) -> Optional[GoogleConsoleState]:
        """
        Simple keyword-based state detection (no LLM).
        
        Checks screenshot text for specific keywords to determine state.
        Returns None only if no keywords match, allowing fallback to LLM detection.
        """
        try:
            # Extract text from screenshot using OCR
            import pytesseract
            from PIL import Image
            
            img = Image.open(screenshot_path)
            ocr_text = pytesseract.image_to_string(img).lower()
            
            # Check for Create credentials dropdown menu (transient menu state) - check FIRST (more specific)
            has_create_credentials = "create credentials" in ocr_text or "+ create credentials" in ocr_text
            has_menu_items = "api key" in ocr_text or "oauth client id" in ocr_text or "service account" in ocr_text
            
            if has_create_credentials and has_menu_items:
                logger.info("[STATE] Keyword detection: CREATE_CREDENTIALS_MENU (dropdown menu open)")
                return GoogleConsoleState.CREATE_CREDENTIALS_MENU
            
            # Check for Credentials page with "Configure consent screen" banner
            has_credentials = "credentials" in ocr_text
            has_configure_consent = "configure consent screen" in ocr_text or "configure oauth consent" in ocr_text
            
            if has_credentials and has_configure_consent:
                logger.info("[STATE] Keyword detection: CREDENTIALS_PAGE with consent screen banner")
                return GoogleConsoleState.CREDENTIALS_PAGE
            
            # Check for Credentials page without banner (still on credentials page)
            if has_credentials and ("create credentials" in ocr_text or "oauth client" in ocr_text):
                logger.info("[STATE] Keyword detection: CREDENTIALS_PAGE (no banner)")
                return GoogleConsoleState.CREDENTIALS_PAGE
            
            # Check for OAuth type form (has "Application type" AND "Create OAuth client ID")
            has_application_type = "application type" in ocr_text
            has_create_oauth_client = "create oauth client id" in ocr_text
            
            if has_application_type and has_create_oauth_client:
                logger.info("[STATE] Keyword detection: OAUTH_TYPE_FORM")
                return GoogleConsoleState.OAUTH_TYPE_FORM
            
            # Check for OAuth type dropdown open (dropdown visible AND "Desktop app")
            has_dropdown_visible = "desktop app" in ocr_text or "web application" in ocr_text
            if has_application_type and has_dropdown_visible and not has_create_oauth_client:
                logger.info("[STATE] Keyword detection: OAUTH_TYPE_DROPDOWN_OPEN")
                return GoogleConsoleState.OAUTH_TYPE_DROPDOWN_OPEN
            
            # Check for OAuth name form (Application type shows "Desktop app" AND "Create" button visible)
            has_desktop_app_selected = "desktop app" in ocr_text
            has_create_button = "create" in ocr_text
            
            if has_application_type and has_desktop_app_selected and has_create_button and not has_create_oauth_client:
                logger.info("[STATE] Keyword detection: OAUTH_NAME_FORM")
                return GoogleConsoleState.OAUTH_NAME_FORM
            
            # Check for OAuth created modal (has "OAuth client created" OR "Download JSON")
            has_client_created = "oauth client created" in ocr_text
            has_download_json = "download json" in ocr_text
            
            if has_client_created or has_download_json:
                logger.info("[STATE] Keyword detection: OAUTH_CREATED_MODAL")
                return GoogleConsoleState.OAUTH_CREATED_MODAL
            
            # Legacy: Check for OAuth client form (has "Application type" and options) - keep for backward compat
            if has_application_type and has_desktop_app_selected and has_create_button:
                logger.info("[STATE] Keyword detection: OAUTH_CLIENT_FORM (legacy)")
                return GoogleConsoleState.OAUTH_CLIENT_FORM
            
            # Legacy: Check for client created modal (has "OAuth client created" and "Download JSON")
            if has_client_created and has_download_json:
                logger.info("[STATE] Keyword detection: CLIENT_CREATED_MODAL (legacy)")
                return GoogleConsoleState.CLIENT_CREATED_MODAL
            
            # Check for consent screen completion (has "OAuth consent screen" and "Test users")
            has_oauth_consent = "oauth consent screen" in ocr_text
            has_test_users = "test users" in ocr_text
            
            if has_oauth_consent and has_test_users:
                logger.info("[STATE] Keyword detection: CONSENT_SCREEN completed")
                return GoogleConsoleState.CONSENT_SCREEN
            
        except Exception as e:
            logger.debug(f"Keyword detection failed: {e}")
        
        return None

    def detect_state(self, screenshot_path: Path) -> GoogleConsoleState:
        """
        Detect current state from screenshot.
        
        ALWAYS tries keyword-based detection first. Only uses LLM if keywords return None.
        LLM failures are handled gracefully (no error spam, just return UNKNOWN).
        """
        # Check download states first (based on watcher, not OCR)
        if hasattr(self.router, 'download_watcher') and self.router.download_watcher:
            # Check if download is complete by looking for file
            try:
                download_dir = self.router.download_watcher.download_dir
                if download_dir.exists():
                    # Look for client_secret*.json files
                    pattern = str(download_dir / "client_secret*.json")
                    files = glob.glob(pattern)
                    if files:
                        # Get the newest file
                        newest = max(files, key=lambda p: Path(p).stat().st_mtime)
                        newest_path = Path(newest)
                        # Verify JSON has required keys
                        try:
                            with open(newest_path, 'r') as f:
                                data = json.load(f)
                            if all(key in data for key in ["client_id", "client_secret", "redirect_uris"]):
                                logger.info("[STATE] Keyword detection: DOWNLOAD_COMPLETE")
                                return GoogleConsoleState.DOWNLOAD_COMPLETE
                        except Exception:
                            pass
            except Exception:
                pass
            
            # Check if download was initiated (download button clicked)
            if self._download_initiated:
                logger.info("[STATE] Keyword detection: DOWNLOAD_INITIATED")
                return GoogleConsoleState.DOWNLOAD_INITIATED
        
        # ALWAYS try keyword-based detection first (fast, no LLM, no blocking)
        keyword_state = self._detect_state_keywords(screenshot_path)
        if keyword_state:
            return keyword_state
        
        # Only fallback to LLM if keywords didn't match
        # But handle LLM failures gracefully - don't block or spam errors
        if not self.router.vision_executor:
            logger.debug("[STATE] No vision executor, returning UNKNOWN")
            return GoogleConsoleState.UNKNOWN

        try:
            prompt = f"""Analyze this Google Cloud Console screenshot and identify the current state.

Look for these indicators:

1. CREDENTIALS_PAGE: Shows "Credentials" heading, "CREATE CREDENTIALS" button, list of existing credentials
2. CONSENT_SCREEN: Shows "OAuth consent screen" tab, "User Type" selection (Internal/External)
3. OAUTH_CLIENT_FORM: Shows "Create OAuth client ID" form with:
   - "Application type" dropdown
   - "Desktop app" option
   - "Name" field
   - "CREATE" button
4. CLIENT_CREATED_MODAL: Shows modal/dialog with:
   - "OAuth client created" message
   - Client ID and Client secret displayed
   - "DOWNLOAD JSON" button
5. DONE: Shows confirmation that credentials were downloaded successfully
6. ERROR: Shows error message or unexpected state

Respond with JSON:
{{
    "state": "CREDENTIALS_PAGE|CONSENT_SCREEN|OAUTH_CLIENT_FORM|CLIENT_CREATED_MODAL|DONE|ERROR|UNKNOWN",
    "confidence": 0.0-1.0,
    "reasoning": "Why you chose this state",
    "key_elements_seen": ["element1", "element2"]
}}
"""

            response = self.router.vision_executor._call_vision_llm(
                prompt,
                self.router.vision_executor.current_state
            )

            if not response or not response.strip():
                logger.debug("[STATE] LLM returned empty response, using UNKNOWN")
                return GoogleConsoleState.UNKNOWN

            # Parse JSON response - handle failures gracefully
            try:
                data = json.loads(response)
                state_str = data.get("state", "UNKNOWN").upper()
                confidence = float(data.get("confidence", 0.0))

                logger.info(f"[STATE] LLM detection: {state_str} (confidence: {confidence:.2f})")
                logger.debug(f"Reasoning: {data.get('reasoning')}")
                logger.debug(f"Key elements: {data.get('key_elements_seen')}")

                # Map string to enum
                try:
                    return GoogleConsoleState[state_str]
                except KeyError:
                    logger.debug(f"[STATE] Unknown state string from LLM: {state_str}, using UNKNOWN")
                    return GoogleConsoleState.UNKNOWN

            except json.JSONDecodeError:
                # Don't spam errors - just log debug and return UNKNOWN
                logger.debug(f"[STATE] LLM JSON parse failed, response: {response[:100]}...")
                return GoogleConsoleState.UNKNOWN

        except Exception as e:
            # Don't spam errors - just log debug and return UNKNOWN
            logger.debug(f"[STATE] LLM detection exception: {e}")
            return GoogleConsoleState.UNKNOWN

    def _click_via_ctrl_f(self, search_text: str, step_id: str = "ctrl_f_click") -> ActionResult:
        """
        Use Ctrl+F to locate text, then immediately click it.

        This completes the full action (locate + click) to avoid partial state issues.
        Returns the final click result.
        """
        if not self.router._pyautogui:
            return ActionResult(False, ActionStrategy.KEYBOARD, "PyAutoGUI not available")

        try:
            # Focus Chrome first
            if self.router.ui_controller:
                try:
                    window = self.router.ui_controller.find_window(title_contains="Chrome")
                    if window:
                        self.router.ui_controller.focus_window(window)
                except Exception:
                    pass

            # Ctrl+F to open find dialog and locate text
            self.router._pyautogui.hotkey("ctrl", "f")
            time.sleep(0.2)

            # Type search text to locate element
            self.router._pyautogui.write(search_text, interval=0.05)
            time.sleep(0.3)

            logger.info(f"[LOCATE] Text located via Ctrl+F: {search_text}")

            # Close find dialog (Escape)
            self.router._pyautogui.press("escape")
            time.sleep(0.3)

            # IMMEDIATELY perform click (don't return partial result)
            screenshot = self.router.take_screenshot(f"{step_id}_{search_text.replace(' ', '_')}")
            if not screenshot:
                return ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot after Ctrl+F")

            logger.info(f"[CLICK] Executing mouse click on located element: {search_text}")
            result = self.router.click(
                target=search_text,
                screenshot_path=screenshot,
                step_id=step_id
            )

            # Return the final click result
            return result

        except Exception as e:
            return ActionResult(False, ActionStrategy.KEYBOARD, f"Ctrl+F click failed: {e}")

    def next_action(self, state: GoogleConsoleState) -> List[Dict[str, Any]]:
        """
        Get the next actions for a given state.

        Returns list of actions to execute in order.
        """
        action_table = {
            GoogleConsoleState.CREDENTIALS_PAGE: [
                {
                    "type": "check_credentials_page_state",
                    "description": "Check if consent screen banner exists or if ready to create OAuth client",
                    "wait_after": 0.5,
                },
            ],
            GoogleConsoleState.CREATE_CREDENTIALS_MENU: [
                {
                    "type": "click_menu_item",
                    "target": "OAuth client ID",
                    "description": "Click OAuth client ID menu item from dropdown",
                    "wait_after": 1.5,
                },
            ],
            GoogleConsoleState.CONSENT_SCREEN: [
                {
                    "type": "check_consent_complete",
                    "description": "Check if consent screen is already completed",
                    "wait_after": 0.5,
                },
            ],
            GoogleConsoleState.OAUTH_TYPE_FORM: [
                {
                    "type": "click_application_type",
                    "description": "Click Application type dropdown",
                    "wait_after": 0.5,
                },
            ],
            GoogleConsoleState.OAUTH_TYPE_DROPDOWN_OPEN: [
                {
                    "type": "click_desktop_app",
                    "description": "Click Desktop app option",
                    "wait_after": 0.5,
                },
            ],
            GoogleConsoleState.OAUTH_NAME_FORM: [
                {
                    "type": "click_create_button",
                    "description": "Click Create button",
                    "wait_after": 1.0,
                },
            ],
            GoogleConsoleState.OAUTH_CREATED_MODAL: [
                {
                    "type": "click_download_json",
                    "target": "Download JSON",
                    "description": "Click Download JSON button",
                    "wait_after": 1.0,
                },
            ],
            GoogleConsoleState.DOWNLOAD_INITIATED: [
                {
                    "type": "wait_for_download",
                    "description": "Wait for download to complete",
                    "wait_after": 1.0,
                },
            ],
            GoogleConsoleState.DOWNLOAD_COMPLETE: [
                {
                    "type": "move_and_verify_json",
                    "description": "Move file and verify JSON",
                    "wait_after": 0.5,
                },
            ],
            GoogleConsoleState.OAUTH_CLIENT_FORM: [
                {
                    "type": "fill_oauth_form",
                    "description": "Fill OAuth client form: Application type -> Desktop app -> Create",
                    "wait_after": 2.0,
                },
            ],
            GoogleConsoleState.CLIENT_CREATED_MODAL: [
                {
                    "type": "download_json",
                    "target": "DOWNLOAD JSON",
                    "description": "Click DOWNLOAD JSON and wait for file",
                    "wait_after": 1.0,
                },
            ],
            GoogleConsoleState.DONE: [],  # No actions needed
            GoogleConsoleState.ERROR: [
                {
                    "type": "recover",
                    "description": "Navigate back to credentials page",
                },
            ],
            GoogleConsoleState.UNKNOWN: [
                {
                    "type": "recover",
                    "description": "Navigate to credentials page",
                },
            ],
        }

        return action_table.get(state, [])

    def _check_precondition(
        self,
        action: Dict[str, Any],
        screenshot_path: Path
    ) -> Tuple[bool, str]:
        """
        Check preconditions before executing an action.

        Returns: (precondition_met, message)
        """
        action_type = action.get("type", "unknown")
        target = action.get("target", "")

        # For click actions, verify target is visible
        if action_type in ["click", "ctrl_f_click", "click_menu_item", "click_create_button"]:
            if not target:
                return False, f"No target specified for {action_type}"

            # Use OCR to verify text is present on screen
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(screenshot_path)
                ocr_text = pytesseract.image_to_string(img).lower()
                target_lower = target.lower()

                if target_lower not in ocr_text:
                    logger.warning(f"[PRECONDITION] Target '{target}' not visible on screen")
                    return False, f"Target '{target}' not visible - page may not be loaded"

                logger.debug(f"[PRECONDITION] Target '{target}' is visible")
                return True, "Precondition met"

            except Exception as e:
                logger.debug(f"Precondition check failed (OCR error): {e}")
                # Don't block action if OCR fails - let it try
                return True, "Precondition check skipped (OCR error)"

        # For other action types, no precondition check needed
        return True, "No preconditions required"

    def _verify_state_changed(
        self,
        before_state: GoogleConsoleState,
        after_screenshot: Path,
        action_description: str
    ) -> Tuple[bool, GoogleConsoleState, str]:
        """
        Verify that an action caused a state transition.

        Returns: (state_changed, new_state, message)
        """
        after_state = self.detect_state(after_screenshot)

        if before_state == after_state:
            # State didn't change - possible failure
            logger.warning(f"[PROGRESS] State unchanged after '{action_description}': still {before_state.value}")
            return False, after_state, f"Action did not change state (still {before_state.value})"

        logger.info(f"[PROGRESS] State transition: {before_state.value} → {after_state.value}")
        return True, after_state, f"State changed: {before_state.value} → {after_state.value}"

    def _reflect_on_action_failure(
        self,
        action: Dict[str, Any],
        error: str,
        screenshot_path: Path,
        step_count: int
    ) -> str:
        """
        Reflect on why an action failed and suggest alternative.

        Returns: reflection message with suggested alternative
        """
        action_type = action.get("type", "unknown")
        target = action.get("target", "N/A")
        description = action.get("description", "")

        # Simple reflection based on action type and error
        reflection = f"Action '{action_type}' failed: {error}\n"

        if "not found" in error.lower() or "not visible" in error.lower():
            reflection += "LIKELY CAUSE: Element not visible or page not loaded\n"
            reflection += "ALTERNATIVE: Try scrolling, waiting longer, or check if we're on the right page\n"
        elif "state unchanged" in error.lower():
            reflection += "LIKELY CAUSE: Click succeeded but didn't trigger expected state change\n"
            reflection += "ALTERNATIVE: Verify element was clickable, try keyboard navigation instead\n"
        elif "timeout" in error.lower():
            reflection += "LIKELY CAUSE: Operation took too long\n"
            reflection += "ALTERNATIVE: Increase wait time or simplify the action\n"
        else:
            reflection += "LIKELY CAUSE: Unexpected error\n"
            reflection += "ALTERNATIVE: Try recovery action or escalate to user\n"

        logger.info(f"[REFLECTION] {reflection}")
        return reflection

    def recover(self, recovery_type: str = "click") -> ActionResult:
        """
        Recovery action with diversification.
        
        Args:
            recovery_type: "click", "scroll", "refocus", or "navigate" (only once)
        """
        if recovery_type == "navigate":
            # Hard rule: navigate at most ONCE per run
            if self._nav_attempts_to_credentials >= 1:
                logger.info("[RECOVERY] Navigation suppressed (already attempted)")
                return ActionResult(False, ActionStrategy.KEYBOARD, "Navigation already attempted once this run")
            logger.info("Executing recovery: navigating to credentials page")
            self._nav_attempts_to_credentials += 1
            self.navigation_used_as_recovery = True
            return self.router.navigate_to_url(GOOGLE_CONSOLE_URLS["credentials"])
        elif recovery_type == "click":
            logger.info("[RECOVERY] Trying click-based recovery")
            # Try clicking common buttons
            screenshot_path = self.router.take_screenshot("recovery_click")
            if screenshot_path:
                # Try clicking "Configure consent screen" or "+ Create credentials"
                result = self.router.click(target="Configure consent screen", screenshot_path=screenshot_path, step_id="recovery_click_consent")
                if result.success:
                    return result
                result = self.router.click(target="Create credentials", screenshot_path=screenshot_path, step_id="recovery_click_create")
                if result.success:
                    return result
            return ActionResult(False, ActionStrategy.KEYBOARD, "Click recovery: no clickable targets found")
        elif recovery_type == "scroll":
            logger.info("[RECOVERY] Trying scroll-based recovery")
            try:
                import pyautogui
                pyautogui.scroll(-300)  # Scroll down
                time.sleep(0.5)
                pyautogui.scroll(300)  # Scroll back up
                time.sleep(0.5)
                return ActionResult(True, ActionStrategy.KEYBOARD, "Scrolled to refresh view")
            except Exception as e:
                return ActionResult(False, ActionStrategy.KEYBOARD, f"Scroll recovery failed: {e}")
        elif recovery_type == "refocus":
            logger.info("[RECOVERY] Trying refocus Chrome")
            try:
                if hasattr(self.router, "executor") and hasattr(self.router.executor, "_focus_chrome_window"):
                    if self.router.executor._focus_chrome_window():
                        time.sleep(0.5)
                        return ActionResult(True, ActionStrategy.KEYBOARD, "Chrome refocused")
                return ActionResult(False, ActionStrategy.KEYBOARD, "Refocus recovery: Chrome focus failed")
            except Exception as e:
                return ActionResult(False, ActionStrategy.KEYBOARD, f"Refocus recovery failed: {e}")
        else:
            return ActionResult(False, ActionStrategy.KEYBOARD, f"Unknown recovery type: {recovery_type}")

    def execute_flow(
        self,
        destination_path: Path,
        on_step: Optional[callable] = None
    ) -> Tuple[bool, str]:
        """
        Execute the complete OAuth client creation flow.

        Args:
            destination_path: Where to save downloaded credentials.json
            on_step: Callback for progress updates

        Returns:
            (success, message)
        """
        step_count = 0
        
        # Reset progress tracking at start of flow
        self._nav_attempts_to_credentials = 0

        # Start download watcher
        self.router.download_watcher.start_watching()

        while step_count < self.max_steps:
            step_count += 1

            # Take screenshot
            screenshot_path = self.router.take_screenshot(f"oauth_flow_step_{step_count}")
            if not screenshot_path:
                return False, "Failed to take screenshot"

            # NOTE: Removed separate stall detection - now handled by
            # state transition verification in action execution

            # Detect current state
            self.current_state = self.detect_state(screenshot_path)
            logger.info(f"Step {step_count}: State = {self.current_state.value}")

            if on_step:
                on_step({
                    "step": step_count,
                    "state": self.current_state.value,
                    "screenshot": str(screenshot_path),
                })

            # Check if done
            if self.current_state == GoogleConsoleState.DONE:
                return True, "OAuth client created successfully"

            # Get next actions
            actions = self.next_action(self.current_state)
            if not actions:
                if self.current_state == GoogleConsoleState.UNKNOWN:
                    # Try recovery (but NOT navigation if already attempted)
                    if self._nav_attempts_to_credentials >= 1:
                        logger.info("[RECOVERY] Switching strategy (no navigation)")
                        recovery_type = "click"
                    else:
                        recovery_type = "navigate"
                    result = self.recover(recovery_type=recovery_type)
                    if not result.success:
                        return False, f"Unknown state and recovery failed: {result.message}"
                    continue
                else:
                    return False, f"No actions defined for state: {self.current_state.value}"

            # Execute actions
            for action in actions:
                action_type = action["type"]
                logger.info(f"  Action: {action['description']}")

                # ============================================================
                # PRECONDITION CHECK
                # Verify action can succeed before attempting
                # ============================================================
                precond_ok, precond_msg = self._check_precondition(action, screenshot_path)
                if not precond_ok:
                    logger.warning(f"[PRECONDITION FAILED] {precond_msg}")
                    result = ActionResult(False, ActionStrategy.KEYBOARD, f"Precondition failed: {precond_msg}")

                    # Don't immediately fail - try recovery
                    logger.info("[REPLAN] Precondition failed, will try recovery")
                    break  # Exit action loop, go to next state detection

                if action_type == "click_menu_item":
                    # Click menu item from dropdown (no Ctrl+F, no typing)
                    logger.info("[FLOW] Create credentials menu detected")
                    time.sleep(0.3)  # Short wait for menu to be fully visible
                    # Take fresh screenshot with menu visible
                    menu_screenshot = self.router.take_screenshot(f"step_{step_count}_menu_visible")
                    if not menu_screenshot:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot of menu")
                    else:
                        logger.info(f"[FLOW] Clicking menu item: {action['target']}")
                        result = self.router.click(
                            target=action["target"],
                            screenshot_path=menu_screenshot,
                            step_id=f"step_{step_count}_menu_item_{action['target']}"
                        )

                elif action_type == "ctrl_f_click":
                    # Use Ctrl+F to locate and click (completes full action)
                    result = self._click_via_ctrl_f(
                        action["target"],
                        step_id=f"step_{step_count}_ctrl_f_{action['target'].replace(' ', '_')}"
                    )

                elif action_type == "click":
                    result = self.router.click(
                        target=action["target"],
                        screenshot_path=screenshot_path,
                        step_id=f"step_{step_count}_{action['target']}"
                    )

                elif action_type == "check_credentials_page_state":
                    # Check if we need to configure consent screen or create OAuth client
                    try:
                        import pytesseract
                        from PIL import Image
                        img = Image.open(screenshot_path)
                        ocr_text = pytesseract.image_to_string(img).lower()
                        
                        # Check for "Configure consent screen" banner
                        if "configure consent screen" in ocr_text or "configure oauth consent" in ocr_text:
                            logger.info("[FLOW] Credentials page has consent screen banner, clicking it")
                            # Use Ctrl+F to locate and click (completes full action)
                            result = self._click_via_ctrl_f(
                                "Configure consent screen",
                                step_id=f"step_{step_count}_consent_click"
                            )
                        else:
                            # No banner, ready to create OAuth client
                            logger.info("[FLOW] Credentials page ready, creating OAuth client")
                            # Use Ctrl+F to locate and click (completes full action)
                            result = self._click_via_ctrl_f(
                                "Create credentials",
                                step_id=f"step_{step_count}_create_click"
                            )
                            if result.success:
                                time.sleep(1.0)
                                # Take fresh screenshot after menu opens
                                screenshot2 = self.router.take_screenshot(f"step_{step_count}_menu_open")
                                if not screenshot2:
                                    result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot after Create credentials")
                                else:
                                    # Select OAuth client ID (menu item, not search)
                                    logger.info(f"[FLOW] Clicking: OAuth client ID using fresh screenshot: {screenshot2}")
                                    oauth_result = self.router.click(
                                        target="OAuth client ID",
                                        screenshot_path=screenshot2,
                                        step_id=f"step_{step_count}_oauth_client_id"
                                    )
                                    if oauth_result.success:
                                        time.sleep(1.5)
                                        # Take fresh screenshot after OAuth client ID selected
                                        screenshot3 = self.router.take_screenshot(f"step_{step_count}_oauth_form")
                                        if not screenshot3:
                                            result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot after OAuth client ID")
                                        else:
                                            # Choose Desktop app
                                            logger.info(f"[FLOW] Clicking: Desktop app using fresh screenshot: {screenshot3}")
                                            desktop_result = self.router.click(
                                                target="Desktop app",
                                                screenshot_path=screenshot3,
                                                step_id=f"step_{step_count}_desktop_app"
                                            )
                                            if desktop_result.success:
                                                time.sleep(0.5)
                                                # Take fresh screenshot before CREATE
                                                screenshot4 = self.router.take_screenshot(f"step_{step_count}_before_create")
                                                if not screenshot4:
                                                    result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot before CREATE")
                                                else:
                                                    # Create
                                                    logger.info(f"[FLOW] Clicking: CREATE using fresh screenshot: {screenshot4}")
                                                    create_result = self.router.click(
                                                        target="CREATE",
                                                        screenshot_path=screenshot4,
                                                        step_id=f"step_{step_count}_create"
                                                    )
                                                    result = create_result
                                            else:
                                                result = desktop_result
                                    else:
                                        result = oauth_result
                    except Exception as e:
                        logger.warning(f"Failed to check credentials page state: {e}")
                        result = ActionResult(True, ActionStrategy.KEYBOARD, "Could not verify page state, continuing")

                elif action_type == "fill_oauth_form":
                    # Fill OAuth client form with fresh screenshots after each click
                    logger.info("[FLOW] OAuth client form detected")
                    
                    # Step a: Take fresh screenshot
                    form_screenshot1 = self.router.take_screenshot(f"step_{step_count}_oauth_form_initial")
                    if not form_screenshot1:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot of OAuth form")
                    else:
                        # Step b: Click "Application type"
                        logger.info("[FLOW] Selecting Application type: Desktop app")
                        app_type_result = self.router.click(
                            target="Application type",
                            screenshot_path=form_screenshot1,
                            step_id=f"step_{step_count}_application_type"
                        )
                        if not app_type_result.success:
                            result = app_type_result
                        else:
                            time.sleep(0.5)
                            # Step c: Take fresh screenshot
                            form_screenshot2 = self.router.take_screenshot(f"step_{step_count}_oauth_form_after_app_type")
                            if not form_screenshot2:
                                result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot after Application type")
                            else:
                                # Step d: Click "Desktop app"
                                desktop_result = self.router.click(
                                    target="Desktop app",
                                    screenshot_path=form_screenshot2,
                                    step_id=f"step_{step_count}_desktop_app"
                                )
                                if not desktop_result.success:
                                    result = desktop_result
                                else:
                                    time.sleep(0.5)
                                    # Step e: Take fresh screenshot
                                    form_screenshot3 = self.router.take_screenshot(f"step_{step_count}_oauth_form_after_desktop")
                                    if not form_screenshot3:
                                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot after Desktop app")
                                    else:
                                        # Step f: Click "Create"
                                        create_result = self.router.click(
                                            target="CREATE",
                                            screenshot_path=form_screenshot3,
                                            step_id=f"step_{step_count}_create_oauth_client"
                                        )
                                        if create_result.success:
                                            logger.info("[FLOW] OAuth client created")
                                            time.sleep(1.0)
                                            # Take fresh screenshot after Create to detect modal
                                            modal_screenshot = self.router.take_screenshot(f"step_{step_count}_after_create")
                                            if modal_screenshot:
                                                # Next iteration will detect CLIENT_CREATED_MODAL
                                                result = ActionResult(True, ActionStrategy.KEYBOARD, "OAuth client created, waiting for modal")
                                            else:
                                                result = create_result
                                        else:
                                            result = create_result

                elif action_type == "click_application_type":
                    # OAUTH_TYPE_FORM: Click "Application type"
                    logger.info("[FLOW] OAuth client form detected")
                    form_screenshot = self.router.take_screenshot(f"step_{step_count}_oauth_type_form")
                    if not form_screenshot:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot of OAuth type form")
                    else:
                        result = self.router.click(
                            target="Application type",
                            screenshot_path=form_screenshot,
                            step_id=f"step_{step_count}_application_type"
                        )
                        if result.success:
                            time.sleep(0.5)
                            # Take fresh screenshot after click
                            self.router.take_screenshot(f"step_{step_count}_after_app_type_click")

                elif action_type == "click_desktop_app":
                    # OAUTH_TYPE_DROPDOWN_OPEN: Click "Desktop app"
                    logger.info("[FLOW] Selecting Application type: Desktop app")
                    dropdown_screenshot = self.router.take_screenshot(f"step_{step_count}_oauth_dropdown")
                    if not dropdown_screenshot:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot of dropdown")
                    else:
                        result = self.router.click(
                            target="Desktop app",
                            screenshot_path=dropdown_screenshot,
                            step_id=f"step_{step_count}_desktop_app"
                        )
                        if result.success:
                            time.sleep(0.5)
                            # Take fresh screenshot after click
                            self.router.take_screenshot(f"step_{step_count}_after_desktop_app_click")

                elif action_type == "click_create_button":
                    # OAUTH_NAME_FORM: Click "Create"
                    name_form_screenshot = self.router.take_screenshot(f"step_{step_count}_oauth_name_form")
                    if not name_form_screenshot:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot of name form")
                    else:
                        result = self.router.click(
                            target="CREATE",
                            screenshot_path=name_form_screenshot,
                            step_id=f"step_{step_count}_create_oauth_client"
                        )
                        if result.success:
                            logger.info("[FLOW] OAuth client created")
                            time.sleep(1.0)
                            # Take fresh screenshot after Create to detect modal
                            self.router.take_screenshot(f"step_{step_count}_after_create")

                elif action_type == "click_download_json":
                    # OAUTH_CREATED_MODAL: Click "Download JSON" and start download watcher
                    logger.info("[FLOW] Downloading credentials JSON")
                    modal_screenshot = self.router.take_screenshot(f"step_{step_count}_oauth_modal")
                    if not modal_screenshot:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Failed to take screenshot of modal")
                    else:
                        result = self.router.click(
                            target=action.get("target", "Download JSON"),
                            screenshot_path=modal_screenshot,
                            step_id=f"step_{step_count}_download_json"
                        )
                        if result.success:
                            # Start download watcher if not already started
                            if hasattr(self.router.download_watcher, 'start_watching'):
                                self.router.download_watcher.start_watching()
                            # Mark download as initiated
                            self._download_initiated = True
                            # Transition to DOWNLOAD_INITIATED will happen on next iteration

                elif action_type == "wait_for_download":
                    # DOWNLOAD_INITIATED: Wait for file (no clicks)
                    downloaded_file = self.router.download_watcher.wait_for_download(
                        pattern="client_secret*.json",
                        timeout=30.0
                    )
                    if downloaded_file:
                        # Transition to DOWNLOAD_COMPLETE will happen on next iteration
                        result = ActionResult(True, ActionStrategy.KEYBOARD, f"Download detected: {downloaded_file}")
                    else:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "Download timeout: client_secret*.json not found")

                elif action_type == "move_and_verify_json":
                    # DOWNLOAD_COMPLETE: Move file and verify JSON
                    # Find the downloaded file
                    import glob
                    download_dir = self.router.download_watcher.download_dir
                    pattern = str(download_dir / "client_secret*.json")
                    files = glob.glob(pattern)
                    if not files:
                        result = ActionResult(False, ActionStrategy.KEYBOARD, "No downloaded file found")
                    else:
                        # Get the newest file
                        newest = max(files, key=lambda p: Path(p).stat().st_mtime)
                        downloaded_file = Path(newest)
                        # Move and verify
                        move_ok, move_msg = self.router.download_watcher.move_and_verify(
                            downloaded_file,
                            destination_path,
                            required_keys=["client_id", "client_secret", "redirect_uris"]
                        )
                        if not move_ok:
                            result = ActionResult(False, ActionStrategy.KEYBOARD, f"Download verification failed: {move_msg}")
                        else:
                            logger.info("[FLOW] OAuth credentials ready")
                            # Mark as done
                            self.current_state = GoogleConsoleState.DONE
                            result = ActionResult(True, ActionStrategy.KEYBOARD, f"OAuth credentials saved to {destination_path}")
                            
                            # Promote to learned procedure
                            try:
                                from agent.memory.unified_memory import get_memory
                                memory = get_memory()
                                steps = [
                                    "Navigate to Credentials page",
                                    "Configure consent screen if required",
                                    "Create OAuth client (Desktop app)",
                                    "Download credentials.json"
                                ]
                                # Store procedure with metadata
                                store = memory._get_store()
                                content = f"Procedure: create_google_calendar_oauth_desktop\nDescription: Automated OAuth client creation for Google Calendar desktop app credentials\nSteps:\n"
                                content += "\n".join(f"  {i+1}. {step}" for i, step in enumerate(steps))
                                metadata = {
                                    "type": "procedure",
                                    "version": 1,
                                    "step_count": len(steps),
                                    "entry_conditions": ["intent.service == 'google_calendar'", "credentials.json missing"],
                                    "success_conditions": ["credentials.json exists", "JSON contains client_id, client_secret, redirect_uris"],
                                    "timestamp": datetime.now().isoformat(),
                                }
                                store.upsert(
                                    kind="procedure",
                                    content=content,
                                    key="procedure:create_google_calendar_oauth_desktop",
                                    metadata=metadata,
                                )
                                logger.info("[LEARNED] Promoted procedure: create_google_calendar_oauth_desktop v1")
                            except Exception as e:
                                logger.debug(f"Could not store procedure: {e}")

                elif action_type == "check_consent_complete":
                    # Check if consent screen shows completion indicators
                    try:
                        import pytesseract
                        from PIL import Image
                        img = Image.open(screenshot_path)
                        ocr_text = pytesseract.image_to_string(img).lower()
                        
                        # If consent screen is completed, navigate to credentials and create OAuth client
                        if "test users" in ocr_text or "publish app" in ocr_text:
                            logger.info("[FLOW] Consent screen completed, returning to credentials page")
                            # Use prepare_and_navigate_chrome if available, otherwise navigate_to_url
                            if hasattr(self.router, "prepare_and_navigate_chrome"):
                                # This would require router to have executor access, use navigate_to_url for now
                                nav_result = self.router.navigate_to_url(GOOGLE_CONSOLE_URLS["credentials"])
                            else:
                                nav_result = self.router.navigate_to_url(GOOGLE_CONSOLE_URLS["credentials"])
                            if not nav_result.success:
                                result = ActionResult(False, ActionStrategy.KEYBOARD, f"Failed to navigate: {nav_result.message}")
                            else:
                                time.sleep(2.0)
                                # Next iteration will detect CREDENTIALS_PAGE and create OAuth client
                                result = ActionResult(True, ActionStrategy.KEYBOARD, "Consent screen completed, ready to create OAuth client")
                        else:
                            # Consent screen not completed yet, continue with setup
                            result = ActionResult(True, ActionStrategy.KEYBOARD, "Consent screen setup in progress")
                    except Exception as e:
                        logger.warning(f"Failed to check consent completion: {e}")
                        result = ActionResult(True, ActionStrategy.KEYBOARD, "Could not verify consent completion, continuing")

                elif action_type == "download_json":
                    # Click download button
                    logger.info("[FLOW] Downloading credentials JSON")
                    result = self.router.click(
                        target=action["target"],
                        screenshot_path=screenshot_path,
                        step_id=f"step_{step_count}_download"
                    )

                    if result.success:
                        # Wait for download
                        downloaded_file = self.router.download_watcher.wait_for_download(
                            pattern="client_secret*.json",
                            timeout=30.0
                        )

                        if not downloaded_file:
                            return False, "Download timeout: client_secret*.json not found"

                        # Move and verify
                        move_ok, move_msg = self.router.download_watcher.move_and_verify(
                            downloaded_file,
                            destination_path,
                            required_keys=["client_id", "client_secret"]
                        )

                        if not move_ok:
                            return False, f"Download verification failed: {move_msg}"

                        # Mark as done
                        self.current_state = GoogleConsoleState.DONE
                        return True, f"OAuth credentials saved to {destination_path}"

                elif action_type == "recover":
                    result = self.recover()

                else:
                    return False, f"Unknown action type: {action_type}"

                # Log result
                logger.info(f"    Result: {result.message} (strategy: {result.strategy.value})")

                # ============================================================
                # STOP-THINK-REPLAN PATTERN
                # ============================================================
                if not result.success:
                    # STOP: Action failed - don't continue blindly
                    logger.warning(f"    Action failed: {result.message}")

                    # THINK: Reflect on why it failed
                    reflection = self._reflect_on_action_failure(
                        action=action,
                        error=result.message,
                        screenshot_path=screenshot_path,
                        step_count=step_count
                    )

                    # Track failure count for this action type
                    failure_key = f"{action_type}_{step_count}"
                    if not hasattr(self, '_action_failures'):
                        self._action_failures = {}
                    self._action_failures[failure_key] = self._action_failures.get(failure_key, 0) + 1

                    # ESCALATE: If failed 2+ times on same action, escalate
                    if self._action_failures[failure_key] >= 2:
                        logger.error("[ESCALATE] Action failed multiple times; asking user for manual help")
                        return False, (
                            f"I'm stuck on the Google Cloud Console.\n"
                            f"Action '{action.get('description', action_type)}' failed:\n"
                            f"{result.message}\n\n"
                            f"Reflection:\n{reflection}\n\n"
                            f"Please complete this step manually, then press Enter here."
                        )

                    # REPLAN: Try recovery or break to next iteration
                    logger.info("[REPLAN] Will try recovery on next iteration")
                    break  # Exit action loop, go to next state detection
                else:
                    # Success - verify state changed for critical actions
                    if action_type in ["ctrl_f_click", "click", "click_menu_item", "click_create_button"]:
                        time.sleep(0.5)  # Brief wait for state to update
                        verify_screenshot = self.router.take_screenshot(f"step_{step_count}_verify")
                        if verify_screenshot:
                            state_changed, new_state, msg = self._verify_state_changed(
                                before_state=self.current_state,
                                after_screenshot=verify_screenshot,
                                action_description=action.get("description", action_type)
                            )

                            if not state_changed and self.current_state not in [GoogleConsoleState.UNKNOWN, GoogleConsoleState.ERROR]:
                                # Click succeeded but state didn't change - treat as failure
                                logger.warning(f"[PROGRESS] {msg}")
                                reflection = self._reflect_on_action_failure(
                                    action=action,
                                    error=msg,
                                    screenshot_path=verify_screenshot,
                                    step_count=step_count
                                )

                                # Increment failure count
                                failure_key = f"{action_type}_{step_count}"
                                if not hasattr(self, '_action_failures'):
                                    self._action_failures = {}
                                self._action_failures[failure_key] = self._action_failures.get(failure_key, 0) + 1

                                # Escalate if 2+ state-unchanged failures
                                if self._action_failures[failure_key] >= 2:
                                    logger.error("[ESCALATE] State not changing; asking user for help")
                                    return False, (
                                        f"I'm stuck - the page isn't responding to clicks.\n"
                                        f"{reflection}\n"
                                        f"Please help complete this step manually."
                                    )

                                # Try recovery
                                break

                # Wait after action
                time.sleep(action.get("wait_after", 0.5))

        return False, f"Max steps ({self.max_steps}) reached without completion"


def create_oauth_credentials(
    destination_path: Path,
    on_step: Optional[callable] = None
) -> Tuple[bool, str]:
    """
    Create OAuth credentials through Google Console.

    High-level entrypoint for the OAuth setup flow.

    Args:
        destination_path: Where to save credentials.json
        on_step: Optional callback for progress updates

    Returns:
        (success, message)
    """
    router = get_computer_use_router()
    ok, msg = router.initialize()
    if not ok:
        return False, f"Router initialization failed: {msg}"

    state_machine = GoogleConsoleStateMachine(router)

    # Navigate to credentials page to start
    logger.info("Starting OAuth credentials creation flow")
    result = router.navigate_to_url(GOOGLE_CONSOLE_URLS["credentials"])
    if not result.success:
        return False, f"Failed to navigate to credentials page: {result.message}"

    time.sleep(2.0)  # Wait for page load

    # Execute flow
    return state_machine.execute_flow(destination_path, on_step=on_step)


__all__ = [
    "GoogleConsoleStateMachine",
    "create_oauth_credentials",
    "GOOGLE_CONSOLE_URLS",
]
