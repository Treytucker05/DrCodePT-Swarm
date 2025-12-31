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


def _import_pyautogui():
    """Import PyAutoGUI for desktop control."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        return pyautogui, None
    except ImportError as e:
        return None, f"PyAutoGUI not installed: {e}"


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
                f\"\"\"SELECT d.{path_col}, u.url
                    FROM downloads d
                    LEFT JOIN downloads_url_chains u ON d.id = u.id
                    ORDER BY d.start_time DESC LIMIT 50\"\"\"
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


def _navigate_chrome(url: str) -> bool:
    """Navigate existing Chrome window to a URL without opening new windows."""
    if not _focus_chrome_enabled():
        return _open_chrome(url)
    if not _ensure_chrome_visible(["chrome", "google", "cloud", "console"]):
        return _open_chrome(url)
    try:
        _hotkey("ctrl", "l")
        time.sleep(0.2)
        _type_text(url)
        _press_key("enter")
        time.sleep(1)
        return True
    except Exception:
        return _open_chrome(url)


def _click_at(x: int, y: int, clicks: int = 1) -> bool:
    """Click at specific coordinates."""
    pyautogui, err = _import_pyautogui()
    if not pyautogui:
        return False
    try:
        pyautogui.click(x, y, clicks=clicks)
        return True
    except Exception:
        return False


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


def _auto_click_text(targets: List[str], *, attempts: int = 2, delay: float = 1.0) -> bool:
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
                pyautogui.click(x + max(1, w // 2), y + max(1, h // 2))
                time.sleep(delay)
                return True
        time.sleep(delay)
    return False


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

    _wait_for_continue(
        "Complete any remaining login steps (including 2FA). Type 'continue' when done.",
        seconds=twofa_wait,
    )

    return _wait_for_any(logged_in_tokens, timeout_seconds=90, interval=2.0)


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

    # Step 3: Navigate to project creation
    print("\n[STEP 2] Navigating to project creation...")
    _navigate_chrome("https://console.cloud.google.com/projectcreate")
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

    # Step 4: Create project (auto-first; manual only if allowed)
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

    # Step 5: Enable Calendar API
    print("\n[STEP 3] Enabling Calendar API...")
    _navigate_chrome(f"https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={args.project_name}")
    time.sleep(2)
    _focus_chrome(["calendar", "google", "cloud"])

    if _autoclick_enabled():
        # Wait for page to load key tokens
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

    # Step 6: Enable Tasks API
    print("\n[STEP 4] Enabling Tasks API...")
    _navigate_chrome(f"https://console.cloud.google.com/apis/library/tasks.googleapis.com?project={args.project_name}")
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
    _take_screenshot("step6_tasks_enabled")

    # Step 7: Configure OAuth consent screen (auto)
    print("\n[STEP 5] Configuring OAuth consent screen...")
    _navigate_chrome(f"https://console.cloud.google.com/apis/credentials/consent?project={args.project_name}")
    time.sleep(3)
    _focus_chrome(["consent", "oauth", "google", "cloud"])

    if _autoclick_enabled():
        # If already configured, skip
        if not _screen_has_any(["publishing status", "oauth consent screen", "edit app"]):
            _auto_click_text(["external"])
            _auto_click_text(["create"])
            time.sleep(2)
        email = (creds or {}).get("username") or ""
        _fill_field_by_label(["app", "name"], "Treys Agent")
        if email:
            _fill_field_by_label(["support", "email"], email)
            _fill_field_by_label(["developer", "contact"], email)
        # Save and continue through steps
        for _ in range(3):
            _auto_click_text(["save and continue", "save & continue"])
            time.sleep(2)
        # Test users page
        if email and _screen_has_any(["test users", "add users"]):
            _fill_field_by_label(["add users", "test users"], email)
            _press_key("enter")
            _auto_click_text(["save and continue", "save & continue"])
            time.sleep(2)
        _auto_click_text(["back to dashboard"])
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

    # Step 8: Create OAuth credentials (auto)
    print("\n[STEP 6] Creating OAuth credentials...")
    _navigate_chrome(f"https://console.cloud.google.com/apis/credentials?project={args.project_name}")
    time.sleep(3)
    _focus_chrome(["credentials", "oauth", "google", "cloud"])

    if _autoclick_enabled():
        _auto_click_text(["create credentials"])
        time.sleep(1)
        _auto_click_text(["oauth client id"])
        time.sleep(2)
        _auto_click_text(["application type"])
        time.sleep(1)
        _auto_click_text(["desktop app"])
        _fill_field_by_label(["name"], "Treys Agent Desktop")
        _auto_click_text(["create"])
        time.sleep(2)
        _auto_click_text(["download json", "download"])
        time.sleep(1)
        _auto_click_text(["ok", "done"])
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
