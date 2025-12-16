from __future__ import annotations

"""
Doctor: environment self-check for DrCodePT-Swarm.
Run: python -m agent.doctor
"""

import shutil
import sys
from pathlib import Path


def check(name, fn):
    try:
        ok, msg = fn()
    except Exception as exc:  # pragma: no cover
        ok, msg = False, str(exc)
    return name, ok, msg


def main():
    root = Path(__file__).resolve().parent

    checks = []

    # Tools registry import
    def _registry():
        import agent.tools.registry as reg  # noqa: F401
        return True, "import ok"

    checks.append(check("tools.registry import", _registry))

    # Playwright
    def _playwright():
        from playwright.sync_api import sync_playwright  # noqa: F401
        exe = None
        base = Path.home() / "AppData" / "Local" / "ms-playwright"
        if base.is_dir():
            hits = list(base.rglob("chrome.exe"))
            if hits:
                exe = str(hits[0])
        with sync_playwright() as p:
            launch_kwargs = {"headless": True}
            if exe:
                launch_kwargs["executable_path"] = exe
            browser = p.chromium.launch(**launch_kwargs)
            page = browser.new_page()
            page.goto("https://example.com", wait_until="load", timeout=10000)
            browser.close()
        return True, "chromium launch ok"

    checks.append(check("playwright chromium", _playwright))

    # PyAutoGUI
    def _pyautogui():
        import pyautogui  # noqa: F401
        return True, "pyautogui import ok"

    checks.append(check("pyautogui", _pyautogui))

    # ffmpeg
    def _ffmpeg():
        return (shutil.which("ffmpeg") is not None, shutil.which("ffmpeg") or "not found")

    checks.append(check("ffmpeg in PATH", _ffmpeg))

    # folders
    def _folders():
        needed = ["runs", "handoff", "sessions", "failures"]
        for d in needed:
            (root / d).mkdir(parents=True, exist_ok=True)
        return True, "created/verified"

    checks.append(check("required folders", _folders))

    # Print table
    print("\nDoctor Results\n==============")
    for name, ok, msg in checks:
        status = "PASS" if ok else "FAIL"
        line = f"{status:5} {name:25} {msg}"
        try:
            sys.stdout.write(line + "\n")
        except Exception:
            sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
