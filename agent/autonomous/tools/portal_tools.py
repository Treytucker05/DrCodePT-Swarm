from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from agent.autonomous.models import ToolResult
from agent.learning.learning_store import load_playbook
from agent.tools.browser import BrowserTool

logger = logging.getLogger(__name__)

_AGENT_DIR = Path(__file__).resolve().parents[2]
_SESSION_DIR = _AGENT_DIR / "memory" / "sessions"
_BLACKBOARD_SESSION = _SESSION_DIR / "blackboard.json"
_COACHRX_SESSION = _SESSION_DIR / "coachrx.json"


class BlackboardSnapshotArgs(BaseModel):
    target: Optional[str] = Field(
        default=None,
        description="Optional section to open: courses, assignments, calendar, course_content",
    )
    extract_selector: str = Field(
        default="body",
        description="CSS selector to extract text from after navigation",
    )
    wait_selector: Optional[str] = Field(
        default=None,
        description="CSS selector to wait for before extraction (defaults to body)",
    )
    take_screenshot: bool = Field(
        default=False, description="Capture a screenshot after navigation"
    )
    headless: Optional[bool] = Field(
        default=None,
        description="Override headless mode; defaults to headful on first login",
    )
    use_saved_session: bool = Field(
        default=True,
        description="Reuse saved session state to skip login when possible",
    )
    save_session: bool = Field(
        default=True,
        description="Persist session state for faster subsequent runs",
    )
    start_url: Optional[str] = Field(
        default=None,
        description="Override the start URL (defaults to playbook start_url)",
    )


class CoachRxSnapshotArgs(BaseModel):
    target: Optional[str] = Field(
        default=None,
        description="Optional section to open: clients, workouts, schedule",
    )
    extract_selector: str = Field(
        default="body",
        description="CSS selector to extract text from after navigation",
    )
    wait_selector: Optional[str] = Field(
        default=None,
        description="CSS selector to wait for before extraction (defaults to body)",
    )
    take_screenshot: bool = Field(
        default=False, description="Capture a screenshot after navigation"
    )
    headless: Optional[bool] = Field(
        default=None,
        description="Override headless mode; defaults to headful on first login",
    )
    use_saved_session: bool = Field(
        default=True,
        description="Reuse saved session state to skip login when possible",
    )
    save_session: bool = Field(
        default=True,
        description="Persist session state for faster subsequent runs",
    )
    start_url: Optional[str] = Field(
        default=None,
        description="Override the start URL (defaults to playbook start_url)",
    )


def _build_steps(
    playbook: Dict[str, Any],
    *,
    target: Optional[str],
    extract_selector: Optional[str],
    wait_selector: Optional[str],
    take_screenshot: bool,
) -> list[Dict[str, Any]]:
    steps: list[Dict[str, Any]] = []
    selectors = (playbook or {}).get("working_selectors") or {}

    if target:
        selector = selectors.get(target)
        if selector:
            steps.append({"action": "click_optional", "selector": selector})
        else:
            steps.append({"action": "click_optional", "text": target})
        steps.append({"action": "sleep", "seconds": 1})

    steps.append({"action": "wait_for", "selector": wait_selector or "body"})

    if take_screenshot:
        steps.append({"action": "screenshot"})

    if extract_selector:
        steps.append({"action": "extract", "selector": extract_selector, "kind": "text"})

    return steps


def _resolve_headless(
    requested: Optional[bool], session_path: Optional[Path]
) -> Optional[bool]:
    if requested is not None:
        return requested
    if session_path and not session_path.is_file():
        # First login tends to require user interaction.
        return False
    return None


def _run_portal_snapshot(
    *,
    ctx,
    site: str,
    session_path: Path,
    args: BaseModel,
    fallback_start_url: str,
) -> ToolResult:
    playbook = load_playbook(site) or {}
    start_url = getattr(args, "start_url", None) or playbook.get("start_url") or fallback_start_url
    if not start_url:
        return ToolResult(success=False, error=f"No start_url found for {site}.")

    steps = _build_steps(
        playbook,
        target=getattr(args, "target", None),
        extract_selector=getattr(args, "extract_selector", None),
        wait_selector=getattr(args, "wait_selector", None),
        take_screenshot=bool(getattr(args, "take_screenshot", False)),
    )

    use_saved_session = bool(getattr(args, "use_saved_session", True))
    save_session = bool(getattr(args, "save_session", True))

    browser_session_path: Optional[Path] = None
    if use_saved_session:
        browser_session_path = session_path
    elif save_session:
        logger.warning("save_session ignored when use_saved_session is False")

    headless = _resolve_headless(getattr(args, "headless", None), browser_session_path)

    inputs = {
        "login_site": site,
        "url": start_url,
        "steps": steps,
        "run_path": str(ctx.run_dir),
        "session_state_path": str(browser_session_path) if save_session and browser_session_path else None,
        "headless": headless,
    }

    session_existed = bool(browser_session_path and browser_session_path.is_file())
    if browser_session_path:
        _SESSION_DIR.mkdir(parents=True, exist_ok=True)

    result = BrowserTool().execute(None, inputs)
    output = result.output or {}
    evidence = result.evidence or {}
    metadata = dict(result.metadata or {})
    metadata.update(
        {
            "site": site,
            "session_state_path": str(browser_session_path) if browser_session_path else None,
            "session_loaded": session_existed,
            "session_saved": bool(save_session and browser_session_path),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    return ToolResult(
        success=bool(result.success),
        output={
            "final_url": output.get("final_url"),
            "extracts": output.get("extracts"),
            "downloads": output.get("downloads"),
            "evidence": evidence,
        },
        error=result.error,
        retryable=result.retryable,
        metadata=metadata,
    )


def blackboard_snapshot(ctx, args: BlackboardSnapshotArgs) -> ToolResult:
    return _run_portal_snapshot(
        ctx=ctx,
        site="blackboard",
        session_path=_BLACKBOARD_SESSION,
        args=args,
        fallback_start_url="https://utmb.blackboard.com/",
    )


def coachrx_snapshot(ctx, args: CoachRxSnapshotArgs) -> ToolResult:
    return _run_portal_snapshot(
        ctx=ctx,
        site="coachrx",
        session_path=_COACHRX_SESSION,
        args=args,
        fallback_start_url="https://dashboard.coachrx.app/",
    )


__all__ = [
    "BlackboardSnapshotArgs",
    "CoachRxSnapshotArgs",
    "blackboard_snapshot",
    "coachrx_snapshot",
]
