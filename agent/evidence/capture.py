from __future__ import annotations

"""Evidence capture helpers."""

import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

Timestamp = lambda: datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _tmp_path(suffix: str) -> Path:
    return Path(tempfile.gettempdir()) / f"evidence_{Timestamp()}{suffix}"


def capture_screenshot(browser) -> Path:
    path = _tmp_path(".png")
    try:
        browser.screenshot(path=str(path))
        return path
    except Exception:
        return None


def capture_html(browser) -> Path:
    path = _tmp_path(".html")
    try:
        html = browser.content()
        path.write_text(html, encoding="utf-8")
        return path
    except Exception:
        return None


def capture_console_logs(browser) -> Path:
    path = _tmp_path(".log")
    try:
        # If browser (page) exposes console messages via attribute
        logs = getattr(browser, "console_messages", [])
        if not logs and hasattr(browser, "context"):
            logs = []
        text = "\n".join(map(str, logs))
        path.write_text(text, encoding="utf-8")
        return path
    except Exception:
        return None


def capture_url(browser) -> str:
    try:
        return getattr(browser, "url", None) or ""
    except Exception:
        return ""


def capture_dom_hints(browser) -> Dict[str, Any]:
    hints = {"clickable_elements": [], "form_fields": [], "accessibility_snapshot": ""}
    try:
        # Basic clickable/form detection using query selectors if available
        if hasattr(browser, "query_selector_all"):
            clickables = browser.query_selector_all("a, button, [role=button], [onclick]")
            hints["clickable_elements"] = [c.get_attribute("id") or c.get_attribute("class") or c.inner_text() for c in clickables if c]
            forms = browser.query_selector_all("input, textarea, select")
            hints["form_fields"] = [f.get_attribute("name") or f.get_attribute("id") or f.get_attribute("type") for f in forms if f]
        if hasattr(browser, "accessibility"):
            try:
                snapshot = browser.accessibility.snapshot()
                hints["accessibility_snapshot"] = json.dumps(snapshot)[:2000]
            except Exception:
                pass
    except Exception:
        return hints
    return hints


def capture_network_har(browser) -> Path:
    # Placeholder: would require routing; not always available.
    return None


def capture_playwright_trace(browser) -> Path:
    return None


def capture_file_state(path: str, run_path: Path = None) -> Path:
    src = Path(path)
    if not src.exists():
        return None
    dest_dir = Path(run_path) / "before" if run_path else src.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{src.name}.bak"
    shutil.copy2(src, dest)
    return dest


def bundle_evidence(run_path: Path, captures: Dict[str, Any]) -> Path:
    evidence_dir = Path(run_path) / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (captures or {}).items():
        if value is None:
            continue
        dest = evidence_dir / f"{name}"
        if isinstance(value, Path):
            dest = evidence_dir / Path(value).name
            try:
                shutil.copy2(value, dest)
            except Exception:
                pass
        elif isinstance(value, dict):
            dest = dest.with_suffix(".json")
            dest.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            dest = dest.with_suffix(".txt")
            dest.write_text(str(value), encoding="utf-8")
    return evidence_dir


async def capture_screenshot_async(browser_or_page) -> Path:
    """Async screenshot capture for Browser-Use compatibility."""
    path = _tmp_path(".png")
    try:
        # Try Browser-Use style (has get_current_page method)
        if hasattr(browser_or_page, 'get_current_page'):
            page = await browser_or_page.get_current_page()
            if page:
                await page.screenshot(path=str(path))
                return path
        # Try Playwright page style
        elif hasattr(browser_or_page, 'screenshot'):
            await browser_or_page.screenshot(path=str(path))
            return path
    except Exception as e:
        print(f"Screenshot capture failed: {e}")
    return None


async def capture_html_async(browser_or_page) -> Path:
    """Async HTML capture for Browser-Use compatibility."""
    path = _tmp_path(".html")
    try:
        if hasattr(browser_or_page, 'get_current_page'):
            page = await browser_or_page.get_current_page()
            if page:
                html = await page.content()
                path.write_text(html, encoding="utf-8")
                return path
        elif hasattr(browser_or_page, 'content'):
            html = await browser_or_page.content()
            path.write_text(html, encoding="utf-8")
            return path
    except Exception as e:
        print(f"HTML capture failed: {e}")
    return None


async def capture_dom_hints_async(browser_or_page) -> Dict[str, Any]:
    """Async DOM hints capture for Browser-Use compatibility."""
    hints = {"clickable_elements": [], "form_fields": [], "accessibility_snapshot": ""}
    try:
        page = None
        if hasattr(browser_or_page, 'get_current_page'):
            page = await browser_or_page.get_current_page()
        elif hasattr(browser_or_page, 'query_selector_all'):
            page = browser_or_page
        
        if page:
            # Get clickable elements
            clickables = await page.query_selector_all("a, button, [role=button], [onclick]")
            for c in clickables[:50]:
                try:
                    text = await c.inner_text()
                    hints["clickable_elements"].append(text[:50] if text else "")
                except:
                    pass
            
            # Get form fields
            forms = await page.query_selector_all("input, textarea, select")
            for f in forms[:30]:
                try:
                    name = await f.get_attribute("name") or await f.get_attribute("id") or ""
                    hints["form_fields"].append(name)
                except:
                    pass
    except Exception as e:
        print(f"DOM hints capture failed: {e}")
    return hints


__all__ = [
    "capture_screenshot",
    "capture_screenshot_async",
    "capture_html",
    "capture_html_async",
    "capture_console_logs",
    "capture_url",
    "capture_dom_hints",
    "capture_dom_hints_async",
    "capture_network_har",
    "capture_playwright_trace",
    "capture_file_state",
    "bundle_evidence",
]
