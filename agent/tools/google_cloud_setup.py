"""
Google Cloud Project Setup - Desktop Commander Automation.

Uses PyAutoGUI to control the REAL Chrome browser on desktop.
This bypasses Google's Selenium/Playwright detection.

The agent:
1. Opens Chrome browser
2. Navigates to Google Cloud Console
3. Uses vision + mouse/keyboard to interact
4. Creates project, enables APIs, creates OAuth credentials
5. Downloads credentials and completes OAuth flow
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CREDENTIALS_PATH = REPO_ROOT / "agent" / "memory" / "google_credentials.json"
DOWNLOADS_DIR = Path(os.path.expanduser("~/Downloads"))
SCREENSHOTS_DIR = REPO_ROOT / "agent" / "screenshots"
_LAST_CHROME_PID: Optional[int] = None
_LAST_CHROME_HWND: Optional[int] = None
_FOCUS_LOCK: bool = False


def _debug_enabled() -> bool:
    return os.getenv("TREYS_AGENT_GOOGLE_DEBUG", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def _debug_log(message: str) -> None:
    if _debug_enabled():
        print(f"[DEBUG] {message}")


def _debug_foreground(label: str) -> None:
    if not _debug_enabled():
        return
    try:
        import win32gui
    except Exception:
        return
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        _debug_log(f"{label} foreground: '{title}' rect={rect}")
    except Exception:
        pass


def _debug_screen_text(label: str, limit: int = 240) -> None:
    if not _debug_enabled():
        return
    text = _screen_text()
    if not text:
        return
    snippet = " ".join(text.split())
    _debug_log(f"{label} OCR: {snippet[:limit]}")


def _import_pyautogui():
    """Import PyAutoGUI for desktop control."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        return pyautogui, None
    except ImportError as e:
        return None, f"PyAutoGUI not installed: {e}"


def _import_pynput():
    """Import pynput for more reliable mouse control."""
    try:
        from pynput.mouse import Controller, Button
        return Controller, Button, None
    except ImportError as e:
        return None, None, f"pynput not installed: {e}"


def _import_win32api():
    """Import win32api for Windows-native mouse control."""
    try:
        import win32api
        import win32con
        return win32api, win32con, None
    except ImportError as e:
        return None, None, f"pywin32 not installed: {e}"


def _focus_chrome_enabled() -> bool:
    return os.getenv("TREYS_AGENT_GOOGLE_FOCUS_CHROME", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _move_chrome_to_primary_enabled() -> bool:
    return os.getenv("TREYS_AGENT_GOOGLE_MOVE_TO_PRIMARY", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _get_primary_monitor_rect() -> Optional[Tuple[int, int, int, int]]:
    try:
        import win32api
        import win32con
    except Exception:
        return None
    try:
        monitors = win32api.EnumDisplayMonitors()
        for handle, _, _ in monitors:
            info = win32api.GetMonitorInfo(handle)
            if info.get("Flags", 0) & win32con.MONITORINFOF_PRIMARY:
                return info.get("Monitor")
        if monitors:
            info = win32api.GetMonitorInfo(monitors[0][0])
            return info.get("Monitor")
    except Exception:
        return None
    return None


def _get_chrome_user_data_dir() -> Optional[Path]:
    override = os.getenv("TREYS_AGENT_CHROME_USER_DATA_DIR", "").strip()
    if override:
        path = Path(override)
        return path if path.exists() else None
    local = os.getenv("LOCALAPPDATA", "")
    if not local:
        return None
    path = Path(local) / "Google" / "Chrome" / "User Data"
    return path if path.exists() else None


def _iter_chrome_history_paths() -> List[Path]:
    base = _get_chrome_user_data_dir()
    if not base:
        return []
    profile_override = os.getenv("TREYS_AGENT_CHROME_PROFILE", "").strip()
    profiles: List[Path] = []
    if profile_override:
        candidate = base / profile_override
        if candidate.exists():
            profiles.append(candidate)
    else:
        # Prefer Default + Profile * directories
        for name in ["Default", "Profile 1", "Profile 2", "Profile 3", "Guest Profile"]:
            candidate = base / name
            if candidate.exists():
                profiles.append(candidate)
        for entry in base.iterdir():
            if entry.is_dir() and entry.name.startswith("Profile ") and entry not in profiles:
                profiles.append(entry)
    history_paths = []
    for profile in profiles:
        history = profile / "History"
        if history.exists():
            history_paths.append(history)
    return history_paths


def _query_downloads_from_history(history_path: Path) -> List[Tuple[str, Optional[str]]]:
    try:
        import sqlite3
    except Exception:
        return []
    try:
        tmp = Path(tempfile.gettempdir()) / f"chrome_history_{uuid4().hex}.sqlite"
        shutil.copy2(history_path, tmp)
    except Exception:
        tmp = history_path
    rows: List[Tuple[str, Optional[str]]] = []
    try:
        con = sqlite3.connect(str(tmp))
        cur = con.cursor()
        # Try target_path/current_path columns
        cur.execute("PRAGMA table_info(downloads)")
        cols = [r[1] for r in cur.fetchall()]
        path_col = "target_path" if "target_path" in cols else ("current_path" if "current_path" in cols else None)
        if not path_col:
            con.close()
            return rows
        query = (
            f"SELECT {path_col}, start_time FROM downloads ORDER BY start_time DESC LIMIT 50"
        )
        cur.execute(query)
        for path, _ in cur.fetchall():
            if path:
                rows.append((path, None))
        # Try join to URLs
        try:
            cur.execute(
                f"""SELECT d.{path_col}, u.url
                    FROM downloads d
                    LEFT JOIN downloads_url_chains u ON d.id = u.id
                    ORDER BY d.start_time DESC LIMIT 50"""
            )
            for path, url in cur.fetchall():
                if path:
                    rows.append((path, url))
        except Exception:
            pass
        con.close()
    except Exception:
        pass
    try:
        if tmp != history_path and tmp.exists():
            tmp.unlink()
    except Exception:
        pass
    return rows


def _find_downloaded_credentials_via_history() -> Optional[Path]:
    history_paths = _iter_chrome_history_paths()
    for history in history_paths:
        rows = _query_downloads_from_history(history)
        for path, url in rows:
            lower = (path or "").lower()
            url_lower = (url or "").lower()
            if "client_secret" in lower or "oauth" in lower or "googleusercontent" in lower:
                candidate = Path(path)
                if candidate.exists():
                    return candidate
                # Check for in-progress download
                if candidate.with_suffix(candidate.suffix + ".crdownload").exists():
                    return candidate.with_suffix(candidate.suffix + ".crdownload")
                # Sometimes Chrome records a "current_path" that changes; just return it
                if candidate.parent.exists():
                    return candidate
    return None


def _wait_for_downloaded_credentials(timeout_seconds: int = 30) -> Optional[Path]:
    start = time.time()
    seen: set[Path] = set()
    search_dirs = [
        DOWNLOADS_DIR,
        REPO_ROOT / "downloads",
        REPO_ROOT / "evidence" / "downloads",
    ]
    override_dir = os.getenv("TREYS_AGENT_GOOGLE_DOWNLOAD_DIR", "").strip()
    if override_dir:
        search_dirs.insert(0, Path(override_dir))
    for dir_path in search_dirs:
        if dir_path.exists():
            seen.update(dir_path.glob("client_secret*.json"))
    while time.time() - start < timeout_seconds:
        for dir_path in search_dirs:
            if not dir_path.exists():
                continue
            for path in dir_path.glob("client_secret*.json"):
                if path not in seen and path.exists() and path.stat().st_size > 0:
                    return path
        time.sleep(1)
    return None


def _attempt_save_as_dialog() -> bool:
    try:
        import win32gui
        import win32con
    except Exception:
        return False
    targets: List[int] = []

    def _enum(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return
            if "save" in title.lower():
                targets.append(hwnd)
        except Exception:
            return

    try:
        win32gui.EnumWindows(_enum, None)
    except Exception:
        return False
    if not targets:
        return False
    hwnd = targets[0]
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)
        _press_key("enter")
        return True
    except Exception:
        return False


def _recover_downloaded_credentials() -> Optional[Path]:
    # 1) Try save dialog if present
    _attempt_save_as_dialog()
    # 2) Wait for download to appear
    found = _wait_for_downloaded_credentials(timeout_seconds=20)
    if found and found.exists():
        return found
    # 3) Open downloads page and try "Keep"/"Save"
    _navigate_chrome("chrome://downloads")
    time.sleep(1)
    if _autoclick_enabled():
        _auto_click_text(["keep", "keep anyway", "allow", "download", "save"], attempts=2, delay=0.8)
    # 4) Wait again
    found = _wait_for_downloaded_credentials(timeout_seconds=20)
    if found and found.exists():
        return found
    # 5) Check Chrome history
    history_path = _find_downloaded_credentials_via_history()
    if history_path:
        if history_path.suffix.endswith(".crdownload") and history_path.exists():
            # Wait for completion
            for _ in range(15):
                if history_path.exists() and not history_path.name.endswith(".crdownload"):
                    break
                time.sleep(1)
        if history_path.exists():
            return history_path
    return None


def _find_hwnd_by_pid(pid: int) -> Optional[int]:
    try:
        import win32gui
        import win32process
    except Exception:
        return None

    matches: List[int] = []

    def _enum(hwnd, _):
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return
            _, proc_pid = win32process.GetWindowThreadProcessId(hwnd)
            if proc_pid != pid:
                return
            title = win32gui.GetWindowText(hwnd)
            if title:
                matches.append(hwnd)
        except Exception:
            return

    try:
        win32gui.EnumWindows(_enum, None)
    except Exception:
        return None

    if not matches:
        return None
    # Prefer Chrome windows if possible
    for hwnd in matches:
        try:
            title = win32gui.GetWindowText(hwnd).lower()
            if "chrome" in title:
                return hwnd
        except Exception:
            continue
    return matches[0]


def _bring_hwnd_to_front(hwnd: int) -> bool:
    try:
        import win32con
        import win32gui
    except Exception:
        return False
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    except Exception:
        pass
    if _move_chrome_to_primary_enabled():
        rect = _get_primary_monitor_rect()
        if rect:
            left, top, right, bottom = rect
            width = max(200, right - left)
            height = max(200, bottom - top)
            try:
                win32gui.MoveWindow(hwnd, left, top, width, height, True)
            except Exception:
                try:
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOP,
                        left,
                        top,
                        width,
                        height,
                        win32con.SWP_SHOWWINDOW,
                    )
                except Exception:
                    pass
    try:
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    except Exception:
        pass
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    return True

def _focus_chrome_window(prefer_tokens: Optional[List[str]] = None) -> bool:
    """Try to bring a Chrome window to the foreground."""
    tokens = [t.lower() for t in (prefer_tokens or []) if t]
    pyautogui, _ = _import_pyautogui()
    screen_w = screen_h = None
    if pyautogui:
        screen_w, screen_h = pyautogui.size()
    # 0) Focus by known PID
    global _LAST_CHROME_PID
    if _LAST_CHROME_HWND:
        try:
            _bring_hwnd_to_front(_LAST_CHROME_HWND)
            return True
        except Exception:
            pass
    if _LAST_CHROME_PID:
        try:
            from pywinauto import Application
            app = Application(backend="uia").connect(process=_LAST_CHROME_PID)
            win = app.top_window()
            try:
                win.set_focus()
                win.maximize()
            except Exception:
                pass
            try:
                rect = win.rectangle()
                if screen_w and screen_h and (rect.left >= screen_w or rect.top >= screen_h):
                    win.move_window(0, 0, screen_w, screen_h, repaint=True)
            except Exception:
                pass
            win.set_focus()
            time.sleep(0.4)
            try:
                rect = win.rectangle()
                if pyautogui:
                    pyautogui.click(rect.left + 80, rect.top + 15)
            except Exception:
                pass
            return True
        except Exception:
            pass
    # Try Win32 window handle by PID
    if _LAST_CHROME_PID:
        try:
            hwnd = _find_hwnd_by_pid(_LAST_CHROME_PID)
            if hwnd:
                _bring_hwnd_to_front(hwnd)
                return True
        except Exception:
            pass
    # 1) pygetwindow (fast path)
    try:
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle("Chrome") or gw.getWindowsWithTitle("Google Chrome")
        if windows:
            target = None
            if tokens:
                for win in windows:
                    title = (win.title or "").lower()
                    if any(token in title for token in tokens):
                        target = win
                        break
            if target is None:
                for win in windows:
                    if not getattr(win, "isMinimized", False):
                        target = win
                        break
                target = target or windows[0]
            try:
                if getattr(target, "isMinimized", False):
                    target.restore()
                target.activate()
                try:
                    target.maximize()
                except Exception:
                    pass
                time.sleep(0.4)
                if pyautogui:
                    pyautogui.click(target.left + 80, target.top + 15)
                try:
                    if hasattr(target, "_hWnd"):
                        _bring_hwnd_to_front(target._hWnd)
                except Exception:
                    pass
                return True
            except Exception:
                pass
    except Exception:
        pass

    # 2) pywinauto (UIA)
    try:
        from pywinauto import Desktop
        windows = Desktop(backend="uia").windows(class_name="Chrome_WidgetWin_1")
        if windows:
            target = None
            if tokens:
                for win in windows:
                    title = (win.window_text() or "").lower()
                    if any(token in title for token in tokens):
                        target = win
                        break
            target = target or windows[0]
            try:
                target.set_focus()
                try:
                    target.maximize()
                except Exception:
                    pass
                time.sleep(0.4)
                if pyautogui:
                    rect = target.rectangle()
                    pyautogui.click(rect.left + 80, rect.top + 15)
                return True
            except Exception:
                pass
    except Exception:
        pass

    return False


def _ensure_chrome_visible(prefer_tokens: Optional[List[str]] = None) -> bool:
    tokens = [t.lower() for t in (prefer_tokens or []) if t]
    global _FOCUS_LOCK
    _FOCUS_LOCK = True
    try:
        if _focus_chrome_window(tokens):
            return True
        # Alt+Tab fallback to cycle windows until Chrome/Cloud is visible
        pyautogui, _ = _import_pyautogui()
        if not pyautogui:
            return False
        for _ in range(8):
            pyautogui.hotkey("alt", "tab")
            time.sleep(0.7)
            if tokens and _screen_has_any(tokens):
                return True
        return False
    finally:
        _FOCUS_LOCK = False


def _focus_chrome(prefer_tokens: Optional[List[str]] = None) -> None:
    if _focus_chrome_enabled():
        _ensure_chrome_visible(prefer_tokens)


def _take_screenshot(name: str = "screen") -> Optional[Path]:
    """Take a screenshot of the current screen."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return None
    _focus_chrome(["google", "cloud", "console"])

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOTS_DIR / f"{name}_{ts}.png"
    img = pyautogui.screenshot()
    img.save(path)
    _debug_log(f"Saved screenshot: {path}")
    _debug_foreground(f"after screenshot {name}")
    _debug_screen_text(f"{name} screen")
    return path


def _open_chrome(url: str) -> bool:
    """Open Chrome browser with a URL."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break

    if not chrome_exe:
        # Try via PATH
        chrome_exe = shutil.which("chrome") or shutil.which("google-chrome")

    if not chrome_exe:
        return False

    try:
        args = [chrome_exe]
        if os.getenv("TREYS_AGENT_GOOGLE_CHROME_NEW_WINDOW", "1").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }:
            args.append("--new-window")
        args.append(url)
        proc = subprocess.Popen(args)
        global _LAST_CHROME_PID, _LAST_CHROME_HWND
        _LAST_CHROME_PID = proc.pid
        _LAST_CHROME_HWND = _find_hwnd_by_pid(proc.pid)
        time.sleep(3)  # Wait for Chrome to open
        _focus_chrome(["chrome", "google", "cloud", "console"])
        return True
    except Exception as e:
        logger.error(f"Failed to open Chrome: {e}")
        return False


