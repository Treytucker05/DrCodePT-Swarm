from __future__ import annotations

"""
Deterministic Playwright step executor (no LLM, no OpenAI).
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ToolAdapter, ToolResult
from agent.memory.credentials import CredentialError, build_login_steps


def _safe_env(value: str) -> str:
    if not isinstance(value, str):
        return value
    if value.startswith("${") and value.endswith("}"):
        key = value[2:-1]
        return os.getenv(key, "")
    return value


def _mk_evidence(run_path: Optional[str]) -> Path:
    base = Path(run_path) if run_path else Path(Path.cwd())
    evidence_dir = base / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir


def _find_chromium_executable() -> Optional[str]:
    base = Path(os.getenv("USERPROFILE", "")) / "AppData" / "Local" / "ms-playwright"
    if base.is_dir():
        for candidate in base.rglob("chrome.exe"):
            return str(candidate)
    return None


class BrowserTool(ToolAdapter):
    tool_name = "browser"

    async def _run_steps(self, context, page, steps: List[Dict[str, Any]], run_path: Optional[str], session_state_path: Optional[str]) -> ToolResult:
        extracts: Dict[str, Any] = {}
        evidence_dir = _mk_evidence(run_path)

        try:
            for idx, step in enumerate(steps):
                action = step.get("action")
                if not action:
                    return ToolResult(False, error="Step missing action")

                # normalize helpers
                selector = step.get("selector")
                text = step.get("text")
                timeout = step.get("timeout_ms", 15000)

                if action == "goto":
                    url = step.get("url")
                    await page.goto(url, wait_until="load", timeout=timeout)

                elif action == "click":
                    if selector:
                        await page.click(selector, timeout=timeout)
                    elif text:
                        await page.get_by_text(text).click(timeout=timeout)
                    else:
                        return ToolResult(False, error="click requires selector or text")

                elif action == "fill":
                    if not selector:
                        return ToolResult(False, error="fill requires selector")
                    value = _safe_env(step.get("value", ""))
                    await page.fill(selector, str(value), timeout=timeout)

                elif action == "submit":
                    if selector:
                        await page.press(selector, "Enter", timeout=timeout)
                    else:
                        await page.keyboard.press("Enter")

                elif action == "press":
                    key = step.get("key")
                    if not key:
                        return ToolResult(False, error="press requires key")
                    if selector:
                        await page.press(selector, key, timeout=timeout)
                    else:
                        await page.keyboard.press(key)

                elif action == "wait_for":
                    if selector:
                        await page.wait_for_selector(selector, timeout=timeout)
                    elif text:
                        await page.get_by_text(text).wait_for(timeout=timeout)
                    else:
                        await page.wait_for_timeout(timeout)

                elif action == "sleep":
                    sec = float(step.get("seconds", 1))
                    await asyncio.sleep(sec)

                elif action == "screenshot":
                    path = step.get("path")
                    if path:
                        shot_path = Path(path)
                        shot_path.parent.mkdir(parents=True, exist_ok=True)
                    else:
                        shot_path = evidence_dir / f"screenshot_step{idx}.png"
                    await page.screenshot(path=str(shot_path), full_page=True)

                elif action == "save_storage_state":
                    dest = Path(step.get("path") or session_state_path or "sessions/state.json")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    await context.storage_state(path=str(dest))

                elif action == "extract":
                    kind = step.get("kind", "text")
                    sel = step.get("selector")
                    if not sel:
                        return ToolResult(False, error="extract requires selector")
                    handle = await page.query_selector(sel)
                    if not handle:
                        return ToolResult(False, error=f"extract selector not found: {sel}")
                    if kind == "html":
                        extracts[sel] = await handle.inner_html()
                    else:
                        extracts[sel] = await handle.inner_text()

                else:
                    return ToolResult(False, error=f"Unsupported action: {action}")

            # end steps
            # save session if path provided
            if session_state_path:
                dest = Path(session_state_path)
                dest.parent.mkdir(parents=True, exist_ok=True)
                await context.storage_state(path=str(dest))

            final_url = page.url
            return ToolResult(True, output={"final_url": final_url, "extracts": extracts})

        except Exception as exc:
            # collect evidence
            screenshot_path = None
            html_path = None
            try:
                screenshot_path = evidence_dir / f"failure_{int(time.time())}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
            except Exception:
                screenshot_path = None
            try:
                html_path = evidence_dir / f"failure_{int(time.time())}.html"
                html = await page.content()
                html_path.write_text(html, encoding="utf-8")
            except Exception:
                html_path = None

            return ToolResult(
                False,
                error=str(exc),
                evidence={"screenshot": str(screenshot_path) if screenshot_path else None, "html": str(html_path) if html_path else None},
            )

    def execute(self, task, inputs: Dict[str, Any]) -> ToolResult:
        login_site = inputs.get("login_site") or getattr(task, "login_site", None)
        user_steps = inputs.get("steps") or getattr(task, "steps", None) or (getattr(task, "inputs", {}) or {}).get(
            "steps"
        )
        start_url = getattr(task, "url", None) or inputs.get("url")

        login_steps: List[Dict[str, Any]] = []
        if login_site:
            try:
                login_steps = build_login_steps(login_site, start_url=start_url)
            except CredentialError as exc:
                return ToolResult(False, error=str(exc))
            except Exception as exc:  # pragma: no cover - safeguard
                return ToolResult(False, error=f"Failed to build login steps: {exc}")

        if user_steps:
            steps = login_steps + user_steps
        elif login_steps:
            steps = login_steps
        else:
            if not start_url:
                return ToolResult(False, error="No steps or url provided for browser task")
            steps = [{"action": "goto", "url": start_url}]

        run_path = inputs.get("run_path")
        session_state_path = getattr(task, "session_state_path", None)

        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            return ToolResult(False, error=f"Playwright not installed: {exc}")

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async def runner():
            async with async_playwright() as p:
                launch_kwargs = {"headless": True}
                exe = _find_chromium_executable()
                if exe:
                    launch_kwargs["executable_path"] = exe
                browser = await p.chromium.launch(**launch_kwargs)
                context_kwargs = {}
                if session_state_path and Path(session_state_path).is_file():
                    context_kwargs["storage_state"] = str(session_state_path)
                context = await browser.new_context(**context_kwargs)
                page = await context.new_page()
                result = await self._run_steps(context, page, steps, run_path, session_state_path)
                await browser.close()
                return result

        try:
            return loop.run_until_complete(runner())
        except Exception as exc:
            return ToolResult(False, error=str(exc))
