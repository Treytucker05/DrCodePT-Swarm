from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Set

DEFAULT_SKIP_DIRS: Set[str] = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "runs",
    ".pytest_cache",
}


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    branch: str


def copy_repo_to_workspace(repo_root: Path, dest: Path, *, skip_dirs: Iterable[str] = DEFAULT_SKIP_DIRS) -> None:
    skip = set(skip_dirs)
    repo_root = repo_root.resolve()
    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os_walk(repo_root):
        rel = Path(root).relative_to(repo_root)
        if any(part in skip for part in rel.parts):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            src = Path(root) / name
            rel_path = src.relative_to(repo_root)
            if any(part in skip for part in rel_path.parts):
                continue
            target = dest / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)


def create_worktree(repo_root: Path, dest: Path, branch: str) -> WorktreeInfo:
    repo_root = repo_root.resolve()
    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "-C", str(repo_root), "worktree", "add", "-b", branch, str(dest), "HEAD"]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return WorktreeInfo(path=dest, branch=branch)


def remove_worktree(repo_root: Path, info: WorktreeInfo) -> None:
    repo_root = repo_root.resolve()
    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "worktree", "remove", "--force", str(info.path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        pass
    try:
        subprocess.run(
            ["git", "-C", str(repo_root), "branch", "-D", info.branch],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        pass


def os_walk(path: Path):
    # Wrapper for testability and to keep os import local.
    import os

    return os.walk(path)


def sanitize_branch_name(text: str) -> str:
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch in {"-", "_", "/"}:
            cleaned.append(ch)
        else:
            cleaned.append("-")
    out = "".join(cleaned).strip("-")
    return out or "swarm"
