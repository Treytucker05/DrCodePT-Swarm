"""
Windows UI Automation Module

Provides accurate, deterministic UI control using Windows Accessibility APIs.
This is MUCH more reliable than pixel-based vision clicking.

Key advantages:
- Click elements by NAME, not guessed coordinates
- Read actual UI state (text, enabled, focused)
- Works regardless of DPI, theme, or window position
- Fast (milliseconds vs seconds for vision)

Vision is kept as a FALLBACK for when UI tree doesn't help.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable

logger = logging.getLogger(__name__)

# Try to import UI automation libraries
_HAS_PYWINAUTO = False
_HAS_UIAUTOMATION = False

try:
    import pywinauto
    from pywinauto import Desktop, Application
    from pywinauto.findwindows import ElementNotFoundError
    _HAS_PYWINAUTO = True
except ImportError:
    logger.warning("pywinauto not available")

try:
    import uiautomation as auto
    _HAS_UIAUTOMATION = True
except ImportError:
    logger.warning("uiautomation not available")


@dataclass
class UIElement:
    """Represents a UI element found in the automation tree."""
    name: str
    control_type: str
    automation_id: str = ""
    class_name: str = ""
    is_enabled: bool = True
    is_visible: bool = True
    bounding_box: Tuple[int, int, int, int] = (0, 0, 0, 0)  # left, top, right, bottom
    value: str = ""
    children_count: int = 0
    _raw: Any = None  # The underlying automation element

    @property
    def center(self) -> Tuple[int, int]:
        """Get the center point of this element."""
        left, top, right, bottom = self.bounding_box
        return ((left + right) // 2, (top + bottom) // 2)

    def click(self) -> bool:
        """Click this element."""
        if self._raw is None:
            return False
        try:
            if _HAS_UIAUTOMATION and hasattr(self._raw, 'Click'):
                self._raw.Click()
                return True
            elif _HAS_PYWINAUTO and hasattr(self._raw, 'click_input'):
                self._raw.click_input()
                return True
            # Fallback to coordinate click
            import pyautogui
            x, y = self.center
            pyautogui.click(x, y)
            return True
        except Exception as e:
            logger.error(f"Failed to click element {self.name}: {e}")
            return False

    def type_text(self, text: str) -> bool:
        """Type text into this element."""
        if self._raw is None:
            return False
        try:
            if _HAS_UIAUTOMATION and hasattr(self._raw, 'SendKeys'):
                self._raw.SendKeys(text)
                return True
            elif _HAS_PYWINAUTO and hasattr(self._raw, 'type_keys'):
                self._raw.type_keys(text, with_spaces=True)
                return True
            # Fallback
            self.click()
            time.sleep(0.1)
            import pyautogui
            pyautogui.write(text)
            return True
        except Exception as e:
            logger.error(f"Failed to type into element {self.name}: {e}")
            return False


@dataclass
class WindowInfo:
    """Information about a window."""
    title: str
    handle: int
    class_name: str
    is_visible: bool
    is_enabled: bool
    bounding_box: Tuple[int, int, int, int]
    process_id: int = 0
    _raw: Any = None


class WindowsUIController:
    """
    Controls Windows UI using accessibility APIs.

    This is the PREFERRED method for UI automation because:
    1. It's deterministic - no guessing coordinates
    2. It's fast - no LLM calls needed to find elements
    3. It's robust - works regardless of visual changes

    Usage:
        controller = WindowsUIController()

        # Find and click a button by name
        button = controller.find_element(name="APIs & Services")
        if button:
            button.click()

        # Or use the high-level API
        controller.click_element(name="Enable API")
    """

    def __init__(self):
        self._initialized = False
        self._active_window: Optional[WindowInfo] = None

    def initialize(self) -> Tuple[bool, str]:
        """Initialize the controller."""
        if not _HAS_PYWINAUTO and not _HAS_UIAUTOMATION:
            return False, "No UI automation library available. Install pywinauto or uiautomation."
        self._initialized = True
        return True, "UI controller initialized"

    def get_active_window(self) -> Optional[WindowInfo]:
        """Get information about the currently active window."""
        try:
            if _HAS_UIAUTOMATION:
                win = auto.GetForegroundControl()
                if win:
                    rect = win.BoundingRectangle
                    return WindowInfo(
                        title=win.Name or "",
                        handle=win.NativeWindowHandle,
                        class_name=win.ClassName or "",
                        is_visible=True,
                        is_enabled=win.IsEnabled,
                        bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                        _raw=win,
                    )
            elif _HAS_PYWINAUTO:
                desktop = Desktop(backend="uia")
                windows = desktop.windows()
                for win in windows:
                    if win.has_focus():
                        rect = win.rectangle()
                        return WindowInfo(
                            title=win.window_text(),
                            handle=win.handle,
                            class_name=win.class_name(),
                            is_visible=win.is_visible(),
                            is_enabled=win.is_enabled(),
                            bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                            _raw=win,
                        )
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
        return None

    def find_window(self, title_contains: str = None, class_name: str = None) -> Optional[WindowInfo]:
        """Find a window by title or class name."""
        try:
            if _HAS_UIAUTOMATION:
                if title_contains:
                    win = auto.WindowControl(searchDepth=1, SubName=title_contains)
                elif class_name:
                    win = auto.WindowControl(searchDepth=1, ClassName=class_name)
                else:
                    return None

                if win.Exists(maxSearchSeconds=2):
                    rect = win.BoundingRectangle
                    return WindowInfo(
                        title=win.Name or "",
                        handle=win.NativeWindowHandle,
                        class_name=win.ClassName or "",
                        is_visible=True,
                        is_enabled=win.IsEnabled,
                        bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                        _raw=win,
                    )
            elif _HAS_PYWINAUTO:
                desktop = Desktop(backend="uia")
                for win in desktop.windows():
                    win_title = win.window_text()
                    win_class = win.class_name()
                    if title_contains and title_contains.lower() in win_title.lower():
                        rect = win.rectangle()
                        return WindowInfo(
                            title=win_title,
                            handle=win.handle,
                            class_name=win_class,
                            is_visible=win.is_visible(),
                            is_enabled=win.is_enabled(),
                            bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                            _raw=win,
                        )
                    if class_name and class_name.lower() in win_class.lower():
                        rect = win.rectangle()
                        return WindowInfo(
                            title=win_title,
                            handle=win.handle,
                            class_name=win_class,
                            is_visible=win.is_visible(),
                            is_enabled=win.is_enabled(),
                            bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                            _raw=win,
                        )
        except Exception as e:
            logger.error(f"Failed to find window: {e}")
        return None

    def find_element(
        self,
        name: str = None,
        control_type: str = None,
        automation_id: str = None,
        class_name: str = None,
        window: WindowInfo = None,
        timeout: float = 5.0,
    ) -> Optional[UIElement]:
        """
        Find a UI element by various criteria.

        Args:
            name: Element name/text to search for (partial match)
            control_type: Type like "Button", "Edit", "Link", "MenuItem"
            automation_id: Unique automation ID
            class_name: CSS/window class name
            window: Window to search in (uses active window if None)
            timeout: Max seconds to wait for element

        Returns:
            UIElement if found, None otherwise
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if _HAS_UIAUTOMATION:
                    return self._find_element_uiautomation(
                        name, control_type, automation_id, class_name, window
                    )
                elif _HAS_PYWINAUTO:
                    return self._find_element_pywinauto(
                        name, control_type, automation_id, class_name, window
                    )
            except Exception as e:
                logger.debug(f"Element search attempt failed: {e}")
            time.sleep(0.2)

        return None

    def _find_element_uiautomation(
        self, name, control_type, automation_id, class_name, window
    ) -> Optional[UIElement]:
        """Find element using uiautomation library."""
        search_from = window._raw if window and window._raw else auto.GetForegroundControl()

        if not search_from:
            return None

        # Build search criteria
        search_kwargs = {"searchDepth": 10}
        if name:
            search_kwargs["SubName"] = name
        if control_type:
            search_kwargs["ControlType"] = getattr(auto.ControlType, control_type + "Control", None)
        if automation_id:
            search_kwargs["AutomationId"] = automation_id
        if class_name:
            search_kwargs["ClassName"] = class_name

        # Search for element
        element = search_from.Control(**search_kwargs)

        if element and element.Exists(maxSearchSeconds=1):
            rect = element.BoundingRectangle
            return UIElement(
                name=element.Name or "",
                control_type=str(element.ControlTypeName or ""),
                automation_id=element.AutomationId or "",
                class_name=element.ClassName or "",
                is_enabled=element.IsEnabled,
                is_visible=True,
                bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                value=getattr(element, 'CurrentValue', '') or "",
                _raw=element,
            )
        return None

    def _find_element_pywinauto(
        self, name, control_type, automation_id, class_name, window
    ) -> Optional[UIElement]:
        """Find element using pywinauto library."""
        search_from = window._raw if window and window._raw else Desktop(backend="uia").windows()[0]

        if not search_from:
            return None

        # Build search criteria
        search_kwargs = {}
        if name:
            search_kwargs["title_re"] = f".*{name}.*"
        if control_type:
            search_kwargs["control_type"] = control_type
        if automation_id:
            search_kwargs["auto_id"] = automation_id
        if class_name:
            search_kwargs["class_name"] = class_name

        try:
            # Use descendants to search deeply
            elements = search_from.descendants(**search_kwargs)
            if elements:
                elem = elements[0]
                rect = elem.rectangle()
                return UIElement(
                    name=elem.window_text() or "",
                    control_type=elem.element_info.control_type or "",
                    automation_id=elem.element_info.automation_id or "",
                    class_name=elem.class_name() or "",
                    is_enabled=elem.is_enabled(),
                    is_visible=elem.is_visible(),
                    bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                    _raw=elem,
                )
        except ElementNotFoundError:
            pass
        return None

    def find_all_elements(
        self,
        control_type: str = None,
        window: WindowInfo = None,
        max_depth: int = 5,
    ) -> List[UIElement]:
        """
        Find all UI elements of a certain type.

        Useful for:
        - Listing all buttons on a page
        - Finding all links
        - Getting form fields
        """
        elements = []
        try:
            if _HAS_UIAUTOMATION:
                search_from = window._raw if window and window._raw else auto.GetForegroundControl()
                if search_from:
                    for elem in search_from.GetChildren():
                        self._collect_elements(elem, elements, control_type, max_depth, 0)
        except Exception as e:
            logger.error(f"Failed to enumerate elements: {e}")
        return elements

    def _collect_elements(self, elem, results: List[UIElement], control_type: str, max_depth: int, depth: int):
        """Recursively collect elements."""
        if depth > max_depth:
            return

        try:
            type_name = str(elem.ControlTypeName or "")
            if control_type is None or control_type.lower() in type_name.lower():
                rect = elem.BoundingRectangle
                results.append(UIElement(
                    name=elem.Name or "",
                    control_type=type_name,
                    automation_id=elem.AutomationId or "",
                    is_enabled=elem.IsEnabled,
                    bounding_box=(rect.left, rect.top, rect.right, rect.bottom),
                    _raw=elem,
                ))

            for child in elem.GetChildren():
                self._collect_elements(child, results, control_type, max_depth, depth + 1)
        except Exception:
            pass

    def click_element(
        self,
        name: str = None,
        control_type: str = None,
        automation_id: str = None,
        timeout: float = 5.0,
    ) -> Tuple[bool, str]:
        """
        High-level API: Find and click an element.

        Returns (success, message)
        """
        element = self.find_element(
            name=name,
            control_type=control_type,
            automation_id=automation_id,
            timeout=timeout,
        )

        if not element:
            return False, f"Element not found: name={name}, type={control_type}"

        if element.click():
            return True, f"Clicked: {element.name} ({element.control_type})"
        else:
            return False, f"Failed to click: {element.name}"

    def type_into_element(
        self,
        text: str,
        name: str = None,
        control_type: str = "Edit",
        automation_id: str = None,
        timeout: float = 5.0,
    ) -> Tuple[bool, str]:
        """
        High-level API: Find an input field and type into it.
        """
        element = self.find_element(
            name=name,
            control_type=control_type,
            automation_id=automation_id,
            timeout=timeout,
        )

        if not element:
            return False, f"Input field not found: name={name}"

        if element.type_text(text):
            return True, f"Typed '{text[:20]}...' into {element.name}"
        else:
            return False, f"Failed to type into: {element.name}"

    def get_element_tree(self, window: WindowInfo = None, max_depth: int = 3) -> Dict[str, Any]:
        """
        Get a simplified tree of UI elements.

        This is useful for:
        - Debugging what elements are visible
        - Passing to LLM for decision making (text, not vision!)
        """
        result = {"elements": []}
        try:
            if _HAS_UIAUTOMATION:
                root = window._raw if window and window._raw else auto.GetForegroundControl()
                if root:
                    result["window_title"] = root.Name or ""
                    self._build_tree(root, result["elements"], max_depth, 0)
        except Exception as e:
            logger.error(f"Failed to build element tree: {e}")
        return result

    def _build_tree(self, elem, results: List, max_depth: int, depth: int):
        """Build element tree recursively."""
        if depth > max_depth:
            return

        try:
            name = elem.Name or ""
            control_type = str(elem.ControlTypeName or "")

            # Only include meaningful elements
            if name or control_type in ["Button", "Link", "Edit", "MenuItem", "TabItem", "ListItem"]:
                rect = elem.BoundingRectangle
                results.append({
                    "name": name,
                    "type": control_type,
                    "enabled": elem.IsEnabled,
                    "bounds": [rect.left, rect.top, rect.right, rect.bottom],
                })

            for child in elem.GetChildren():
                self._build_tree(child, results, max_depth, depth + 1)
        except Exception:
            pass

    def wait_for_element(
        self,
        name: str = None,
        control_type: str = None,
        timeout: float = 30.0,
        poll_interval: float = 0.5,
    ) -> Optional[UIElement]:
        """
        Wait for an element to appear.

        Useful for waiting for pages to load or dialogs to appear.
        """
        start = time.time()
        while time.time() - start < timeout:
            elem = self.find_element(name=name, control_type=control_type, timeout=0.1)
            if elem:
                return elem
            time.sleep(poll_interval)
        return None

    def focus_window(self, window: WindowInfo) -> bool:
        """Bring a window to the foreground."""
        try:
            if window._raw:
                if _HAS_UIAUTOMATION and hasattr(window._raw, 'SetFocus'):
                    window._raw.SetFocus()
                    return True
                elif _HAS_PYWINAUTO and hasattr(window._raw, 'set_focus'):
                    window._raw.set_focus()
                    return True
        except Exception as e:
            logger.error(f"Failed to focus window: {e}")
        return False


# Singleton instance
_controller: Optional[WindowsUIController] = None


def get_ui_controller() -> WindowsUIController:
    """Get the singleton UI controller instance."""
    global _controller
    if _controller is None:
        _controller = WindowsUIController()
        _controller.initialize()
    return _controller


__all__ = [
    "WindowsUIController",
    "UIElement",
    "WindowInfo",
    "get_ui_controller",
]
