from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional

from agent.autonomous.isolation import DEFAULT_SKIP_DIRS


@dataclass(frozen=True)
class PreflightResult:
    run_dir: Path
    root_listing_path: Path
    repo_index_path: Path
    repo_map_path: Path
    root_listing: List[dict]
    repo_map: List[dict]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _list_root(repo_root: Path) -> List[dict]:
    items = []
    try:
        for entry in repo_root.iterdir():
            try:
                items.append(
                    {
                        "name": entry.name,
                        "type": "dir" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else None,
                    }
                )
            except Exception:
                continue
    except Exception:
        return []
    return items


def _iter_files(repo_root: Path, *, skip_dirs: Iterable[str]) -> Iterable[Path]:
    skip = set(skip_dirs)
    for root, dirs, files in os_walk(repo_root):
        rel = Path(root).relative_to(repo_root)
        if any(part in skip for part in rel.parts):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            path = Path(root) / name
            if any(part in skip for part in path.relative_to(repo_root).parts):
                continue
            yield path


def _score_path(path: Path, objective: str) -> int:
    name = path.name.lower()
    score = 0
    if name in {"readme.md", "readme.txt", "readme.rst"}:
        score += 100
    if name.startswith("architecture"):
        score += 90
    if name.endswith(".py"):
        score += 40
    if name.endswith((".md", ".rst", ".txt")):
        score += 30
    if name.endswith((".json", ".yaml", ".yml", ".toml")):
        score += 20
    lower_obj = (objective or "").lower()
    if any(k in lower_obj for k in ("filepath", "file path", "launcher", "entrypoint")):
        if "launchers" in path.parts:
            score += 120
        if name.endswith((".bat", ".ps1", ".cmd")):
            score += 110
        if any(k in name for k in ("launch", "entry", "main")):
            score += 60
    if "config" in lower_obj or "settings" in lower_obj:
        if "config" in name or "config" in path.parts:
            score += 40
    return score


def _first_non_empty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""


def run_preflight(
    *,
    repo_root: Path,
    objective: str,
    run_dir: Path,
    max_results: int,
    max_map_files: int,
    max_total_bytes: int,
) -> PreflightResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    root_listing = _list_root(repo_root)
    root_listing_path = run_dir / "root_listing.json"
    _write_json(root_listing_path, {"root": str(repo_root), "entries": root_listing})

    repo_files: List[dict] = []
    for path in _iter_files(repo_root, skip_dirs=DEFAULT_SKIP_DIRS):
        try:
            stat = path.stat()
        except Exception:
            continue
        repo_files.append({"path": str(path), "size": int(stat.st_size), "mtime": float(stat.st_mtime)})
        if len(repo_files) >= max_results:
            break
    repo_index_path = run_dir / "repo_index.json"
    _write_json(repo_index_path, {"root": str(repo_root), "count": len(repo_files), "files": repo_files})

    scored = []
    for entry in repo_files:
        p = Path(entry["path"])
        score = _score_path(p, objective)
        scored.append({**entry, "score": score})
    scored.sort(key=lambda r: (r["score"], -r["size"]), reverse=True)

    mapped: List[dict] = []
    remaining = max_total_bytes
    for entry in scored:
        if len(mapped) >= max_map_files:
            break
        if remaining <= 0:
            break
        p = Path(entry["path"])
        if not p.is_file():
            continue
        try:
            snippet_bytes = min(4096, remaining, entry["size"])
            text = p.read_text(encoding="utf-8", errors="replace")[:snippet_bytes]
        except Exception:
            text = ""
            snippet_bytes = 0
        entry["description"] = _first_non_empty_line(text)
        mapped.append(entry)
        remaining -= snippet_bytes

    repo_map_path = run_dir / "repo_map.json"
    _write_json(
        repo_map_path,
        {
            "objective": objective,
            "count": len(mapped),
            "files": mapped,
        },
    )
    return PreflightResult(
        run_dir=run_dir,
        root_listing_path=root_listing_path,
        repo_index_path=repo_index_path,
        repo_map_path=repo_map_path,
        root_listing=root_listing,
        repo_map=mapped,
    )


def os_walk(path: Path):
    import os

    return os.walk(path)
