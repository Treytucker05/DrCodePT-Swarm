from __future__ import annotations

from pathlib import Path
from typing import List


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_agents_md() -> str:
    path = _repo_root() / "AGENTS.md"
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _tool_categories() -> List[str]:
    return [
        "Filesystem (read/write/search files and folders)",
        "Web (search/fetch pages)",
        "Browser (Playwright/desktop automation when enabled)",
        "Code (run Python or shell commands)",
        "Memory (store and recall facts/notes)",
    ]


def build_capabilities_response() -> str:
    _ = _load_agents_md()  # intentionally load for context; response is concise
    lines: List[str] = []
    lines.append("Absolutely—here’s what I can help with.")
    lines.append("")
    lines.append("What I can help with:")
    for item in [
        "Plan and execute multi-step tasks on your machine (files, scripts, automation).",
        "Research and summarize information with sources when you ask.",
        "Organize and clean email workflows (especially Yahoo Mail).",
        "Think through problems and propose a plan without running anything.",
    ]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("How to ask me (examples):")
    for example in [
        "“Clean up my Downloads folder and archive old files.”",
        "“Research the best options for X and summarize.”",
        "“Help me consolidate my Yahoo folders.”",
        "“Think through a migration plan without running tools.”",
    ]:
        lines.append(f"- {example}")
    lines.append("")
    lines.append("When to use Team vs Think vs Mail:")
    lines.append("- Team: end-to-end execution with checkpoints and verification.")
    lines.append("- Think: planning/refinement only—no tool execution.")
    lines.append("- Mail: email organization and rules/workflows.")
    lines.append("")
    lines.append("One example task per mode:")
    lines.append("- Team: “Team: audit this repo and fix failing tests.”")
    lines.append("- Think: “Think: design a rollout plan for a new feature.”")
    lines.append("- Mail: “Mail: consolidate my Yahoo folders into 5 buckets.”")
    lines.append("- Research: “Research: compare top options for X.”")
    lines.append("")
    lines.append("Tool categories I can use (when you approve execution):")
    for cat in _tool_categories():
        lines.append(f"- {cat}")
    return "\n".join(lines)
