"""
Google Console OAuth Setup State Machine

Deterministic flow for creating OAuth client credentials.
No free-form planning - uses explicit state detection and action table.
"""
from __future__ import annotations

import json
import logging
import time
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

    def detect_state(self, screenshot_path: Path) -> GoogleConsoleState:
        """
        Detect current state from screenshot using vision LLM.

        Returns the current state in the OAuth setup flow.
        """
        if not self.router.vision_executor:
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

            if not response:
                return GoogleConsoleState.UNKNOWN

            # Parse JSON response
            try:
                data = json.loads(response)
                state_str = data.get("state", "UNKNOWN").upper()
                confidence = float(data.get("confidence", 0.0))

                logger.info(f"State detection: {state_str} (confidence: {confidence:.2f})")
                logger.debug(f"Reasoning: {data.get('reasoning')}")
                logger.debug(f"Key elements: {data.get('key_elements_seen')}")

                # Map string to enum
                try:
                    return GoogleConsoleState[state_str]
                except KeyError:
                    logger.warning(f"Unknown state string: {state_str}")
                    return GoogleConsoleState.UNKNOWN

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse state detection JSON: {e}")
                return GoogleConsoleState.UNKNOWN

        except Exception as e:
            logger.error(f"State detection error: {e}")
            return GoogleConsoleState.UNKNOWN

    def next_action(self, state: GoogleConsoleState) -> List[Dict[str, Any]]:
        """
        Get the next actions for a given state.

        Returns list of actions to execute in order.
        """
        action_table = {
            GoogleConsoleState.CREDENTIALS_PAGE: [
                {
                    "type": "click",
                    "target": "CREATE CREDENTIALS",
                    "description": "Click CREATE CREDENTIALS button",
                    "wait_after": 1.0,
                },
                {
                    "type": "click",
                    "target": "OAuth client ID",
                    "description": "Select OAuth client ID from dropdown",
                    "wait_after": 1.5,
                },
            ],
            GoogleConsoleState.CONSENT_SCREEN: [
                {
                    "type": "click",
                    "target": "Internal",
                    "description": "Select Internal user type",
                    "wait_after": 0.5,
                },
                {
                    "type": "click",
                    "target": "CREATE",
                    "description": "Click CREATE button",
                    "wait_after": 2.0,
                },
            ],
            GoogleConsoleState.OAUTH_CLIENT_FORM: [
                {
                    "type": "click",
                    "target": "Application type",
                    "description": "Click Application type dropdown",
                    "wait_after": 0.5,
                },
                {
                    "type": "click",
                    "target": "Desktop app",
                    "description": "Select Desktop app",
                    "wait_after": 0.5,
                },
                {
                    "type": "click",
                    "target": "CREATE",
                    "description": "Click CREATE button",
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

    def recover(self) -> ActionResult:
        """Recovery action: navigate to credentials page."""
        logger.info("Executing recovery: navigating to credentials page")
        return self.router.navigate_to_url(GOOGLE_CONSOLE_URLS["credentials"])

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

        # Start download watcher
        self.router.download_watcher.start_watching()

        while step_count < self.max_steps:
            step_count += 1

            # Take screenshot
            screenshot_path = self.router.take_screenshot(f"oauth_flow_step_{step_count}")
            if not screenshot_path:
                return False, "Failed to take screenshot"

            # Check for visual stall
            stalled, msg = self.router.anti_thrash.check_stalled(screenshot_path)
            if stalled:
                logger.warning(f"Visual stall detected: {msg}")
                result = self.recover()
                if not result.success:
                    return False, f"Recovery failed: {result.message}"
                continue

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
                    # Try recovery
                    result = self.recover()
                    if not result.success:
                        return False, f"Unknown state and recovery failed: {result.message}"
                    continue
                else:
                    return False, f"No actions defined for state: {self.current_state.value}"

            # Execute actions
            for action in actions:
                action_type = action["type"]
                logger.info(f"  Action: {action['description']}")

                if action_type == "click":
                    result = self.router.click(
                        target=action["target"],
                        screenshot_path=screenshot_path,
                        step_id=f"step_{step_count}_{action['target']}"
                    )

                elif action_type == "download_json":
                    # Click download button
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

                if not result.success:
                    logger.warning(f"    Action failed, will retry on next iteration")
                    break  # Exit action loop, go to next state detection

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
