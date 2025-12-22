from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from agent.config.profile import ProfileConfig, RunUsage


_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "runs",
    ".pytest_cache",
}


@dataclass(frozen=True)
class RepoFile:
    path: str
    size: int
    mtime: float
    score: int = 0
    description: str = ""


def _is_skipped(path: Path) -> bool:
    return any(part in _SKIP_DIRS for part in path.parts)


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _score_path(path: Path) -> int:
    name = path.name.lower()
    if name in {"readme.md", "readme.txt", "readme.rst"}:
        return 100
    if name in {"pyproject.toml", "requirements.txt", "setup.cfg"}:
        return 90
    if name.endswith(".py"):
        return 80
    if name.endswith((".md", ".rst", ".txt")):
        return 60
    if name.endswith((".json", ".yaml", ".yml", ".toml")):
        return 50
    return 10


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""


def build_repo_index(
    repo_root: Path,
    *,
    run_dir: Path,
    max_results: int,
) -> List[RepoFile]:
    results: List[RepoFile] = []
    seen: set[str] = set()
    root_entries = []
    try:
        root_entries = [p.name for p in repo_root.iterdir()]
    except Exception:
        root_entries = []

    patterns = [
        "README*",
        "ARCHITECTURE*",
        "agent/**/*.py",
        "agent/**/README*",
        "configs/**/*",
        "config/**/*",
    ]

    def _add_path(path: Path) -> None:
        if len(results) >= max_results:
            return
        if _is_skipped(path):
            return
        if not path.is_file():
            return
        key = str(path)
        if key in seen:
            return
        try:
            stat = path.stat()
        except Exception:
            return
        results.append(
            RepoFile(
                path=key,
                size=int(stat.st_size),
                mtime=float(stat.st_mtime),
            )
        )
        seen.add(key)

    for pattern in patterns:
        for path in repo_root.glob(pattern):
            _add_path(path)
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    if len(results) < max_results:
        for path in repo_root.rglob("*"):
            if len(results) >= max_results:
                break
            _add_path(path)
    _write_json(
        run_dir / "repo_index.json",
        {
            "root": str(repo_root),
            "root_entries": root_entries,
            "count": len(results),
            "files": [r.__dict__ for r in results],
        },
    )
    return results


def build_repo_map(
    repo_files: Iterable[RepoFile],
    *,
    run_dir: Path,
    profile: ProfileConfig,
    usage: Optional[RunUsage] = None,
) -> List[RepoFile]:
    files = list(repo_files)
    scored: List[RepoFile] = []
    for entry in files:
        p = Path(entry.path)
        scored.append(RepoFile(path=entry.path, size=entry.size, mtime=entry.mtime, score=_score_path(p)))
    scored.sort(key=lambda r: (r.score, -r.size), reverse=True)

    max_files = max(1, profile.max_files_to_read)
    remaining_bytes = profile.max_total_bytes_to_read
    if usage is not None:
        remaining_bytes = usage.remaining_bytes(profile.max_total_bytes_to_read)

    mapped: List[RepoFile] = []
    for entry in scored:
        if len(mapped) >= max_files:
            break
        if remaining_bytes <= 0:
            break
        p = Path(entry.path)
        if not p.is_file():
            continue
        try:
            snippet_bytes = min(4096, remaining_bytes, entry.size)
            text = p.read_text(encoding="utf-8", errors="replace")[:snippet_bytes]
        except Exception:
            text = ""
            snippet_bytes = 0
        desc = _first_non_empty_line(text)
        mapped.append(
            RepoFile(
                path=entry.path,
                size=entry.size,
                mtime=entry.mtime,
                score=entry.score,
                description=desc,
            )
        )
        remaining_bytes -= snippet_bytes
        if usage is not None:
            usage.consume_file(snippet_bytes)

    if profile.name in {"deep", "audit"} and remaining_bytes > 0:
        for entry in scored[len(mapped) :]:
            if len(mapped) >= max_files:
                break
            if remaining_bytes <= 0:
                break
            p = Path(entry.path)
            if not p.is_file():
                continue
            try:
                snippet_bytes = min(2048, remaining_bytes, entry.size)
                text = p.read_text(encoding="utf-8", errors="replace")[:snippet_bytes]
            except Exception:
                text = ""
                snippet_bytes = 0
            desc = _first_non_empty_line(text)
            mapped.append(
                RepoFile(
                    path=entry.path,
                    size=entry.size,
                    mtime=entry.mtime,
                    score=entry.score,
                    description=desc,
                )
            )
            remaining_bytes -= snippet_bytes
            if usage is not None:
                usage.consume_file(snippet_bytes)

    _write_json(
        run_dir / "repo_map.json",
        {
            "profile": profile.name,
            "count": len(mapped),
            "files": [m.__dict__ for m in mapped],
        },
    )
    return mapped


def is_repo_review_task(task: str) -> bool:
    text = (task or "").lower()
    signals = ["repo", "repository", "codebase", "code base", "review", "audit", "scan"]
    return any(s in text for s in signals)