def _navigate_chrome(url: str, expect_tokens: Optional[List[str]] = None) -> bool:
    """Navigate existing Chrome window to a URL without opening new windows."""
    if not _focus_chrome_enabled():
        return _open_chrome(url)
    if not _ensure_chrome_visible(["chrome", "google", "cloud", "console"]):
        return _open_chrome(url)
    try:
        _debug_log(f"Navigating Chrome to: {url}")
        _hotkey("ctrl", "l")
        time.sleep(0.2)
        _type_text(url)
        _press_key("enter")
        time.sleep(1)
        if expect_tokens:
            if not _wait_for_any(expect_tokens, timeout_seconds=8, interval=1.0):
                _debug_log(f"Expected tokens not found after nav: {expect_tokens}")
                _debug_screen_text("after navigation")
        _debug_foreground("after navigation")
        return True
    except Exception:
        return _open_chrome(url)


def _save_debug_screenshot_with_coords(name: str, x: int, y: int, click_result: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """
    Save a debug screenshot with coordinate overlay for troubleshooting.
    
    Args:
        name: Screenshot name prefix
        x: Target X coordinate
        y: Target Y coordinate
        click_result: Optional click result dict for additional info
    
    Returns:
        Path to saved screenshot or None
    """
    if not _debug_enabled():
        return None
    
    try:
        pyautogui, _ = _import_pyautogui()
        if not pyautogui:
            return None
        
        from PIL import Image, ImageDraw, ImageFont
        
        # Take screenshot
        img = pyautogui.screenshot()
        draw = ImageDraw.Draw(img)
        
        # Get current mouse position
        try:
            mouse_pos = pyautogui.position()
            mouse_x, mouse_y = mouse_pos.x, mouse_pos.y
        except Exception:
            mouse_x, mouse_y = None, None
        
        # Draw target coordinates
        draw.ellipse([x - 10, y - 10, x + 10, y + 10], outline="red", width=3)
        draw.line([x - 20, y, x + 20, y], fill="red", width=2)
        draw.line([x, y - 20, x, y + 20], fill="red", width=2)
        
        # Draw current mouse position if available
        if mouse_x is not None and mouse_y is not None:
            draw.ellipse([mouse_x - 8, mouse_y - 8, mouse_x + 8, mouse_y + 8], outline="blue", width=2)
        
        # Add text annotation
        info_lines = [f"Target: ({x}, {y})"]
        if mouse_x is not None and mouse_y is not None:
            info_lines.append(f"Mouse: ({mouse_x}, {mouse_y})")
        if click_result:
            info_lines.append(f"Method: {click_result.get('method_used', 'unknown')}")
            info_lines.append(f"Distance: {click_result.get('distance_from_target', 0):.1f}px")
            if click_result.get('conversion_applied'):
                info_lines.append(f"Converted from: {click_result.get('original_coords')}")
        
        # Draw text on image (top-left corner with background)
        text = "\n".join(info_lines)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Draw background rectangle for text
        bbox = draw.textbbox((10, 10), text, font=font) if font else (10, 10, 200, 50)
        draw.rectangle([bbox[0] - 5, bbox[1] - 5, bbox[2] + 5, bbox[3] + 5], fill="white", outline="black")
        draw.text((10, 10), text, fill="black", font=font)
        
        # Save screenshot
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = SCREENSHOTS_DIR / f"{name}_debug_{ts}.png"
        img.save(path)
        _debug_log(f"Saved debug screenshot with coordinates: {path}")
        return path
    except Exception as e:
        _debug_log(f"Failed to save debug screenshot: {e}")
        return None


def _verify_click_success(executor, expected_state_change: str = "enable button should change to manage/disable") -> Tuple[bool, str]:
    """
    Verify that a click was successful by taking a new screenshot and checking state.
    
    Args:
        executor: VisionExecutor instance
        expected_state_change: Description of what should have changed
    
    Returns:
        (success: bool, message: str)
    """
    time.sleep(1)  # Wait for page to respond
    try:
        # Take new screenshot to verify state changed
        executor.take_screenshot("post_click_verify")
        _debug_log(f"Post-click verification: {expected_state_change}")
        
        # Get fresh screen text to check state
        screen_text = _screen_text().lower()
        
        # Check if API is already enabled (this indicates either it was already enabled OR click succeeded)
        has_manage_disable = _screen_has_any(["manage", "disable", "api enabled"])
        has_enable_button = _screen_has_any(["enable"]) and not has_manage_disable
        
        if has_manage_disable:
            # API is enabled - but we need to check if it was ALREADY enabled or just got enabled
            # If we see "API Enabled" with checkmark, it might have been there before
            # We can't perfectly detect this, but if we just clicked, we'll assume success
            _debug_log("Verification: API appears enabled (Manage/Disable/API Enabled detected)")
            return True, "API is enabled - click may have succeeded or was already enabled"
        elif has_enable_button:
            # Enable button still visible - click likely failed
            _debug_log("Verification FAILED: Enable button still visible after click")
            return False, "Enable button still visible - click may have failed"
        else:
            # Page might have navigated away or state unclear
            _debug_log("Verification UNCLEAR: Cannot determine button state")
            return True, "Page state unclear - assuming click succeeded"
    except Exception as e:
        _debug_log(f"Verification error: {e}")
        return False, f"Verification failed: {e}"


def _get_chrome_window_rect() -> Optional[Tuple[int, int, int, int]]:
    """Get Chrome window rectangle (left, top, right, bottom) in screen coordinates."""
    global _LAST_CHROME_HWND, _LAST_CHROME_PID
    try:
        import win32gui
    except Exception:
        return None
    
    # Try using stored HWND first
    if _LAST_CHROME_HWND:
        try:
            rect = win32gui.GetWindowRect(_LAST_CHROME_HWND)
            return rect
        except Exception:
            pass
    
    # Try finding by PID
    if _LAST_CHROME_PID:
        hwnd = _find_hwnd_by_pid(_LAST_CHROME_PID)
        if hwnd:
            try:
                rect = win32gui.GetWindowRect(hwnd)
                _LAST_CHROME_HWND = hwnd
                return rect
            except Exception:
                pass
    
    # Fallback: find Chrome window by title
    try:
        def _enum(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return
                title = win32gui.GetWindowText(hwnd).lower()
                if "chrome" in title and ("cloud" in title or "console" in title or "google" in title):
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        matches.append((hwnd, rect))
                    except Exception:
                        pass
            except Exception:
                return
        
        matches = []
        win32gui.EnumWindows(_enum, None)
        if matches:
            _LAST_CHROME_HWND = matches[0][0]
            return matches[0][1]
    except Exception:
        pass
    
    return None


def _click_at(x: int, y: int, clicks: int = 1) -> Dict[str, Any]:
    """
    Click at specific coordinates using the most reliable method available.
    
    Tries methods in order of reliability:
    1. pynput (most reliable on Windows)
    2. win32api SendInput (Windows-native, very reliable)
    3. PyAutoGUI (fallback, sometimes unreliable)
    
    Returns detailed result dict:
    {
        "success": bool,
        "method_used": "pynput" | "win32api" | "pyautogui" | None,
        "mouse_position_after": (x, y) | None,
        "distance_from_target": float,
        "original_coords": (x, y),
        "converted_coords": (x, y),
        "conversion_applied": bool,
        "window_rect": (left, top, right, bottom) | None,
    }
    """
    original_x, original_y = x, y
    conversion_applied = False
    window_rect = None
    
    # Get screen size for validation (try PyAutoGUI first as it's most common)
    pyautogui, _ = _import_pyautogui()
    screen_w, screen_h = 1920, 1080  # defaults
    if pyautogui:
        try:
            screen_w, screen_h = pyautogui.size()
        except Exception:
            pass
    
    _debug_log(f"Screen size: {screen_w}x{screen_h}, input coordinates: ({x}, {y})")
    
    # Try to get Chrome window position to convert window-relative to screen-absolute
    window_rect = _get_chrome_window_rect()
    if window_rect:
        left, top, right, bottom = window_rect
        window_width = right - left
        window_height = bottom - top
        _debug_log(f"Chrome window rect: ({left}, {top}, {right}, {bottom}), size: {window_width}x{window_height}")
        
        # If coordinates are small (likely window-relative), convert to screen-absolute
        if x < window_width and y < window_height:
            screen_x = left + x
            screen_y = top + y
            _debug_log(f"Converting window-relative ({x}, {y}) to screen-absolute ({screen_x}, {screen_y})")
            x, y = screen_x, screen_y
            conversion_applied = True
        else:
            _debug_log(f"Coordinates ({x}, {y}) seem to be screen-absolute (larger than window {window_width}x{window_height})")
    else:
        _debug_log("Could not get Chrome window position - using coordinates as-is (assumed screen-absolute)")
    
    # Validate coordinates
    if x < 0 or y < 0:
        _debug_log(f"Coordinates ({x}, {y}) are negative - invalid")
        return {
            "success": False,
            "method_used": None,
            "mouse_position_after": None,
            "distance_from_target": float('inf'),
            "original_coords": (original_x, original_y),
            "converted_coords": (x, y),
            "conversion_applied": conversion_applied,
            "window_rect": window_rect,
        }
    
    # Get mouse position before click
    mouse_before = None
    if pyautogui:
        try:
            mouse_before = pyautogui.position()
            _debug_log(f"Mouse before click: {mouse_before}")
        except Exception:
            pass
    
    # Method 1: Try pynput (most reliable on Windows)
    Controller, Button, err = _import_pynput()
    if Controller and Button:
        try:
            _debug_log(f"[PYNPUT] Step 1: Moving mouse to ({x}, {y})...")
            mouse = Controller()
            mouse.position = (x, y)
            time.sleep(0.3)  # Wait for mouse to actually move
            
            # Verify mouse moved using pynput
            current_pos = mouse.position
            distance = ((current_pos[0] - x) ** 2 + (current_pos[1] - y) ** 2) ** 0.5
            _debug_log(f"[PYNPUT] Step 2: Mouse reported at {current_pos}, distance from target: {distance:.1f}px")
            
            # CRITICAL: Take screenshot to visually verify mouse is over button
            _debug_log(f"[PYNPUT] Step 3: Taking screenshot to verify mouse position visually...")
            debug_shot_before = _save_debug_screenshot_with_coords("before_click_pynput", x, y, None)
            if debug_shot_before:
                _debug_log(f"[PYNPUT] Saved verification screenshot: {debug_shot_before}")
            
            # Also verify using pyautogui for comparison
            pyautogui_pos = None
            if pyautogui:
                try:
                    pyautogui_pos = pyautogui.position()
                    pyautogui_distance = ((pyautogui_pos.x - x) ** 2 + (pyautogui_pos.y - y) ** 2) ** 0.5
                    _debug_log(f"[PYNPUT] PyAutoGUI reports mouse at ({pyautogui_pos.x}, {pyautogui_pos.y}), distance: {pyautogui_distance:.1f}px")
                except Exception:
                    pass
            
            # Check if mouse is close enough to target
            if distance < 50:  # Close enough
                _debug_log(f"[PYNPUT] Step 4: Mouse is close enough (distance: {distance:.1f}px), proceeding with click...")
                for i in range(clicks):
                    mouse.click(Button.left, 1)
                    if i < clicks - 1:
                        time.sleep(0.05)
                
                time.sleep(0.2)
                
                # Take screenshot after click
                _debug_log(f"[PYNPUT] Step 5: Taking screenshot after click...")
                debug_shot_after = _save_debug_screenshot_with_coords("after_click_pynput", x, y, None)
                if debug_shot_after:
                    _debug_log(f"[PYNPUT] Saved post-click screenshot: {debug_shot_after}")
                
                final_pos = mouse.position
                final_distance = ((final_pos[0] - x) ** 2 + (final_pos[1] - y) ** 2) ** 0.5
                _debug_log(f"[PYNPUT] Click completed. Final mouse position: {final_pos}, distance: {final_distance:.1f}px")
                return {
                    "success": True,
                    "method_used": "pynput",
                    "mouse_position_after": (final_pos[0], final_pos[1]),
                    "distance_from_target": final_distance,
                    "original_coords": (original_x, original_y),
                    "converted_coords": (x, y),
                    "conversion_applied": conversion_applied,
                    "window_rect": window_rect,
                    "debug_screenshot_before": str(debug_shot_before) if debug_shot_before else None,
                    "debug_screenshot_after": str(debug_shot_after) if debug_shot_after else None,
                }
            else:
                _debug_log(f"[PYNPUT] Mouse didn't reach target (distance: {distance:.1f}px), trying fallback...")
        except Exception as e:
            _debug_log(f"[PYNPUT] Failed: {e}, trying fallback...")
            import traceback
            _debug_log(traceback.format_exc())
    
    # Method 2: Try win32api SendInput (Windows-native)
    win32api, win32con, err = _import_win32api()
    if win32api and win32con:
        try:
            _debug_log(f"[WIN32API] Step 1: Moving mouse to ({x}, {y})...")
            # Move mouse using SetCursorPos
            win32api.SetCursorPos((x, y))
            time.sleep(0.3)  # Wait for mouse to actually move
            
            # Verify mouse position
            current_pos = win32api.GetCursorPos()
            distance = ((current_pos[0] - x) ** 2 + (current_pos[1] - y) ** 2) ** 0.5
            _debug_log(f"[WIN32API] Step 2: Mouse reported at {current_pos}, distance from target: {distance:.1f}px")
            
            # CRITICAL: Take screenshot to visually verify mouse is over button
            _debug_log(f"[WIN32API] Step 3: Taking screenshot to verify mouse position visually...")
            debug_shot_before = _save_debug_screenshot_with_coords("before_click_win32api", x, y, None)
            if debug_shot_before:
                _debug_log(f"[WIN32API] Saved verification screenshot: {debug_shot_before}")
            
            # Also verify using pyautogui for comparison
            pyautogui_pos = None
            if pyautogui:
                try:
                    pyautogui_pos = pyautogui.position()
                    pyautogui_distance = ((pyautogui_pos.x - x) ** 2 + (pyautogui_pos.y - y) ** 2) ** 0.5
                    _debug_log(f"[WIN32API] PyAutoGUI reports mouse at ({pyautogui_pos.x}, {pyautogui_pos.y}), distance: {pyautogui_distance:.1f}px")
                except Exception:
                    pass
            
            _debug_log(f"[WIN32API] Step 4: Proceeding with click...")
            # Click using mouse_event
            for i in range(clicks):
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
                if i < clicks - 1:
                    time.sleep(0.05)
            
            time.sleep(0.2)
            
            # Take screenshot after click
            _debug_log(f"[WIN32API] Step 5: Taking screenshot after click...")
            debug_shot_after = _save_debug_screenshot_with_coords("after_click_win32api", x, y, None)
            if debug_shot_after:
                _debug_log(f"[WIN32API] Saved post-click screenshot: {debug_shot_after}")
            
            final_pos = win32api.GetCursorPos()
            final_distance = ((final_pos[0] - x) ** 2 + (final_pos[1] - y) ** 2) ** 0.5
            _debug_log(f"[WIN32API] Click completed. Final mouse position: {final_pos}, distance: {final_distance:.1f}px")
            return {
                "success": True,
                "method_used": "win32api",
                "mouse_position_after": (final_pos[0], final_pos[1]),
                "distance_from_target": final_distance,
                "original_coords": (original_x, original_y),
                "converted_coords": (x, y),
                "conversion_applied": conversion_applied,
                "window_rect": window_rect,
                "debug_screenshot_before": str(debug_shot_before) if debug_shot_before else None,
                "debug_screenshot_after": str(debug_shot_after) if debug_shot_after else None,
            }
        except Exception as e:
            _debug_log(f"[WIN32API] Failed: {e}, trying PyAutoGUI fallback...")
            import traceback
            _debug_log(traceback.format_exc())
    
    # Method 3: Fallback to PyAutoGUI
    if pyautogui:
        try:
            _debug_log(f"[PYAUTOGUI] Step 1: Moving mouse to ({x}, {y})...")
            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0.05
            
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.3)  # Wait for mouse to actually move
            
            mouse_after_move = pyautogui.position()
            distance_after_move = ((mouse_after_move.x - x) ** 2 + (mouse_after_move.y - y) ** 2) ** 0.5
            _debug_log(f"[PYAUTOGUI] Step 2: Mouse reported at {mouse_after_move}, distance: {distance_after_move:.1f}px")
            
            # CRITICAL: Take screenshot to visually verify mouse is over button
            _debug_log(f"[PYAUTOGUI] Step 3: Taking screenshot to verify mouse position visually...")
            debug_shot_before = _save_debug_screenshot_with_coords("before_click_pyautogui", x, y, None)
            if debug_shot_before:
                _debug_log(f"[PYAUTOGUI] Saved verification screenshot: {debug_shot_before}")
            
            _debug_log(f"[PYAUTOGUI] Step 4: Proceeding with click...")
            pyautogui.click(clicks=clicks)
            time.sleep(0.2)
            
            # Take screenshot after click
            _debug_log(f"[PYAUTOGUI] Step 5: Taking screenshot after click...")
            debug_shot_after = _save_debug_screenshot_with_coords("after_click_pyautogui", x, y, None)
            if debug_shot_after:
                _debug_log(f"[PYAUTOGUI] Saved post-click screenshot: {debug_shot_after}")
            
            mouse_after = pyautogui.position()
            final_distance = ((mouse_after.x - x) ** 2 + (mouse_after.y - y) ** 2) ** 0.5
            _debug_log(f"[PYAUTOGUI] Click completed. Final mouse position: {mouse_after}, distance: {final_distance:.1f}px")
            return {
                "success": True,
                "method_used": "pyautogui",
                "mouse_position_after": (mouse_after.x, mouse_after.y),
                "distance_from_target": final_distance,
                "original_coords": (original_x, original_y),
                "converted_coords": (x, y),
                "conversion_applied": conversion_applied,
                "window_rect": window_rect,
                "debug_screenshot_before": str(debug_shot_before) if debug_shot_before else None,
                "debug_screenshot_after": str(debug_shot_after) if debug_shot_after else None,
            }
        except pyautogui.FailSafeException:
            _debug_log("[PYAUTOGUI] FailSafeException - mouse moved to corner")
            return {
                "success": False,
                "method_used": "pyautogui",
                "mouse_position_after": None,
                "distance_from_target": float('inf'),
                "original_coords": (original_x, original_y),
                "converted_coords": (x, y),
                "conversion_applied": conversion_applied,
                "window_rect": window_rect,
            }
        except Exception as e:
            _debug_log(f"[PYAUTOGUI] Failed: {type(e).__name__}: {e}")
            import traceback
            _debug_log(traceback.format_exc())
    
    _debug_log("ERROR: No click method available (pynput, win32api, or pyautogui)")
    return {
        "success": False,
        "method_used": None,
        "mouse_position_after": None,
        "distance_from_target": float('inf'),
        "original_coords": (original_x, original_y),
        "converted_coords": (x, y),
        "conversion_applied": conversion_applied,
        "window_rect": window_rect,
    }


def _type_text(text: str, interval: float = 0.02) -> bool:
    """Type text using keyboard."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    if not _FOCUS_LOCK:
        _focus_chrome(["chrome", "google", "cloud", "console"])
    try:
        pyautogui.write(text, interval=interval)
        return True
    except Exception:
        return False


def _press_key(key: str) -> bool:
    """Press a keyboard key."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    if not _FOCUS_LOCK:
        _focus_chrome(["chrome", "google", "cloud", "console"])
    try:
        pyautogui.press(key)
        return True
    except Exception:
        return False


def _hotkey(*keys) -> bool:
    """Press a key combination."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    if not _FOCUS_LOCK:
        _focus_chrome(["chrome", "google", "cloud", "console"])
    try:
        pyautogui.hotkey(*keys)
        return True
    except Exception:
        return False


def _wait_and_prompt(message: str) -> str:
    """Prompt user for input."""
    print(f"\n[USER ACTION REQUIRED] {message}")
    return input("> ").strip()


def _hands_free_enabled() -> bool:
    return os.getenv("TREYS_AGENT_GOOGLE_HANDS_FREE", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def _manual_fallback_allowed() -> bool:
    return os.getenv("TREYS_AGENT_GOOGLE_MANUAL_FALLBACK", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def _autoclick_enabled() -> bool:
    return os.getenv("TREYS_AGENT_GOOGLE_AUTOCLICK", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _auto_click_text(
    targets: List[str],
    *,
    attempts: int = 2,
    delay: float = 1.0,
    min_y: int = 0,
    max_y: Optional[int] = None,
) -> bool:
    """Attempt to click a screen element by OCR text match."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    try:
        import pytesseract
        from PIL import Image  # noqa: F401
    except Exception:
        return False

    target_tokens = [t.lower() for t in targets if t]
    for _ in range(max(1, attempts)):
        img = pyautogui.screenshot()
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        texts = data.get("text", [])
        for i, text in enumerate(texts):
            t = (text or "").strip().lower()
            if not t:
                continue
            if any(token in t for token in target_tokens):
                x = int(data["left"][i])
                y = int(data["top"][i])
                w = int(data["width"][i])
                h = int(data["height"][i])
                if y < min_y:
                    continue
                if max_y is not None and y > max_y:
                    continue
                pyautogui.click(x + max(1, w // 2), y + max(1, h // 2))
                time.sleep(delay)
                return True
        time.sleep(delay)
    return False


def _auto_click_main(targets: List[str], *, attempts: int = 2, delay: float = 1.0) -> bool:
    """Click OCR text but avoid the browser toolbar/bookmarks area."""
    return _auto_click_text(targets, attempts=attempts, delay=delay, min_y=120)


def _find_button_coordinates_ocr(button_texts: List[str], screenshot_path: Optional[Path] = None) -> Optional[Tuple[int, int]]:
    """
    Use OCR to find the exact coordinates of a button by its text.
    
    Args:
        button_texts: List of text patterns to search for (e.g., ["enable", "enable api"])
        screenshot_path: Optional path to screenshot. If None, takes a new screenshot.
    
    Returns:
        (x, y) coordinates of button center, or None if not found
    """
    try:
        import pytesseract
        from PIL import Image
        pyautogui, _ = _import_pyautogui()
        if not pyautogui:
            return None
        
        # Take or use screenshot
        if screenshot_path and screenshot_path.exists():
            img = Image.open(screenshot_path)
        else:
            img = pyautogui.screenshot()
        
        # Run OCR
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        texts = data.get("text", [])
        
        button_texts_lower = [t.lower() for t in button_texts]
        
        # Search for button text
        best_match = None
        best_confidence = 0
        
        for i, text in enumerate(texts):
            text_lower = (text or "").strip().lower()
            if not text_lower:
                continue
            
            # Check if any button text matches
            # IMPORTANT: Avoid matching "enable" within "API enabled" or other text
            for btn_text in button_texts_lower:
                # For "^enable$" pattern, match only standalone "enable" word
                if btn_text == "^enable$":
                    # Use word boundary matching - "enable" must be a complete word
                    import re
                    if re.search(r'\benable\b', text_lower):
                        # Found standalone "enable" - this is likely the button
                        x = int(data["left"][i])
                        y = int(data["top"][i])
                        w = int(data["width"][i])
                        h = int(data["height"][i])
                        conf = float(data.get("conf", [0])[i] or 0)
                        
                        # Calculate center of button
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Avoid browser toolbar (y < 120) and avoid text in "API enabled" status
                        # "API enabled" usually appears in upper/mid section, Enable button is usually lower
                        if center_y > 120 and center_y > 400:  # Enable button is usually in lower half
                            if conf > best_confidence:
                                best_match = (center_x, center_y)
                                best_confidence = conf
                                _debug_log(f"Found button '{btn_text}' at ({center_x}, {center_y}) with confidence {conf:.1f}%")
                elif btn_text in text_lower:
                    # For phrases like "enable button" or "enable api", match normally
                    x = int(data["left"][i])
                    y = int(data["top"][i])
                    w = int(data["width"][i])
                    h = int(data["height"][i])
                    conf = float(data.get("conf", [0])[i] or 0)
                    
                    # Calculate center of button
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # Avoid browser toolbar (y < 120)
                    if center_y > 120:
                        if conf > best_confidence:
                            best_match = (center_x, center_y)
                            best_confidence = conf
                            _debug_log(f"Found button '{btn_text}' at ({center_x}, {center_y}) with confidence {conf:.1f}%")
        
        if best_match:
            _debug_log(f"OCR found button at coordinates: {best_match}")
            return best_match
        
        _debug_log(f"OCR could not find button text: {button_texts}")
        return None
    except Exception as e:
        _debug_log(f"OCR button search failed: {e}")
        return None


def _troubleshoot_failed_click(executor, target_text: str, attempted_coords: Tuple[int, int], click_result: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    """
    Troubleshoot a failed click by trying alternative approaches.
    
    Returns:
        New coordinates to try, or None if no solution found
    """
    _debug_log(f"Troubleshooting failed click for '{target_text}' at {attempted_coords}")
    
    # Strategy 1: Use OCR to find exact button location
    _debug_log("Strategy 1: Using OCR to find exact button coordinates...")
    new_screenshot = executor.take_screenshot("troubleshoot_ocr")
    ocr_coords = _find_button_coordinates_ocr([target_text, f"{target_text} api", f"{target_text} button"], new_screenshot.screenshot_path)
    
    if ocr_coords:
        ocr_x, ocr_y = ocr_coords
        attempted_x, attempted_y = attempted_coords
        
        # Check if OCR coordinates are significantly different
        distance = ((ocr_x - attempted_x) ** 2 + (ocr_y - attempted_y) ** 2) ** 0.5
        if distance > 20:  # More than 20px difference
            _debug_log(f"OCR found different coordinates: {ocr_coords} (distance: {distance:.1f}px from attempted {attempted_coords})")
            return ocr_coords
        else:
            _debug_log(f"OCR coordinates similar to attempted ({distance:.1f}px difference), may be correct")
    
    # Strategy 2: Try nearby coordinates (button might be slightly offset)
    _debug_log("Strategy 2: Trying nearby coordinates...")
    attempted_x, attempted_y = attempted_coords
    offsets = [
        (0, -10), (0, 10), (-10, 0), (10, 0),  # Up, down, left, right
        (-5, -5), (5, 5), (-5, 5), (5, -5),  # Diagonals
        (0, -20), (0, 20), (-20, 0), (20, 0),  # Further offsets
    ]
    
    for offset_x, offset_y in offsets:
        new_x = attempted_x + offset_x
        new_y = attempted_y + offset_y
        if new_x > 0 and new_y > 120:  # Valid coordinates
            _debug_log(f"Trying offset coordinates: ({new_x}, {new_y})")
            return (new_x, new_y)
    
    # Strategy 3: Check if we need to scroll first
    _debug_log("Strategy 3: Button might be off-screen, may need to scroll")
    # This will be handled by the caller
    
    return None


def _auto_click_near_label(
    label_tokens: List[str], *, x_offset: int = 140, require_all: bool = False
) -> bool:
    """Click near a label (e.g., to focus an input field)."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    try:
        import pytesseract
        from PIL import Image  # noqa: F401
    except Exception:
        return False

    tokens = [t.lower() for t in label_tokens if t]
    img = pyautogui.screenshot()
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    texts = data.get("text", [])
    for i, text in enumerate(texts):
        t = (text or "").strip().lower()
        if not t:
            continue
        if require_all:
            if not all(token in t for token in tokens):
                continue
        else:
            if not any(token in t for token in tokens):
                continue
        x = int(data["left"][i])
        y = int(data["top"][i])
        w = int(data["width"][i])
        h = int(data["height"][i])
        pyautogui.click(x + w + x_offset, y + max(1, h // 2))
        time.sleep(0.5)
        return True
    return False


def _screen_text() -> str:
    """Return OCR text for the current screen (lowercased)."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return ""
    _focus_chrome(["google", "cloud", "console"])
    try:
        import pytesseract
    except Exception:
        return ""
    img = pyautogui.screenshot()
    try:
        text = pytesseract.image_to_string(img)
    except Exception:
        return ""
    return (text or "").lower()


def _screen_has_any(tokens: List[str]) -> bool:
    text = _screen_text()
    return any(token.lower() in text for token in tokens if token)


def _wait_for_any(tokens: List[str], *, timeout_seconds: int = 30, interval: float = 1.0) -> bool:
    end = time.time() + timeout_seconds
    while time.time() < end:
        if _screen_has_any(tokens):
            return True
        time.sleep(interval)
    return False


def _fill_field_by_label(label_tokens: List[str], value: str) -> bool:
    """Click near a label and type into the field."""
    if not value:
        return False
    if not _auto_click_near_label(label_tokens):
        return False
    try:
        _hotkey("ctrl", "a")
    except Exception:
        pass
    _type_text(value)
    return True


def _ensure_logged_in(creds: Optional[Dict[str, str]], *, twofa_wait: int) -> bool:
    """Detect logged-in state and perform login if needed."""
    logged_in_tokens = [
        "google cloud",
        "console.cloud.google.com",
        "navigation menu",
        "apis & services",
        "billing",
        "search products",
        "dashboard",
        "select a project",
        "project selector",
        "resources",
        "cloud shell",
        "cloud console",
    ]
    account_picker_tokens = [
        "choose an account",
        "continue as",
        "use another account",
        "choose account",
    ]
    login_tokens = [
        "email",
        "phone",
        "forgot email",
        "next",
        "create account",
        "to continue",
        "sign in",
        "use your google account",
        "email or phone",
    ]

    # Give the page a moment to load recognizable text
    _wait_for_any(logged_in_tokens + account_picker_tokens + login_tokens, timeout_seconds=6, interval=1.0)

    if _screen_has_any(logged_in_tokens) and not _screen_has_any(["sign in", "email"]):
        return True

    if _screen_has_any(account_picker_tokens):
        # Prefer clicking the saved username or "Continue as" if available
        if creds and creds.get("username"):
            if _auto_click_text([creds["username"], creds["username"].split("@")[0], "continue as"]):
                return _wait_for_any(logged_in_tokens, timeout_seconds=60, interval=2.0)
        if _auto_click_text(["continue as"]):
            return _wait_for_any(logged_in_tokens, timeout_seconds=60, interval=2.0)
        # Fallback: click the first account entry region
        pyautogui, _ = _import_pyautogui()
        if pyautogui:
            w, h = pyautogui.size()
            pyautogui.click(int(w * 0.5), int(h * 0.42))
            time.sleep(1)
            if _screen_has_any(logged_in_tokens):
                return True

    if not _screen_has_any(login_tokens):
        # Try opening login page explicitly
        _open_chrome("https://accounts.google.com/ServiceLogin?service=cloudconsole")
        time.sleep(2)

    if _screen_has_any(logged_in_tokens) and not _screen_has_any(["sign in", "email"]):
        return True

    if _screen_has_any(account_picker_tokens):
        if creds and creds.get("username"):
            if _auto_click_text([creds["username"], creds["username"].split("@")[0], "continue as"]):
                return _wait_for_any(logged_in_tokens, timeout_seconds=60, interval=2.0)
        if _auto_click_text(["continue as"]):
            return _wait_for_any(logged_in_tokens, timeout_seconds=60, interval=2.0)

    if not creds or not creds.get("username") or not creds.get("password"):
        # If we cannot see a login form, assume the user is already logged in
        if not _screen_has_any(login_tokens):
            return True
        return False

    # Attempt login
    _auto_click_near_label(["email", "phone", "email or phone"])
    _type_text(creds.get("username", ""))
    _press_key("enter")
    _wait_for_any(["password"], timeout_seconds=10, interval=1.0)
    _auto_click_near_label(["password"])
    _type_text(creds.get("password", ""))
    _press_key("enter")
    
    # Wait a moment for 2FA screen to appear
    time.sleep(2)
    
    # Attempt automatic 2FA handling
    if _handle_2fa_automatically(creds):
        # 2FA handled automatically, continue
        pass
    else:
        # Fall back to manual wait
        _wait_for_continue(
            "Complete any remaining login steps (including 2FA). Type 'continue' when done.",
            seconds=twofa_wait,
        )

    return _wait_for_any(logged_in_tokens, timeout_seconds=90, interval=2.0)


def _handle_2fa_automatically(creds: Optional[Dict[str, str]]) -> bool:
    """
    Automatically handle 2FA by:
    1. Detecting 2FA screen
    2. Clicking "Send code to email" option
    3. Opening Gmail in new tab
    4. Extracting verification code from email
    5. Entering code back into 2FA form
    """
    twofa_tokens = [
        "verify",
        "verification",
        "2-step",
        "2 step",
        "two-step",
        "two step",
        "enter the code",
        "enter code",
        "verification code",
        "google verification",
    ]
    
    # Check if we're on a 2FA screen
    if not _screen_has_any(twofa_tokens):
        _debug_log("Not on 2FA screen, skipping automatic 2FA handling")
        return False
    
    _debug_log("2FA screen detected, attempting automatic handling...")
    
    # Step 1: Click "Send code to email" or similar option
    email_option_tokens = [
        "send code to",
        "send to email",
        "get code via email",
        "email",
        "send it",
    ]
    
    # Try to find and click email option
    clicked_email_option = False
    if _screen_has_any(["email"]) or _screen_has_any(["send"]):
        # Look for radio button or button with email option
        clicked_email_option = _auto_click_text(email_option_tokens, attempts=3, delay=0.5)
        if not clicked_email_option:
            # Try clicking near "email" text
            clicked_email_option = _auto_click_near_label(email_option_tokens)
    
    if clicked_email_option:
        _debug_log("Clicked email option for 2FA code")
        time.sleep(1)
        # Press Enter or click "Next" to send code
        _press_key("enter")
        time.sleep(2)
    else:
        _debug_log("Could not click email option, trying Enter as fallback")
        _press_key("enter")
        time.sleep(2)
    
    # Step 2: Open Gmail in new tab
    _debug_log("Opening Gmail in new tab to retrieve code...")
    _hotkey("ctrl", "t")  # Open new tab
    time.sleep(0.5)
    _hotkey("ctrl", "l")  # Focus address bar
    time.sleep(0.3)
    _type_text("https://mail.google.com")
    _press_key("enter")
    time.sleep(3)  # Wait for Gmail to load
    
    # Step 3: Extract verification code from Gmail
    code = _extract_2fa_code_from_gmail()
    
    if not code:
        _debug_log("Could not extract 2FA code from Gmail, falling back to manual")
        # Close Gmail tab and return False
        _hotkey("ctrl", "w")
        return False
    
    _debug_log(f"Extracted 2FA code: {code}")
    
    # Step 4: Switch back to original tab (Ctrl+PageUp or Alt+Tab)
    _hotkey("ctrl", "pageup")  # Switch to previous tab
    time.sleep(1)
    # Alternative: use Alt+Tab to switch windows
    pyautogui, _ = _import_pyautogui()
    if pyautogui:
        pyautogui.hotkey("alt", "tab")
        time.sleep(0.5)
    
    # Step 5: Enter the code
    _debug_log("Entering 2FA code...")
    time.sleep(1)
    
    # Find code input field
    code_input_tokens = ["code", "enter code", "verification code", "enter the code"]
    _auto_click_near_label(code_input_tokens)
    time.sleep(0.5)
    
    # Type the code
    _type_text(code)
    time.sleep(0.5)
    _press_key("enter")
    
    # Wait a moment for verification
    time.sleep(3)
    
    _debug_log("2FA code entered, waiting for verification...")
    return True


def _extract_2fa_code_from_gmail() -> Optional[str]:
    """
    Extract 2FA verification code from Gmail.
    Looks for the most recent email from Google/noreply with a verification code.
    """
    import re
    
    # Wait for Gmail to load
    time.sleep(2)
    
    # Use OCR to find verification code
    ocr_text = _screen_text()
    if not ocr_text:
        return None
    
    _debug_log(f"Gmail OCR text (first 500 chars): {ocr_text[:500]}")
    
    # Look for common verification code patterns
    # Google codes are usually 6 digits
    code_patterns = [
        r'\b(\d{6})\b',  # 6-digit code
        r'code[:\s]+(\d{6})',  # "code: 123456"
        r'verification[:\s]+(\d{6})',  # "verification: 123456"
        r'(\d{6})\s+is your',  # "123456 is your"
        r'Your code is[:\s]+(\d{6})',  # "Your code is: 123456"
        r'G-(\d{6})',  # Google format: G-123456
    ]
    
    for pattern in code_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        if matches:
            # Take the first match (most recent)
            code = matches[0] if isinstance(matches[0], str) else matches[0][0] if matches[0] else None
            if code:
                # Clean up code (remove G- prefix if present)
                code = re.sub(r'G-', '', str(code)).strip()
                if len(code) >= 4:  # Valid codes are usually 4-8 digits
                    return code
    
    # If OCR didn't work, try scrolling to top and looking at email preview
    # Click on first email if visible
    pyautogui, _ = _import_pyautogui()
    if pyautogui:
        try:
            # Try clicking first email in inbox
            w, h = pyautogui.size()
            pyautogui.click(int(w * 0.3), int(h * 0.4))  # Approximate location of first email
            time.sleep(2)
            
            # Try OCR again
            ocr_text = _screen_text()
            if ocr_text:
                for pattern in code_patterns:
                    matches = re.findall(pattern, ocr_text, re.IGNORECASE)
                    if matches:
                        code = matches[0] if isinstance(matches[0], str) else matches[0][0] if matches[0] else None
                        if code:
                            code = re.sub(r'G-', '', str(code)).strip()
                            if len(code) >= 4:
                                return code
        except Exception as exc:
            _debug_log(f"Failed to click email: {exc}")
    
    return None


def _sleep_with_countdown(seconds: int, label: str) -> None:
    seconds = max(1, int(seconds))
    print(f"[AUTO] {label} (waiting {seconds}s)")
    for _ in range(seconds):
        time.sleep(1)


def _wait_or_prompt(message: str, *, seconds: int) -> str:
    """Hands-free wait (no input) or prompt for manual confirmation."""
    if not _manual_fallback_allowed():
        return ""
    if _hands_free_enabled():
        _sleep_with_countdown(seconds, message)
        return ""
    return _wait_and_prompt(message)


def _prompt_manual_or_fail(message: str, *, seconds: int) -> bool:
    """Prompt for manual action if allowed; otherwise signal failure."""
    if not _manual_fallback_allowed():
        return False
    _wait_for_continue(message, seconds=seconds)
    return True


def _attempt_project_creation(project_name: str) -> bool:
    """Try to create a project using OCR + keyboard heuristics."""
    if not project_name:
        return False
    _focus_chrome(["project", "cloud", "google"])
    offsets = [60, 100, 140, 180, 220, 260]
    focused = False
    # Strict match first
    for offset in offsets:
        if _auto_click_near_label(["project", "name"], x_offset=offset, require_all=True):
            focused = True
            break
    # Looser match fallback
    if not focused:
        for offset in offsets:
            if _auto_click_near_label(["project", "name"], x_offset=offset, require_all=False):
                focused = True
                break
    if not focused:
        for offset in offsets:
            if _auto_click_near_label(["project"], x_offset=offset, require_all=False):
                focused = True
                break
    if not focused:
        pyautogui, _ = _import_pyautogui()
        if pyautogui:
            w, h = pyautogui.size()
            pyautogui.click(int(w * 0.5), int(h * 0.38))
            time.sleep(0.5)
    try:
        _hotkey("ctrl", "a")
    except Exception:
        pass
    _type_text(project_name)
    time.sleep(0.5)
    if _auto_click_text(["create", "create project"], attempts=3, delay=0.8):
        return True
    _press_key("enter")
    time.sleep(1)
    if _auto_click_text(["create", "create project"], attempts=2, delay=0.8):
        return True
    # Tab-cycle fallback: attempt to reach input then submit
    pyautogui, _ = _import_pyautogui()
    if pyautogui:
        for _ in range(6):
            _press_key("tab")
            time.sleep(0.2)
        _type_text(project_name)
        time.sleep(0.5)
        if _auto_click_text(["create", "create project"], attempts=2, delay=0.8):
            return True
        _press_key("enter")
        time.sleep(1)
        if _auto_click_text(["create", "create project"], attempts=2, delay=0.8):
            return True
    return False


def _wait_for_continue(message: str, *, seconds: int) -> str:
    """Require typing 'continue' after 2FA, or timed wait in hands-free."""
    if _hands_free_enabled():
        _sleep_with_countdown(seconds, message)
        return ""
    require_continue = os.getenv("TREYS_AGENT_GOOGLE_REQUIRE_CONTINUE_2FA", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }
    if not require_continue:
        return _wait_and_prompt(message)
    print(f"\n[USER ACTION REQUIRED] {message}")
    while True:
        answer = input("> ").strip().lower()
        if answer in {"continue", "c", "go", "ok"}:
            return answer
        print("Type 'continue' to proceed.")


def _prompt_user_guidance(message: str) -> str:
    """Ask for a direct instruction to recover UI automation."""
    print(f"\n[USER GUIDANCE] {message}")
    try:
        answer = input("> ").strip()
    except EOFError:
        # Non-interactive environment (e.g., testing) - return empty to continue
        print("  (Non-interactive mode - continuing automatically)")
        return ""
    lower = answer.lower()
    if lower in {"continue", "c", "go", "ok"}:
        return ""
    if lower.startswith(("open ", "goto ", "url ")):
        parts = answer.split(None, 1)
        if len(parts) == 2:
            _navigate_chrome(parts[1].strip())
            return ""
    if "enable" in lower:
        _auto_click_main(["enable", "enable api", "enable to"])
        return ""
    return answer


def _get_saved_google_creds() -> Optional[Dict[str, str]]:
    """Retrieve saved Google credentials (if available)."""
    try:
        from agent.memory.credentials import get_credential
    except Exception:
        return None
    for site in ("google", "gmail", "google_account"):
        creds = get_credential(site)
        if creds and (creds.get("username") or creds.get("password")):
            return creds
    return None


def _normalize_text(value: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _project_is_active(project_name: str) -> bool:
    if not project_name:
        return False
    screen = _screen_text()
    if not screen:
        return False
    return _normalize_text(project_name) in _normalize_text(screen)


def _find_downloaded_credentials() -> Optional[Path]:
    """Find the most recently downloaded credentials JSON file."""
    search_dirs = [
        DOWNLOADS_DIR,
        REPO_ROOT / "downloads",
        REPO_ROOT / "evidence" / "downloads",
    ]
    override_dir = os.getenv("TREYS_AGENT_GOOGLE_DOWNLOAD_DIR", "").strip()
    if override_dir:
        search_dirs.insert(0, Path(override_dir))

    candidates = []
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        # Look for Google OAuth credential files
        for pattern in ["client_secret*.json", "*oauth*.json", "credentials*.json"]:
            for f in search_dir.glob(pattern):
                # Skip if older than 1 hour
                if time.time() - f.stat().st_mtime < 3600:
                    candidates.append((f.stat().st_mtime, f))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]


def _move_credentials_to_place(src: Path) -> bool:
    """Move downloaded credentials to the expected location."""
    try:
        DEFAULT_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, DEFAULT_CREDENTIALS_PATH)
        return True
    except Exception as e:
        logger.error(f"Failed to move credentials: {e}")
        return False


def _run_oauth_flow() -> Tuple[bool, str]:
    """Run the OAuth flow to get tokens (SecretStore preferred)."""
    try:
        from agent.tools.google_setup import GOOGLE_SCOPES, _run_oauth_flow as _run_flow
    except Exception as exc:
        return False, f"OAuth flow unavailable: {exc}"

    creds, message = _run_flow(GOOGLE_SCOPES)
    return bool(creds), message


def _check_already_configured() -> bool:
    """Check if Google APIs are already configured."""
    try:
        from agent.tools.google_setup import GOOGLE_SCOPES, _get_existing_credentials
    except Exception:
        return False

    creds, _ = _get_existing_credentials(GOOGLE_SCOPES)
    return creds is not None


def _log_to_reflexion(action: str, success: bool, details: str) -> None:
    """Log setup attempts to reflexion for learning."""
    try:
        from agent.autonomous.memory.reflexion import ReflexionEntry, write_reflexion

        entry = ReflexionEntry(
            id=f"gcloud_setup_{uuid4().hex[:8]}",
            timestamp=datetime.utcnow().isoformat() + "Z",
            objective="Full Google Cloud project setup for calendar access",
            context_fingerprint="google_cloud_desktop_setup",
            phase=action,
            tool_calls=[{"tool": "full_google_setup", "action": action}],
            errors=[] if success else [details],
            reflection=f"Google Cloud setup {action}: {'succeeded' if success else 'failed'} - {details}",
            fix=action if success else f"Retry or manually: {details}",
            outcome="success" if success else "failure",
            tags=["google", "oauth", "setup", "calendar", "cloud", "desktop"],
        )
        write_reflexion(entry)
    except Exception as e:
        logger.debug(f"Could not write to reflexion: {e}")


# ============================================================================
# Pydantic Models
# ============================================================================

class FullGoogleSetupArgs(BaseModel):
    """Arguments for full Google Cloud setup."""
    project_name: str = Field(
        default="treys-agent",
        description="Name for the Google Cloud project"
    )
    skip_if_configured: bool = Field(
        default=True,
        description="Skip setup if already configured"
    )
    apis_needed: List[str] = Field(
        default=["calendar", "tasks"],
        description="List of APIs to enable: 'calendar', 'tasks', or both. Determined from user request."
    )


class CheckAndFixArgs(BaseModel):
    """Arguments for check and fix tool."""
    auto_fix: bool = Field(
        default=True,
        description="Automatically fix issues when possible"
    )


# ============================================================================
# Tool Implementations
# ============================================================================

def full_google_setup(ctx, args: FullGoogleSetupArgs):
    """
    Complete Google Cloud setup using Desktop Commander.

    This opens the REAL Chrome browser and guides you through:
    1. Google Cloud Console login
    2. Project creation
    3. API enabling (Calendar, Tasks)
    4. OAuth consent screen setup
    5. OAuth credential creation
    6. Credential download
    7. OAuth flow completion

    Uses PyAutoGUI for mouse/keyboard - bypasses bot detection.
    """
    from agent.autonomous.models import ToolResult

    # Check if already configured
    if args.skip_if_configured and _check_already_configured():
        _log_to_reflexion("check_existing", True, "Already configured")
        return ToolResult(
            success=True,
            output={
                "status": "already_configured",
                "message": "Google APIs are already configured and working!",
                "credentials_path": str(DEFAULT_CREDENTIALS_PATH),
                "token_storage": "secret_store",
            },
        )

    # Check if we just need OAuth (credentials exist but no token)
    if DEFAULT_CREDENTIALS_PATH.exists() and not _check_already_configured():
        _log_to_reflexion("oauth_only", True, "Running OAuth flow")
        success, message = _run_oauth_flow()
        if success:
            return ToolResult(
                success=True,
                output={"status": "oauth_completed", "message": message},
            )
        else:
            return ToolResult(success=False, error=message, retryable=True)

    # Check PyAutoGUI
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return ToolResult(success=False, error=err, retryable=False)

    # Check OCR dependency when autoclick is enabled
    if _autoclick_enabled():
        try:
            import pytesseract  # noqa: F401
            try:
                _ = pytesseract.get_tesseract_version()
            except Exception:
                return ToolResult(
                    success=False,
                    error="Tesseract OCR engine not found. Install Tesseract and retry.",
                    retryable=True,
                )
        except Exception:
            return ToolResult(
                success=False,
                error="pytesseract is not installed. Run: pip install -r requirements.txt",
                retryable=True,
            )

    print("\n" + "=" * 60)
    print("  GOOGLE CLOUD SETUP - Desktop Commander")
    print("=" * 60)
    print("\nThis will open Chrome and guide you through Google Cloud setup.")
    print("You'll need to interact with the browser when prompted.\n")

    # Step 1: Open Chrome to Google Cloud Console
    print("[STEP 1] Opening Google Cloud Console...")
    if not _open_chrome("https://console.cloud.google.com/"):
        return ToolResult(
            success=False,
            error="Could not open Chrome. Make sure Chrome is installed.",
            retryable=True,
        )
    _take_screenshot("step1_console_opened")

    # Step 2: Wait for login (auto-detect; no prompt if already logged in)
    creds = _get_saved_google_creds()
    step_wait = int(os.getenv("TREYS_AGENT_GOOGLE_STEP_WAIT_SECONDS", "25"))
    twofa_wait = int(os.getenv("TREYS_AGENT_GOOGLE_2FA_WAIT_SECONDS", "120"))
    if not _ensure_logged_in(creds, twofa_wait=twofa_wait):
        return ToolResult(
            success=False,
            error="Google login not detected or credentials missing. Please save credentials (Cred: google) and retry.",
            retryable=True,
        )
    _take_screenshot("step2_logged_in")

    # Reasoned UI loop (observe → reason → act → verify) for setup steps
    if os.getenv("TREYS_AGENT_GOOGLE_REASONED", "1").strip().lower() in {"1", "true", "yes", "y", "on"}:
        try:
            from agent.autonomous.vision_executor import get_vision_executor
        except Exception as exc:
            return ToolResult(success=False, error=f"Vision executor unavailable: {exc}", retryable=True)

        executor = get_vision_executor()
        max_steps = int(os.getenv("TREYS_AGENT_GOOGLE_REASONING_STEPS", "80"))
        executor.max_steps = max_steps

        project_detected = _project_is_active(args.project_name)
        project_note = (
            f"Project '{args.project_name}' appears to be selected already; do NOT create a new project."
            if project_detected
            else (
                f"Project '{args.project_name}' already exists. Open the project selector and switch to it. "
                "Only create a new project if it truly does not exist."
            )
        )
        # Build API list for objective
        api_names = []
        if "calendar" in [a.lower() for a in args.apis_needed]:
            api_names.append("Google Calendar API")
        if "tasks" in [a.lower() for a in args.apis_needed]:
            api_names.append("Google Tasks API")

        api_text = " and ".join(api_names)

        objective = (
            f"Set up Google Cloud for {api_text} using the project name "
            f"'{args.project_name}'. {project_note} "
            f"Enable {api_text}. "
            "Configure OAuth consent screen as External with app name 'Treys Agent' and developer/support email set. "
            "Create OAuth Client ID for Desktop app named 'Treys Agent Desktop'. "
            "Download the JSON credentials file. If Chrome opens bookmarks or a wrong page, "
            "use the address bar to navigate back to the correct Google Cloud Console URL."
        )

        # Build context URLs
        context_urls = []
        if "calendar" in [a.lower() for a in args.apis_needed]:
            context_urls.append(f"- Calendar API: https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={args.project_name}\n")
        if "tasks" in [a.lower() for a in args.apis_needed]:
            context_urls.append(f"- Tasks API: https://console.cloud.google.com/apis/library/tasks.googleapis.com?project={args.project_name}\n")

        context = (
            "Use the Chrome address bar (Ctrl+L) to navigate. "
            "URLs:\n"
            f"- Project create: https://console.cloud.google.com/projectcreate\n"
            f"- Project home: https://console.cloud.google.com/home/dashboard?project={args.project_name}\n"
            + "".join(context_urls) +
            f"- Consent screen: https://console.cloud.google.com/apis/credentials/consent?project={args.project_name}\n"
            f"- Credentials: https://console.cloud.google.com/apis/credentials?project={args.project_name}\n"
            "If you see chrome://bookmarks, navigate to the credentials URL above. "
            "Avoid clicking the bookmarks bar. "
            "If login/2FA is required, ask the user to complete it."
        )

        # Build list of API keywords to detect based on apis_needed
        api_keywords = []
        if "calendar" in [a.lower() for a in args.apis_needed]:
            api_keywords.append("calendar api")
        if "tasks" in [a.lower() for a in args.apis_needed]:
            api_keywords.append("tasks api")
        
        steps_taken = 0
        wait_count = 0
        low_conf_count = 0
        stall_count = 0
        last_observation = ""
        low_conf_threshold = float(os.getenv("TREYS_AGENT_UI_CONFIDENCE_MIN", "0.35"))
        low_conf_steps = int(os.getenv("TREYS_AGENT_UI_LOW_CONFIDENCE_STEPS", "2"))
        stall_steps = int(os.getenv("TREYS_AGENT_UI_STALL_STEPS", "3"))
        enable_attempts = 0
        enable_skip_until_nav = False  # Skip Enable detection after too many failures
        consecutive_enable_failures = 0
        max_enable_failures = int(os.getenv("TREYS_AGENT_GOOGLE_MAX_ENABLE_FAILURES", "8"))  # Hard limit
        oauth_consent_configured = False  # Track if OAuth consent screen has been configured
        credentials_created = False  # Track if credentials have been created
        
        # WRAP ENTIRE LOOP IN TRY/EXCEPT to catch all exceptions
        try:
            while steps_taken < max_steps:
                steps_taken += 1
                
                # HARD EXIT: Stop if too many consecutive Enable failures
                if consecutive_enable_failures >= max_enable_failures:
                    error_msg = (
                        f"Failed to click Enable button after {consecutive_enable_failures} consecutive attempts. "
                        "The UI automation may be misreading the button state. "
                        "Please manually enable the APIs and re-run setup, or check the debug screenshots."
                    )
                    _debug_log(error_msg)
                    fail_shot = _take_screenshot("enable_button_hard_fail")
                    return ToolResult(
                        success=False,
                        error=error_msg + (f" Screenshot: {fail_shot}" if fail_shot else ""),
                        retryable=True,
                    )
                
                # Ensure Chrome is in focus before taking screenshot (critical for multi-monitor)
                _focus_chrome(["chrome", "google", "cloud", "console"])
                time.sleep(0.3)  # Brief pause to ensure window is actually focused
                state = executor.take_screenshot(f"gcloud_reason_{steps_taken}")
                analysis = executor.analyze_screen(objective, context)
                action_type = analysis.get("action")
                observation = (analysis.get("observation") or "").strip().lower()
                confidence = float(analysis.get("confidence", 1.0) or 0.0)

                if observation and observation == last_observation:
                    stall_count += 1
                else:
                    stall_count = 0
                    last_observation = observation

                if confidence < low_conf_threshold:
                    low_conf_count += 1
                else:
                    low_conf_count = 0

                if _debug_enabled():
                    _debug_log(f"Reasoned step {steps_taken}: {analysis}")

                # Deterministic fallback: click "Enable" when on API page
                # CRITICAL: Check if API is already enabled FIRST before trying to enable
                if not enable_skip_until_nav and _screen_has_any(api_keywords):
                    # Check if API is already enabled (MUST check this first!)
                    if _screen_has_any(["manage", "disable", "api enabled"]):
                        # API is already enabled - reset counters and skip all enable logic
                        _debug_log("API already enabled (Manage/Disable/API Enabled detected) - skipping enable logic")
                        enable_attempts = 0
                        consecutive_enable_failures = 0
                        enable_skip_until_nav = False  # Reset skip flag so we can navigate
                        # Let vision executor handle navigation to next API or credentials page
                        # Don't block here - continue to vision executor
                    # Only try to enable if API is NOT already enabled AND we see "enable" button text
                    elif _screen_has_any(["enable"]) and not _screen_has_any(["manage", "disable", "api enabled"]):
                        enable_attempts += 1
                        consecutive_enable_failures += 1
                        
                        # HARD EXIT CHECK: If we've hit max failures, exit immediately
                        if consecutive_enable_failures >= max_enable_failures:
                            error_msg = (
                                f"Failed to click Enable button after {consecutive_enable_failures} consecutive attempts. "
                                "Please manually enable the APIs and re-run setup."
                            )
                            _debug_log(error_msg)
                            fail_shot = _take_screenshot("enable_button_hard_fail")
                            return ToolResult(
                                success=False,
                                error=error_msg + (f" Screenshot: {fail_shot}" if fail_shot else ""),
                                retryable=True,
                            )
                        
                        _debug_log(f"Enable button detected on API page (attempt {enable_attempts})")
                        # IMPROVEMENT: Use OCR first to find exact Enable button coordinates
                        # Search for standalone "Enable" button, not "enable" within other text
                        _debug_log("Step 1 (deterministic): Using OCR to find exact 'Enable' button coordinates...")
                        executor.take_screenshot("enable_button_ocr_search")
                        # Search for button text that's more specific - look for standalone "Enable" button
                        ocr_coords = _find_button_coordinates_ocr(["enable button", "enable api", "^enable$"])
                        
                        clicked = False
                        click_result = None
                        ocr_x, ocr_y = None, None
                        x, y = None, None
                        
                        # Try OCR coordinates first (more accurate)
                        if ocr_coords:
                            ocr_x, ocr_y = ocr_coords
                            _debug_log(f"OCR found Enable button at: ({ocr_x}, {ocr_y})")
                            _focus_chrome(["chrome", "google", "cloud"])
                            time.sleep(0.3)
                            click_result = _click_at(ocr_x, ocr_y)
                            clicked = click_result.get("success", False)
                            _debug_log(f"OCR-based click result: method={click_result.get('method_used')}, "
                                     f"success={clicked}, distance={click_result.get('distance_from_target', 0):.1f}px")
                            _save_debug_screenshot_with_coords("enable_button_click_ocr", ocr_x, ocr_y, click_result)
                        
                        # Fallback: Try using coordinates from vision analysis if OCR didn't work
                        if not clicked:
                            target = analysis.get("target", {})
                            if isinstance(target, dict) and target.get("x") and target.get("y"):
                                try:
                                    x, y = int(float(target.get("x", 0))), int(float(target.get("y", 0)))
                                    if x > 0 and y > 0:
                                        _debug_log(f"OCR failed, trying vision-provided coordinates: ({x}, {y})")
                                        _focus_chrome(["chrome", "google", "cloud"])
                                        time.sleep(0.3)
                                        click_result = _click_at(x, y)
                                        clicked = click_result.get("success", False)
                                        _debug_log(f"Vision-based click result: method={click_result.get('method_used')}, "
                                                 f"success={clicked}, distance={click_result.get('distance_from_target', 0):.1f}px, "
                                                 f"converted={click_result.get('conversion_applied')}")
                                        _save_debug_screenshot_with_coords("enable_button_click_vision", x, y, click_result)
                                except Exception as exc:
                                    _debug_log(f"Coordinate click exception: {exc}")
                        
                        if clicked:
                            _debug_log(f"Clicked Enable button successfully")
                            # Verify immediately instead of just waiting
                            # Wait a bit longer for state change
                            time.sleep(2)
                            verify_success, verify_msg = _verify_click_success(
                                executor,
                                "Enable button should change to Manage/Disable"
                            )
                            _debug_log(f"Enable button verification (deterministic): {verify_msg}")
                            if verify_success:
                                enable_attempts = 0
                                consecutive_enable_failures = 0
                                enable_skip_until_nav = False
                                wait_count = 0
                                continue
                            else:
                                _debug_log(f"Verification failed - consecutive failures: {consecutive_enable_failures}")
                                # TROUBLESHOOTING: Try troubleshooting if verification failed
                                if click_result:
                                    troubleshoot_coords = _troubleshoot_failed_click(executor, "enable", 
                                        (ocr_x if ocr_coords else (x if x else 0), 
                                         ocr_y if ocr_coords else (y if y else 0)), 
                                        click_result)
                                    if troubleshoot_coords:
                                        _debug_log(f"Troubleshooting found alternative coordinates, retrying...")
                                        click_result = _click_at(*troubleshoot_coords)
                                        verify_success, verify_msg = _verify_click_success(executor, "Enable button should change")
                                        if verify_success:
                                            enable_attempts = 0
                                            consecutive_enable_failures = 0
                                            enable_skip_until_nav = False
                                            wait_count = 0
                                            continue
                        time.sleep(1)  # Brief wait if verification unclear
                        
                        # Fallback to OCR-based click if coordinate click didn't work or wasn't available
                        if not clicked:
                            _debug_log("Trying OCR-based Enable button click")
                            clicked = _auto_click_main(["enable", "enable api", "enable to"], attempts=3, delay=0.8)
                            if clicked:
                                _debug_log("OCR-based Enable click succeeded")
                        if clicked:
                            wait_count = 0
                            # Verify click success immediately
                            time.sleep(2)  # Wait for state change
                            verify_success, verify_msg = _verify_click_success(
                                executor,
                                "Enable button should change to Manage/Disable"
                            )
                            _debug_log(f"Enable button verification: {verify_msg}")
                            
                            if verify_success or _wait_for_any(["manage", "disable", "api enabled"], timeout_seconds=6):
                                enable_attempts = 0
                                consecutive_enable_failures = 0
                                enable_skip_until_nav = False
                                _debug_log("Enable button click successful - API enabled")
                                continue
                            else:
                                _debug_log(f"Click executed but state hasn't changed yet - consecutive failures: {consecutive_enable_failures}")
                        
                        # If still not enabled after attempts, try pressing Enter in case button is focused
                        if enable_attempts >= 2 and not clicked:
                            _debug_log("Trying Enter key as fallback")
                            _focus_chrome(["chrome", "google", "cloud"])
                            _press_key("enter")
                            time.sleep(2)
                            if _wait_for_any(["manage", "disable", "api enabled"], timeout_seconds=6):
                                enable_attempts = 0
                                consecutive_enable_failures = 0  # Reset on success
                                _debug_log("Enter key press successful - API enabled")
                                continue
                        
                        if enable_attempts >= 3 or consecutive_enable_failures >= 5:
                            _debug_log(f"Enable button click failed after {enable_attempts} attempts, {consecutive_enable_failures} consecutive failures")
                            
                            # Skip Enable button detection until we navigate away (to prevent infinite loop)
                            enable_skip_until_nav = True
                            _debug_log("Skipping Enable button detection until navigation occurs (to prevent infinite loop)")
                            
                            guidance = _prompt_user_guidance(
                                f"I've tried clicking the Enable button {enable_attempts} times but it's not working. "
                                f"Please click Enable manually and type 'continue', or tell me what to do next. "
                                f"You can also say 'navigate to <url>' to move to a different page."
                            )
                            if guidance:
                                context = f"{context}\nUser said: {guidance}"
                                # If user says navigate or provides a URL, reset skip flag
                                if "navigate" in guidance.lower() or "goto" in guidance.lower() or "http" in guidance.lower():
                                    enable_skip_until_nav = False
                                    consecutive_enable_failures = 0  # Reset when user guides navigation
                            enable_attempts = 0  # Reset counter but keep skip flag
                            continue

                # Prevent unnecessary ask_user prompts for simple Enable button clicks
                if action_type == "ask_user":
                    # If we can handle it deterministically, don't ask user
                    # Check if observation mentions any of the APIs we're setting up
                    observation_has_api = any(api_kw in observation for api_kw in api_keywords)
                    if "enable" in observation or observation_has_api:
                        if _screen_has_any(["enable"]) and not _screen_has_any(["manage", "disable", "api enabled"]):
                            # Try to enable automatically
                            if _auto_click_main(["enable", "enable api"], attempts=2):
                                time.sleep(2)
                                if _wait_for_any(["manage", "disable", "api enabled"], timeout_seconds=6):
                                    consecutive_enable_failures = 0  # Reset on success
                                    continue
                    # For navigation, don't ask - just do it
                    # Check if observation mentions any of the APIs we're setting up
                    observation_has_api = any(api_kw in observation for api_kw in api_keywords)
                    if "navigate" in observation.lower() or "goto" in observation.lower() or observation_has_api:
                        if observation_has_api:
                            # Navigate to the appropriate API page based on which API is mentioned
                            if "tasks api" in observation and "tasks" in [a.lower() for a in args.apis_needed]:
                                _navigate_chrome(f"https://console.cloud.google.com/apis/library/tasks.googleapis.com?project={args.project_name}")
                            elif "calendar api" in observation and "calendar" in [a.lower() for a in args.apis_needed]:
                                _navigate_chrome(f"https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={args.project_name}")
                            consecutive_enable_failures = 0  # Reset on navigation
                            continue
                        if "calendar api" in observation:
                            _navigate_chrome(f"https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={args.project_name}")
                            consecutive_enable_failures = 0  # Reset on navigation
                            continue

                # Bookmarks recovery
                if _screen_has_any(["bookmarks"]) and not _screen_has_any(["google cloud"]):
                    _navigate_chrome(f"https://console.cloud.google.com/apis/credentials?project={args.project_name}")
                    wait_count = 0
                    consecutive_enable_failures = 0  # Reset on navigation
                    continue

                # AUTOMATIC CREDENTIALS PAGE HANDLING
                # Detect if we're on the credentials page
                if _screen_has_any(["credentials", "oauth 2.0 client ids", "create credentials"]) and _screen_has_any(["api keys", "oauth", "service accounts"]):
                    _debug_log("Detected credentials page")
                    
                    # Check if we need to configure OAuth consent screen first
                    if not oauth_consent_configured and _screen_has_any(["configure consent screen", "remember to configure"]):
                        _debug_log("OAuth consent screen not configured yet - navigating to consent screen")
                        _navigate_chrome(f"https://console.cloud.google.com/apis/credentials/consent?project={args.project_name}")
                        wait_count = 0
                        consecutive_enable_failures = 0
                        continue
                    
                    # If consent screen is configured (or not needed), click Create Credentials
                    if not credentials_created and _screen_has_any(["create credentials", "+ create"]):
                        _debug_log("Clicking Create Credentials button")
                        if _auto_click_main(["create credentials", "+ create"], attempts=3):
                            time.sleep(2)
                            # Check if we're now on the credential type selection
                            if _screen_has_any(["oauth client id", "application type", "desktop app"]):
                                _debug_log("Credential creation dialog opened")
                                # Click OAuth Client ID
                                if _auto_click_main(["oauth client id"], attempts=2):
                                    time.sleep(2)
                                    # Select Desktop app
                                    if _screen_has_any(["application type", "desktop app", "web application"]):
                                        if _auto_click_main(["desktop app"], attempts=2):
                                            time.sleep(1)
                                            # Fill in name
                                            _fill_field_by_label(["name"], "Treys Agent Desktop")
                                            time.sleep(0.5)
                                            # Click Create
                                            if _auto_click_main(["create"], attempts=2):
                                                time.sleep(3)
                                                # Download JSON
                                                if _screen_has_any(["download json", "download"]):
                                                    if _auto_click_main(["download json", "download"], attempts=2):
                                                        time.sleep(2)
                                                        # Click OK/Done
                                                        _auto_click_main(["ok", "done"], attempts=2)
                                                        credentials_created = True
                                                        _debug_log("Credentials created and downloaded successfully")
                                                        continue
                        # If automatic creation failed, continue to vision executor
                        _debug_log("Automatic credential creation failed - will use vision executor")
                
                # AUTOMATIC OAUTH CONSENT SCREEN HANDLING
                if _screen_has_any(["oauth consent screen", "consent screen", "publishing status"]) and not oauth_consent_configured:
                    _debug_log("Detected OAuth consent screen page")
                    
                    # Check if already configured (has "Edit App" or "Publishing status")
                    if _screen_has_any(["edit app", "publishing status", "configured", "in production"]):
                        _debug_log("OAuth consent screen already configured")
                        oauth_consent_configured = True
                        # Navigate to credentials page
                        _navigate_chrome(f"https://console.cloud.google.com/apis/credentials?project={args.project_name}")
                        wait_count = 0
                        consecutive_enable_failures = 0
                        continue
                    
                    # Need to configure - click External
                    if _screen_has_any(["external", "internal", "user type"]):
                        _debug_log("Configuring OAuth consent screen - selecting External")
                        if _auto_click_main(["external"], attempts=2):
                            time.sleep(1)
                            # Click Create
                            if _auto_click_main(["create"], attempts=2):
                                time.sleep(2)
                                # Fill app name
                                if _screen_has_any(["app name", "application name"]):
                                    email = (creds or {}).get("username") or ""
                                    _fill_field_by_label(["app name", "application name"], "Treys Agent")
                                    time.sleep(0.5)
                                    # Fill user support email
                                    if _screen_has_any(["user support email", "support email", "email"]):
                                        _fill_field_by_label(["user support email", "support email"], email)
                                    time.sleep(0.5)
                                    # Fill developer contact email
                                    if _screen_has_any(["developer contact", "developer email"]):
                                        _fill_field_by_label(["developer contact", "developer email"], email)
                                    time.sleep(0.5)
                                    # Save and Continue (might need to click multiple times)
                                    for _ in range(3):
                                        if _screen_has_any(["save and continue", "continue", "next"]):
                                            if _auto_click_main(["save and continue", "continue", "next"], attempts=2):
                                                time.sleep(2)
                                        else:
                                            break
                                    oauth_consent_configured = True
                                    _debug_log("OAuth consent screen configured - navigating to credentials")
                                    # Navigate to credentials page
                                    _navigate_chrome(f"https://console.cloud.google.com/apis/credentials?project={args.project_name}")
                                    wait_count = 0
                                    consecutive_enable_failures = 0
                                    continue

                if action_type == "done":
                    break
                if action_type == "ask_user":
                    answer = _prompt_user_guidance(
                        analysis.get("value", "Need help. You can say: click enable / open <url> / continue."),
                    )
                    if answer:
                        context = f"{context}\nUser said: {answer}"
                    continue
                if action_type == "goto":
                    url = analysis.get("value") or ""
                    if url:
                        # Navigation occurred - reset Enable skip flag
                        if enable_skip_until_nav:
                            _debug_log("Navigation detected - resetting Enable button skip flag")
                            enable_skip_until_nav = False
                            consecutive_enable_failures = 0  # Reset on navigation
                        _navigate_chrome(url)
                    else:
                        context = f"{context}\nPrevious action failed: missing URL for goto."
                    continue
                if action_type == "error":
                    return ToolResult(
                        success=False,
                        error=analysis.get("value", "Reasoned UI loop reported error"),
                        retryable=True,
                    )
                
                # Handle click actions directly when we have coordinates (more reliable than vision executor)
                if action_type == "click":
                    target = analysis.get("target", {})
                    observation_lower = observation.lower()
                    _debug_log(f"Click action detected, target: {target}, action_type: {action_type}, observation: {observation[:100]}")
                    
                    # Extract button text from observation for troubleshooting
                    button_text = None
                    if "enable" in observation_lower:
                        button_text = "enable"
                    elif "manage" in observation_lower:
                        button_text = "manage"
                    
                    if isinstance(target, dict) and target.get("x") and target.get("y"):
                        try:
                            x, y = int(float(target.get("x", 0))), int(float(target.get("y", 0)))
                            _debug_log(f"Attempting direct click at vision-provided coordinates: ({x}, {y})")
                            if x > 0 and y > 0:
                                _focus_chrome(["chrome", "google", "cloud"])
                                time.sleep(0.4)
                                
                                # IMPROVEMENT: Use OCR to verify/find exact coordinates before clicking
                                if button_text:
                                    _debug_log(f"Step 1: Using OCR to find exact '{button_text}' button coordinates...")
                                    executor.take_screenshot("pre_click_ocr_search")
                                    ocr_coords = _find_button_coordinates_ocr([button_text, f"{button_text} api"])
                                    if ocr_coords:
                                        ocr_x, ocr_y = ocr_coords
                                        vision_distance = ((ocr_x - x) ** 2 + (ocr_y - y) ** 2) ** 0.5
                                        _debug_log(f"OCR found button at ({ocr_x}, {ocr_y}), vision said ({x}, {y}), distance: {vision_distance:.1f}px")
                                        
                                        # If OCR coordinates are significantly different, use OCR coordinates
                                        if vision_distance > 30:  # More than 30px difference
                                            _debug_log(f"OCR coordinates differ by {vision_distance:.1f}px - using OCR coordinates instead")
                                            x, y = ocr_x, ocr_y
                                        elif vision_distance > 10:
                                            _debug_log(f"Coordinates differ by {vision_distance:.1f}px - trying OCR coordinates first")
                                            # Try OCR first, then fall back to vision
                                            original_x, original_y = x, y
                                            x, y = ocr_x, ocr_y
                                
                                # Click and get detailed result
                                click_result = _click_at(x, y)
                                _debug_log(f"Click result: method={click_result.get('method_used')}, "
                                         f"success={click_result.get('success')}, "
                                         f"distance={click_result.get('distance_from_target', 0):.1f}px, "
                                         f"mouse_pos={click_result.get('mouse_position_after')}, "
                                         f"converted={click_result.get('conversion_applied')}")
                                
                                # Save debug screenshot with coordinate overlay
                                _save_debug_screenshot_with_coords("click_attempt", x, y, click_result)
                                
                                # If mouse didn't reach target, try alternative approach
                                if click_result.get("success") and click_result.get("distance_from_target", float('inf')) > 10:
                                    _debug_log(f"WARNING: Click reported success but mouse is {click_result.get('distance_from_target', 0):.1f}px away from target")
                                    _debug_log("Attempting alternative click method...")
                                    # Try pressing Enter as fallback if button might be focused
                                    _press_key("enter")
                                    time.sleep(1)
                                
                                if click_result.get("success"):
                                    _debug_log(f"Direct click executed at coordinates: ({x}, {y}) using {click_result.get('method_used')}")
                                    
                                    # Immediate post-click verification
                                    verify_success, verify_msg = _verify_click_success(
                                        executor, 
                                        "Enable button should change to Manage/Disable"
                                    )
                                    _debug_log(f"Post-click verification: {verify_msg}")
                                    
                                    # TROUBLESHOOTING: If click succeeded but verification failed, try troubleshooting
                                    if not verify_success and button_text:
                                        _debug_log("Click succeeded but verification failed - troubleshooting...")
                                        troubleshoot_coords = _troubleshoot_failed_click(executor, button_text, (x, y), click_result)
                                        if troubleshoot_coords:
                                            new_x, new_y = troubleshoot_coords
                                            _debug_log(f"Troubleshooting found new coordinates: ({new_x}, {new_y}), retrying click...")
                                            click_result = _click_at(new_x, new_y)
                                            verify_success, verify_msg = _verify_click_success(executor, "Enable button should change to Manage/Disable")
                                            _debug_log(f"Troubleshoot retry verification: {verify_msg}")
                                    
                                    if verify_success:
                                        # Take one more screenshot and re-analyze to confirm
                                        executor.take_screenshot("post_click_confirmed")
                                        
                                        # Double-check with vision executor
                                        re_analysis = executor.analyze_screen(
                                            "Is the Enable button still visible, or has it changed to Manage/Disable?",
                                            "We just clicked the Enable button. Verify the state changed."
                                        )
                                        re_observation = (re_analysis.get("observation") or "").strip().lower()
                                        
                                        if "manage" in re_observation or "disable" in re_observation or "enabled" in re_observation:
                                            _debug_log("Verification confirmed: Button state changed successfully")
                                            wait_count = 0
                                            enable_attempts = 0
                                            consecutive_enable_failures = 0  # Reset on success
                                            enable_skip_until_nav = False
                                            continue
                                        elif "enable" in re_observation and "button" in re_observation:
                                            _debug_log("Verification failed: Enable button still visible after click")
                                            # Don't increment here - already incremented at start of Enable detection
                                            # If too many failures, skip Enable detection
                                            if consecutive_enable_failures >= 5:
                                                enable_skip_until_nav = True
                                                _debug_log(f"Too many consecutive failures ({consecutive_enable_failures}), skipping Enable detection")
                                            # Click may have failed - continue to retry logic
                                        else:
                                            _debug_log("Verification unclear: Page state unknown, assuming success")
                                            wait_count = 0
                                            consecutive_enable_failures = 0  # Reset on success
                                            enable_skip_until_nav = False
                                            continue
                                    else:
                                        _debug_log("Post-click verification failed - click may not have worked")
                                        # Don't increment here - already incremented at start of Enable detection
                                        if consecutive_enable_failures >= 5:
                                            enable_skip_until_nav = True
                                        # Continue to retry or ask user
                                    
                                    # Additional state check
                                    if _screen_has_any(api_keywords):
                                        if _wait_for_any(["manage", "disable", "enabled"], timeout_seconds=3):
                                            _debug_log("Click successful - API enabled/state changed (confirmed by OCR)")
                                            wait_count = 0
                                            enable_attempts = 0
                                            consecutive_enable_failures = 0  # Reset on success
                                            continue
                                        else:
                                            _debug_log("Still showing Enable button - click may have failed")
                                    else:
                                        # Not on API page anymore, assume click worked and navigated away
                                        _debug_log("No longer on API page, assuming click succeeded")
                                        wait_count = 0
                                        consecutive_enable_failures = 0  # Reset on navigation
                                        continue
                                else:
                                    _debug_log(f"Click failed: method={click_result.get('method_used')}, "
                                             f"distance={click_result.get('distance_from_target', 0):.1f}px")
                                    _debug_log("Coordinate click failed - falling through to vision executor")
                        except Exception as exc:
                            _debug_log(f"Coordinate click exception: {exc}")
                            import traceback
                            _debug_log(traceback.format_exc())

                success, message = executor.execute_action(analysis)
                if not success:
                    context = f"{context}\nPrevious action failed: {message}"
                    continue

                if action_type == "wait":
                    wait_count += 1
                else:
                    wait_count = 0

                if (wait_count >= 3) or (low_conf_count >= low_conf_steps) or (stall_count >= stall_steps):
                    guidance = _prompt_user_guidance(
                        "I may be stuck. If you see the Enable button, click it and type 'continue'. "
                        "Or tell me: open <url> / click enable."
                    )
                    if guidance:
                        context = f"{context}\nUser said: {guidance}"
                    wait_count = 0
                    low_conf_count = 0
                    stall_count = 0
                    continue
            
            # Loop exited without completing (max_steps reached)
            _debug_log(f"Reasoned UI loop completed {steps_taken} steps but setup may be incomplete")
            fail_shot = _take_screenshot("reasoned_loop_max_steps_reached")
            return ToolResult(
                success=False,
                error=(
                    f"Setup automation reached maximum steps ({max_steps}) without completing. "
                    f"Enable failures: {consecutive_enable_failures}. "
                    "Please check the current state and manually complete setup if needed."
                    + (f" Screenshot: {fail_shot}" if fail_shot else "")
                ),
                retryable=True,
            )
            
        except Exception as exc:
            # CATCH ALL EXCEPTIONS IN THE LOOP
            import traceback
            error_trace = traceback.format_exc()
            _debug_log(f"Exception in reasoned UI loop: {exc}")
            _debug_log(error_trace)
            fail_shot = _take_screenshot("reasoned_loop_exception")
            return ToolResult(
                success=False,
                error=(
                    f"Exception during Google Cloud setup automation: {exc}\n"
                    f"Steps taken: {steps_taken}, Enable failures: {consecutive_enable_failures}\n"
                    f"Check debug logs for details."
                    + (f" Screenshot: {fail_shot}" if fail_shot else "")
                ),
                retryable=True,
            )

    else:
        # Fallback to scripted flow (legacy)
        if _project_is_active(args.project_name):
            print("\n[STEP 2] Project already selected; continuing...")
            _take_screenshot("step2_project_selected")
        else:
            print("\n[STEP 2] Opening project dashboard to select existing project...")
            _navigate_chrome(
                f"https://console.cloud.google.com/home/dashboard?project={args.project_name}",
                expect_tokens=["google", "cloud"],
            )
            time.sleep(2)
            if _project_is_active(args.project_name):
                _take_screenshot("step2_project_dashboard")
            else:
                print("\n[STEP 2B] Project not detected; navigating to project creation as fallback...")
                _navigate_chrome(
                    "https://console.cloud.google.com/projectcreate",
                    expect_tokens=["project", "create", "google cloud"],
                )
                time.sleep(2)
                if not _screen_has_any(["google", "cloud", "project"]):
                    fail_shot = _take_screenshot("step3_project_create_not_visible")
                    return ToolResult(
                        success=False,
                        error=(
                            "Chrome/Cloud Console not visible in foreground. "
                            "Please ensure Chrome is visible and retry."
                            + (f" Screenshot: {fail_shot}" if fail_shot else "")
                        ),
                        retryable=True,
                    )
                _take_screenshot("step3_project_create")
                created = False
                if _autoclick_enabled():
                    created = _attempt_project_creation(args.project_name)
                    if not created:
                        time.sleep(1)
                        created = _attempt_project_creation(args.project_name)
                if not created:
                    fail_shot = _take_screenshot("step4_project_create_failed")
                    manual_ok = _prompt_manual_or_fail(
                        f"Create a new project:\n"
                        f"1. Enter project name: {args.project_name}\n"
                        f"2. Click 'Create'\n"
                        f"3. Wait for project to be created\n\n"
                        f"Complete these steps in the browser.",
                        seconds=step_wait,
                    )
                    if not manual_ok:
                        return ToolResult(
                            success=False,
                            error=(
                                "Auto-creation failed: could not locate the Project Name field or Create button."
                                + (f" Screenshot: {fail_shot}" if fail_shot else "")
                            ),
                            retryable=True,
                        )
                _take_screenshot("step4_project_created")
        
        # Enable Calendar API if needed
        if "calendar" in [a.lower() for a in args.apis_needed]:
            print("\n[STEP 3] Enabling Calendar API...")
            _navigate_chrome(
                f"https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={args.project_name}",
                expect_tokens=["calendar", "api", "google cloud"],
            )
            time.sleep(2)
            _focus_chrome(["calendar", "google", "cloud"])
            if _autoclick_enabled():
                _wait_for_any(["enable", "manage", "disable", "api", "calendar"], timeout_seconds=12, interval=1.0)
                enabled_tokens = ["api enabled", "manage", "disable", "enabled"]
                enabled = _screen_has_any(enabled_tokens)
                if not enabled:
                    enabled = _auto_click_text(["enable", "enable api", "enable to", "activate"], attempts=4, delay=0.9)
                if not enabled:
                    _press_key("pagedown")
                    time.sleep(1)
                    enabled = _auto_click_text(["enable", "enable api", "enable to", "activate"], attempts=2, delay=0.9)
                if not enabled:
                    fail_shot = _take_screenshot("step5_calendar_enable_failed")
                    manual_ok = _prompt_manual_or_fail(
                        "Click 'Enable' to enable the Google Calendar API.",
                        seconds=step_wait,
                    )
                    if not manual_ok:
                        return ToolResult(
                            success=False,
                            error=(
                                "Auto-enable failed: could not locate the Enable button for Calendar API."
                                + (f" Screenshot: {fail_shot}" if fail_shot else "")
                            ),
                            retryable=True,
                        )
            else:
                manual_ok = _prompt_manual_or_fail(
                    "Click 'Enable' to enable the Google Calendar API.",
                    seconds=step_wait,
                )
                if not manual_ok:
                    return ToolResult(
                        success=False,
                        error="Auto-enable disabled and manual fallback not allowed.",
                        retryable=True,
                    )
            _take_screenshot("step5_calendar_enabled")
        
        # Enable Tasks API if needed
        if "tasks" in [a.lower() for a in args.apis_needed]:
            print("\n[STEP 4] Enabling Tasks API...")
            _navigate_chrome(
                f"https://console.cloud.google.com/apis/library/tasks.googleapis.com?project={args.project_name}",
                expect_tokens=["tasks", "api", "google cloud"],
            )
            time.sleep(2)
            _focus_chrome(["tasks", "google", "cloud"])
            if _autoclick_enabled():
                _wait_for_any(["enable", "manage", "disable", "api", "tasks"], timeout_seconds=12, interval=1.0)
                enabled_tokens = ["api enabled", "manage", "disable", "enabled"]
                enabled = _screen_has_any(enabled_tokens)
                if not enabled:
                    enabled = _auto_click_text(["enable", "enable api", "enable to", "activate"], attempts=4, delay=0.9)
                if not enabled:
                    _press_key("pagedown")
                    time.sleep(1)
                    enabled = _auto_click_text(["enable", "enable api", "enable to", "activate"], attempts=2, delay=0.9)
                if not enabled:
                    fail_shot = _take_screenshot("step6_tasks_enable_failed")
                    manual_ok = _prompt_manual_or_fail(
                        "Click 'Enable' to enable the Google Tasks API.",
                        seconds=step_wait,
                    )
                    if not manual_ok:
                        return ToolResult(
                            success=False,
                            error=(
                                "Auto-enable failed: could not locate the Enable button for Tasks API."
                                + (f" Screenshot: {fail_shot}" if fail_shot else "")
                            ),
                            retryable=True,
                        )
            else:
                manual_ok = _prompt_manual_or_fail(
                    "Click 'Enable' to enable the Google Tasks API.",
                    seconds=step_wait,
                )
                if not manual_ok:
                    return ToolResult(
                        success=False,
                        error="Auto-enable disabled and manual fallback not allowed.",
                        retryable=True,
                    )
                return ToolResult(
                    success=False,
                    error="Auto-enable disabled and manual fallback not allowed.",
                    retryable=True,
                )
        _take_screenshot("step6_tasks_enabled")
        print("\n[STEP 5] Configuring OAuth consent screen...")
        _navigate_chrome(
            f"https://console.cloud.google.com/apis/credentials/consent?project={args.project_name}",
            expect_tokens=["consent", "oauth", "google cloud"],
        )
        time.sleep(3)
        _focus_chrome(["consent", "oauth", "google", "cloud"])
        if _autoclick_enabled():
            if not _screen_has_any(["publishing status", "oauth consent screen", "edit app"]):
                _auto_click_main(["external"])
                _auto_click_main(["create"])
                time.sleep(2)
            email = (creds or {}).get("username") or ""
            _fill_field_by_label(["app", "name"], "Treys Agent")
            if email:
                _fill_field_by_label(["support", "email"], email)
                _fill_field_by_label(["developer", "contact"], email)
            for _ in range(3):
                _auto_click_main(["save and continue", "save & continue"])
                time.sleep(2)
            if email and _screen_has_any(["test users", "add users"]):
                _fill_field_by_label(["add users", "test users"], email)
                _press_key("enter")
                _auto_click_main(["save and continue", "save & continue"])
                time.sleep(2)
            _auto_click_main(["back to dashboard"])
        else:
            manual_ok = _prompt_manual_or_fail(
                "Configure the OAuth consent screen manually.",
                seconds=step_wait * 2,
            )
            if not manual_ok:
                return ToolResult(
                    success=False,
                    error="Auto-consent setup disabled and manual fallback not allowed.",
                    retryable=True,
                )
        _take_screenshot("step7_consent_configured")
        print("\n[STEP 6] Creating OAuth credentials...")
        if _autoclick_enabled():
            success = False
            for _ in range(2):
                _navigate_chrome(
                    f"https://console.cloud.google.com/apis/credentials?project={args.project_name}",
                    expect_tokens=["credentials", "oauth", "google cloud"],
                )
                time.sleep(3)
                _focus_chrome(["credentials", "oauth", "google", "cloud"])
                if _screen_has_any(["bookmarks", "chrome://bookmarks"]):
                    _debug_log("Detected bookmarks page; re-navigating to credentials.")
                    continue
                _auto_click_main(["create credentials"])
                time.sleep(1)
                if _screen_has_any(["bookmarks", "chrome://bookmarks"]):
                    _debug_log("Bookmarks page opened after Create Credentials; retrying.")
                    continue
                _auto_click_main(["oauth client id"])
                time.sleep(2)
                _auto_click_main(["application type"])
                time.sleep(1)
                _auto_click_main(["desktop app"])
                _fill_field_by_label(["name"], "Treys Agent Desktop")
                _auto_click_main(["create"])
                time.sleep(2)
                _auto_click_main(["download json", "download"])
                time.sleep(1)
                _auto_click_main(["ok", "done"])
                success = True
                break
            if not success:
                fail_shot = _take_screenshot("step8_oauth_create_failed")
                return ToolResult(
                    success=False,
                    error=(
                        "Failed to create OAuth credentials; page navigation was unstable (bookmarks page)."
                        + (f" Screenshot: {fail_shot}" if fail_shot else "")
                    ),
                    retryable=True,
                )
        else:
            manual_ok = _prompt_manual_or_fail(
                "Create OAuth credentials manually.",
                seconds=step_wait,
            )
            if not manual_ok:
                return ToolResult(
                    success=False,
                    error="Auto-credential creation disabled and manual fallback not allowed.",
                    retryable=True,
                )
        _take_screenshot("step8_oauth_created")
        _take_screenshot("step9_downloaded")

    # Step 10: Find and move credentials
    print("\n[STEP 7] Looking for downloaded credentials...")
    time.sleep(2)  # Give filesystem time to update

    creds_file = _find_downloaded_credentials()
    if creds_file:
        print(f"Found credentials at: {creds_file}")
        if _move_credentials_to_place(creds_file):
            print(f"Moved to: {DEFAULT_CREDENTIALS_PATH}")
            _log_to_reflexion("credentials_saved", True, f"Saved from {creds_file}")
        else:
            return ToolResult(
                success=False,
                error=f"Found credentials but failed to move to {DEFAULT_CREDENTIALS_PATH}",
                retryable=True,
            )
    else:
        # Attempt recovery: dialogs, chrome://downloads, history lookup
        recovered = _recover_downloaded_credentials()
        if recovered and recovered.exists():
            print(f"Recovered credentials at: {recovered}")
            if _move_credentials_to_place(recovered):
                print(f"Moved to: {DEFAULT_CREDENTIALS_PATH}")
                _log_to_reflexion("credentials_saved", True, f"Recovered from {recovered}")
            else:
                return ToolResult(
                    success=False,
                    error=f"Recovered credentials but failed to move to {DEFAULT_CREDENTIALS_PATH}",
                    retryable=True,
                )
        else:
            if not _manual_fallback_allowed():
                return ToolResult(
                    success=False,
                    error="Downloaded credentials not found automatically. Manual fallback is disabled.",
                    retryable=True,
                )
            manual_path = _wait_and_prompt(
                f"Could not find the downloaded credentials.\n"
                f"Please enter the full path to the downloaded JSON file\n"
                f"(or press Enter to check Downloads folder again):"
            )
            if manual_path:
                src = Path(manual_path)
                if src.exists():
                    _move_credentials_to_place(src)
                else:
                    return ToolResult(
                        success=False,
                        error=f"File not found: {manual_path}",
                        retryable=True,
                    )
            else:
                # Try again
                creds_file = _find_downloaded_credentials()
                if creds_file:
                    _move_credentials_to_place(creds_file)
                else:
                    return ToolResult(
                        success=False,
                        error=f"Please manually copy the client_secret*.json to: {DEFAULT_CREDENTIALS_PATH}",
                        retryable=True,
                    )

    # Step 11: Run OAuth flow
    print("\n[STEP 8] Completing OAuth flow...")
    print("A browser window will open for you to grant permissions.\n")

    success, message = _run_oauth_flow()

    if success:
        _log_to_reflexion("setup_complete", True, "Full setup completed")
        print("\n" + "=" * 60)
        print("  SETUP COMPLETE!")
        print("=" * 60)
        return ToolResult(
            success=True,
            output={
                "status": "setup_complete",
                "message": "Google Cloud project created and configured!",
                "project_name": args.project_name,
                "credentials_path": str(DEFAULT_CREDENTIALS_PATH),
                "token_storage": "secret_store",
                "apis_enabled": ["Calendar", "Tasks"],
            },
        )
    else:
        _log_to_reflexion("oauth_failed", False, message)
        return ToolResult(
            success=False,
            error=message,
            retryable=True,
        )


def check_and_fix_google_setup(ctx, args: CheckAndFixArgs):
    """
    Diagnose and fix Google API setup issues.

    Checks:
    1. Google libraries installed
    2. OAuth credentials file exists
    3. Token exists (SecretStore or file) and is valid
    """
    from agent.autonomous.models import ToolResult

    issues = []
    fixes_applied = []

    # Check 1: Libraries
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:
        issues.append(f"Missing Google libraries: {e}")

    # Check 2: Credentials file
    if not DEFAULT_CREDENTIALS_PATH.exists():
        issues.append(f"OAuth credentials missing: {DEFAULT_CREDENTIALS_PATH}")

        if args.auto_fix:
            found = _find_downloaded_credentials()
            if found and _move_credentials_to_place(found):
                fixes_applied.append(f"Moved credentials from {found}")
                issues.remove(f"OAuth credentials missing: {DEFAULT_CREDENTIALS_PATH}")

    # Check 3: Token validity (SecretStore preferred)
    if DEFAULT_CREDENTIALS_PATH.exists():
        try:
            from agent.tools.google_setup import GOOGLE_SCOPES, _get_existing_credentials
            creds, msg = _get_existing_credentials(GOOGLE_SCOPES)
            if creds is None:
                issues.append(f"Need to complete OAuth flow ({msg})")
        except Exception as e:
            issues.append(f"Token check failed: {e}")

    # If we were able to refresh in _get_existing_credentials, note it
    # (No additional action needed here.)

    if not issues:
        return ToolResult(
            success=True,
            output={
                "status": "configured",
                "message": "Google APIs are ready!",
                "fixes_applied": fixes_applied,
            },
        )
    else:
        return ToolResult(
            success=False,
            error="Setup incomplete",
            output={
                "issues": issues,
                "fixes_applied": fixes_applied,
                "next_step": "Run full_google_setup to complete",
            },
            retryable=True,
        )


# ============================================================================
# Tool Registration
# ============================================================================

GOOGLE_CLOUD_SETUP_SPECS = [
    {
        "name": "full_google_setup",
        "args_model": FullGoogleSetupArgs,
        "fn": full_google_setup,
        "description": "Complete Google Cloud setup using Desktop Commander (opens real Chrome, creates project, enables APIs, creates OAuth credentials)",
    },
    {
        "name": "check_and_fix_google_setup",
        "args_model": CheckAndFixArgs,
        "fn": check_and_fix_google_setup,
        "description": "Diagnose and fix Google API setup issues",
    },
]


def register_google_cloud_setup_tools(registry) -> None:
    """Register Google Cloud setup tools."""
    from agent.autonomous.tools.registry import ToolSpec

    for spec in GOOGLE_CLOUD_SETUP_SPECS:
        registry.register(ToolSpec(
            name=spec["name"],
            args_model=spec["args_model"],
            fn=spec["fn"],
            description=spec["description"],
        ))


__all__ = [
    "FullGoogleSetupArgs",
    "CheckAndFixArgs",
    "full_google_setup",
    "check_and_fix_google_setup",
    "register_google_cloud_setup_tools",
    "GOOGLE_CLOUD_SETUP_SPECS",
]
