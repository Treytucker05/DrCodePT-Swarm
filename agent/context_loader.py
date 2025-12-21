"""
Context Loader for Trey's Agent.
Scans and summarizes all available resources at startup.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

BASE_DIR = Path(__file__).resolve().parent


def get_saved_credentials() -> List[str]:
    """Return list of sites with saved credentials."""
    sites: List[str] = []

    for filename in ["credential_store.json", "credentials.json"]:
        cred_file = BASE_DIR / "memory" / filename
        if cred_file.exists():
            try:
                data = json.loads(cred_file.read_text())
                if isinstance(data, dict):
                    if "entries" in data:
                        for entry in data["entries"].values():
                            site = entry.get("site")
                            if site and site not in sites:
                                sites.append(site)
                    else:
                        for k in data.keys():
                            if k not in sites:
                                sites.append(k)
            except Exception:
                pass

    playbooks_dir = BASE_DIR / "memory" / "site_playbooks"
    if playbooks_dir.exists():
        for f in playbooks_dir.glob("*.yaml"):
            site = f.stem
            if site not in sites:
                sites.append(site)

    storage_dir = BASE_DIR / "browser_state"
    if storage_dir.exists():
        for f in storage_dir.glob("*_state.json"):
            site = f.stem.replace("_state", "")
            if site not in sites:
                sites.append(site)

    return sorted(sites)


def get_available_playbooks() -> List[Dict[str, Any]]:
    """Return list of available playbooks with metadata."""
    index_file = BASE_DIR / "learning" / "playbooks" / "index.json"
    playbooks: List[Dict[str, Any]] = []

    if index_file.exists():
        try:
            data = json.loads(index_file.read_text())
            if isinstance(data, dict):
                for pb_id, pb_info in data.items():
                    playbooks.append(
                        {
                            "id": pb_id,
                            "name": pb_info.get("name", pb_id),
                            "tags": pb_info.get("tags", []),
                            "success_count": pb_info.get("success_count", 0),
                            "goal_pattern": pb_info.get("goal_pattern", ""),
                        }
                    )
        except Exception:
            pass

    return playbooks


def get_available_tools() -> List[str]:
    """Return list of registered tools."""
    tools = [
        "shell",
        "browser",
        "python",
        "filesystem",
        "api",
        "desktop",
        "screen_recorder",
        "vision",
        "notify",
        "code_review",
        "research",
        "mcp",
    ]
    return tools


def get_recent_tasks(limit: int = 5) -> List[Dict[str, Any]]:
    """Return recent task executions."""
    tasks_dir = BASE_DIR / "tasks"
    recent: List[Dict[str, Any]] = []

    if tasks_dir.exists():
        executed = sorted(tasks_dir.glob("executed_plan_*.yaml"), reverse=True)[:limit]
        for f in executed:
            try:
                import yaml

                data = yaml.safe_load(f.read_text())
                recent.append(
                    {
                        "name": data.get("name", f.stem),
                        "goal": data.get("goal", ""),
                        "type": data.get("type", ""),
                        "timestamp": f.stem.split("_")[-1] if "_" in f.stem else "",
                        "file": f.name,
                    }
                )
            except Exception:
                pass

    return recent[:limit]


def get_session_info() -> Dict[str, Any]:
    """Return current session information."""
    sessions_dir = BASE_DIR / "sessions"
    info = {"active": False, "last_used": None, "task_count": 0}

    if sessions_dir.exists():
        sessions = sorted(sessions_dir.glob("*/session.json"), reverse=True)
        if sessions:
            try:
                data = json.loads(sessions[0].read_text())
                info["active"] = True
                info["last_used"] = data.get("updated_at", data.get("created_at"))
                info["task_count"] = len(data.get("history", []))
            except Exception:
                pass

    return info


def build_context_summary() -> Dict[str, Any]:
    """Build complete context summary."""
    return {
        "credentials": get_saved_credentials(),
        "playbooks": get_available_playbooks(),
        "tools": get_available_tools(),
        "recent_tasks": get_recent_tasks(),
        "session": get_session_info(),
        "generated_at": datetime.now().isoformat(),
    }


def format_context_for_display() -> str:
    """Format context for terminal display."""
    ctx = build_context_summary()
    lines = []

    creds = ctx["credentials"]
    if creds:
        lines.append(f"  Credentials: {', '.join(creds)}")
    else:
        lines.append("  Credentials: None saved")

    playbooks = ctx["playbooks"]
    if playbooks:
        pb_names = [p["name"] for p in playbooks[:5]]
        lines.append(f"  Playbooks: {len(playbooks)} available ({', '.join(pb_names)})")
    else:
        lines.append("  Playbooks: None yet (will learn from tasks)")

    tools = ctx["tools"]
    lines.append(f"  Tools: {len(tools)} available")

    session = ctx["session"]
    if session["active"]:
        lines.append(f"  Session: Active ({session['task_count']} tasks)")
    else:
        lines.append("  Session: New session")

    return "\n".join(lines)


def format_context_for_llm() -> str:
    """Format context as system prompt for the configured LLM."""
    ctx = build_context_summary()

    parts = ["AGENT CONTEXT (automatically loaded):"]

    creds = ctx["credentials"]
    if creds:
        parts.append("\nSAVED CREDENTIALS (can auto-login):")
        for site in creds:
            parts.append(f"  - {site}")
        parts.append("When user mentions these sites, use 'login_site' field in browser tasks.")

    playbooks = ctx["playbooks"]
    if playbooks:
        parts.append("\nAVAILABLE PLAYBOOKS (reusable patterns):")
        for pb in playbooks[:10]:
            tags = ", ".join(pb["tags"]) if pb["tags"] else "general"
            parts.append(f"  - {pb['name']} (tags: {tags}, used {pb['success_count']}x)")
        parts.append("Suggest using existing playbooks when the goal matches.")

    tools = ctx["tools"]
    parts.append("\nAVAILABLE TOOLS:")
    tool_descriptions = {
        "shell": "PowerShell commands",
        "browser": "Web automation (Playwright)",
        "python": "Python script execution",
        "filesystem": "File read/write/move",
        "api": "HTTP requests",
        "desktop": "Mouse/keyboard automation",
        "screen_recorder": "Screen recording",
        "vision": "Screenshot capture",
        "notify": "Windows notifications",
        "code_review": "LLM-assisted code review",
        "research": "Multi-source web research",
    }
    for tool in tools:
        desc = tool_descriptions.get(tool, "")
        parts.append(f"  - {tool}: {desc}")

    recent = ctx["recent_tasks"]
    if recent:
        parts.append("\nRECENT TASKS (for context):")
        for task in recent[:3]:
            parts.append(f"  - {task['name']}: {task['goal'][:50]}...")

    parts.append("\nUse this context to make informed suggestions and leverage existing resources.")

    return "\n".join(parts)


if __name__ == "__main__":
    print("=== Context Summary ===")
    print(format_context_for_display())
    print("\n=== LLM Context ===")
    print(format_context_for_llm())
