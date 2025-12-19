from __future__ import annotations

"""Learn mode - record user actions as playbooks."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    from colorama import Fore, Style

    GREEN, RED, CYAN, YELLOW, RESET = (
        Fore.GREEN,
        Fore.RED,
        Fore.CYAN,
        Fore.YELLOW,
        Style.RESET_ALL,
    )
except Exception:
    GREEN = RED = CYAN = YELLOW = RESET = ""

BASE_DIR = Path(__file__).resolve().parents[1]  # .../agent


def _slugify(text: str) -> str:
    import re

    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "playbook"


def _best_selector(node: Dict[str, Any]) -> str:
    # Prefer stable "test" selectors when present.
    for key in ("data-test-id", "data-testid", "data-test", "data-qa"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return f"[{key}='{value.strip()}']"

    el_id = node.get("id")
    if isinstance(el_id, str) and el_id.strip():
        return f"#{el_id.strip()}"

    name = node.get("name")
    if isinstance(name, str) and name.strip():
        return f"[name='{name.strip()}']"

    aria = node.get("aria-label")
    if isinstance(aria, str) and aria.strip():
        return f"[aria-label='{aria.strip()}']"

    tag = node.get("tag") or "div"
    klass = node.get("class")
    if isinstance(klass, str) and klass.strip():
        first = klass.split()[0]
        if first:
            return f"{tag}.{first}"

    return str(tag)


async def _record_browser_actions(start_url: str) -> List[Dict[str, Any]]:
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Playwright not installed: {exc}") from exc

    tracking_script = r"""
(() => {
  window.__treyRecorded = window.__treyRecorded || [];
  function pick(el) {
    if (!el) return {};
    const out = {
      tag: (el.tagName || '').toLowerCase(),
      id: el.id || '',
      name: el.getAttribute ? (el.getAttribute('name') || '') : '',
      class: el.className && typeof el.className === 'string' ? el.className : '',
      'aria-label': el.getAttribute ? (el.getAttribute('aria-label') || '') : '',
      'data-test-id': el.getAttribute ? (el.getAttribute('data-test-id') || '') : '',
      'data-testid': el.getAttribute ? (el.getAttribute('data-testid') || '') : '',
      'data-test': el.getAttribute ? (el.getAttribute('data-test') || '') : '',
      'data-qa': el.getAttribute ? (el.getAttribute('data-qa') || '') : '',
      text: (el.innerText || '').slice(0, 80)
    };
    return out;
  }

  document.addEventListener('click', (e) => {
    const el = e.target && e.target.closest ? e.target.closest('a,button,input,select,textarea,[role],[data-test-id],[data-testid]') || e.target : e.target;
    window.__treyRecorded.push({ type: 'click', node: pick(el), ts: new Date().toISOString() });
  }, true);

  document.addEventListener('input', (e) => {
    const el = e.target;
    if (!el) return;
    window.__treyRecorded.push({ type: 'input', inputType: (el.type || 'text'), node: pick(el), ts: new Date().toISOString() });
  }, true);
})();
"""

    actions: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=75)
        context = await browser.new_context()
        page = await context.new_page()
        await page.add_init_script(tracking_script)

        if start_url:
            await page.goto(start_url, wait_until="domcontentloaded", timeout=30000)

        print(f"{YELLOW}[RECORDING]{RESET} Perform the task. Close the browser window when done.\\n")

        while True:
            try:
                if not context.pages:
                    break
            except Exception:
                break

            try:
                batch = await page.evaluate("window.__treyRecorded || []")
                if batch:
                    actions.extend(batch)
                    await page.evaluate("window.__treyRecorded = []")
            except Exception:
                pass

            await asyncio.sleep(0.35)

        try:
            await browser.close()
        except Exception:
            pass

    return actions


def _actions_to_steps(start_url: str, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    if start_url:
        steps.append(
            {
                "type": "browser",
                "description": "Open start page",
                "action": "goto",
                "url": start_url,
            }
        )

    # Naive conversion: clicks + non-password inputs (as env placeholders)
    input_counter = 0
    for act in actions:
        kind = act.get("type")
        node = act.get("node") or {}
        selector = _best_selector(node)
        text = (node.get("text") or "").strip()

        if kind == "click":
            step: Dict[str, Any] = {"type": "browser", "description": "Click", "action": "click"}
            if selector:
                step["selector"] = selector
            elif text:
                step["text"] = text
            else:
                continue
            steps.append(step)
            continue

        if kind == "input":
            input_type = str(act.get("inputType") or "").lower()
            if input_type in {"password"}:
                continue
            # Avoid capturing secrets; use env placeholders for values.
            input_counter += 1
            env_name = f"TREY_INPUT_{input_counter}"
            steps.append(
                {
                    "type": "browser",
                    "description": f"Fill ({env_name})",
                    "action": "fill",
                    "selector": selector,
                    "value": f"${{{env_name}}}",
                }
            )
            continue

    # Drop obvious duplicates
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for step in steps:
        key = (
            step.get("type"),
            step.get("action"),
            step.get("selector"),
            step.get("text"),
            step.get("url"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(step)
    return deduped


def mode_learn(task_name: str) -> None:
    from agent.modes.execute import load_playbooks, save_playbooks

    print(f"\\n{CYAN}[LEARN MODE]{RESET} Recording: {task_name}")
    print("Tip: If login is required, log in first (or set up stored credentials).\\n")

    start_url = input(f"{CYAN}Start URL (optional):{RESET} ").strip()
    login_site = input(f"{CYAN}Login site key (optional, e.g. yahoo):{RESET} ").strip().lower()

    try:
        actions = asyncio.run(_record_browser_actions(start_url))
    except Exception as exc:
        print(f"{YELLOW}[INFO]{RESET} Browser recording unavailable: {exc}")
        print("Fallback: describe each step (blank line when done).")
        manual: List[Dict[str, Any]] = []
        while True:
            s = input(f"  Step {len(manual) + 1}: ").strip()
            if not s:
                break
            manual.append({"type": "manual", "description": s})

        if not manual:
            print(f"{YELLOW}[INFO]{RESET} No steps recorded.")
            return

        playbook_steps = manual
    else:
        playbook_steps = _actions_to_steps(start_url, actions)

    playbooks = load_playbooks()

    pb_id = _slugify(task_name)
    if pb_id in playbooks:
        pb_id = f"{pb_id}-{datetime.now().strftime('%H%M%S')}"

    playbook: Dict[str, Any] = {
        "name": task_name,
        "description": f"Playbook for: {task_name}",
        "triggers": [task_name.lower().strip(), pb_id],
        "steps": playbook_steps,
        "created": datetime.now().isoformat(),
        "type": "learned",
    }
    if login_site:
        playbook["login_site"] = login_site

    save_playbooks({**playbooks, pb_id: playbook})

    print(f"\\n{GREEN}[SAVED]{RESET} Playbook created: {task_name}")
    if any(s.get("action") == "fill" and "value" in s for s in playbook_steps):
        print(f"{YELLOW}[NOTE]{RESET} This playbook uses env vars like TREY_INPUT_1 for fill steps.")
    print(f"Next time, just say: '{task_name}'")

