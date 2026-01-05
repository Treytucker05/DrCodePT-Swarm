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


def _iter_files_deterministic(repo_root: Path) -> Iterable[Path]:
    """Yield repo files in a deterministic order without materializing all paths.

    `Path.rglob()` order can vary across OS/filesystems. Repo analysis should be
    stable when `max_results` caps selection.
    """

    import os

    repo_root = repo_root.resolve()
    for root, dirs, files in os.walk(repo_root):
        # Prune + sort directories in-place for deterministic traversal.
        dirs[:] = sorted([d for d in dirs if d not in _SKIP_DIRS])
        root_path = Path(root)
        for name in sorted(files):
            yield root_path / name


@dataclass(frozen=True)
class RepoFile:
    path: str
    size: int
    mtime: float
    score: int = 0
    description: str = ""


@dataclass
class RepoScanner:
    repo_root: Path
    run_dir: Path
    max_results: int
    profile: ProfileConfig
    usage: Optional[RunUsage] = None

    def index(self) -> List[RepoFile]:
        return build_repo_index(self.repo_root, run_dir=self.run_dir, max_results=self.max_results)

    def map(self, repo_files: Optional[Iterable[RepoFile]] = None) -> List[RepoFile]:
        files = repo_files if repo_files is not None else self.index()
        return build_repo_map(files, run_dir=self.run_dir, profile=self.profile, usage=self.usage)

    def scan(self) -> Tuple[List[RepoFile], List[RepoFile]]:
        index = self.index()
        repo_map = build_repo_map(index, run_dir=self.run_dir, profile=self.profile, usage=self.usage)
        return index, repo_map


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
        root_entries = sorted([p.name for p in repo_root.iterdir()])
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
        for path in sorted(repo_root.glob(pattern)):
            _add_path(path)
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    if len(results) < max_results:
        for path in _iter_files_deterministic(repo_root):
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
    # Deterministic ranking: score desc, size asc, path asc.
    scored.sort(key=lambda r: (-r.score, r.size, r.path))

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
    strong_signals = [
        "repo",
        "repository",
        "codebase",
        "code base",
        "code review",
        "pull request",
        "pr",
        "audit",
        "scan",
        "static analysis",
        "lint",
    ]
    if any(s in text for s in strong_signals):
        return True
    if "review" not in text:
        return False
    doc_hints = [
        ".docx",
        ".doc",
        ".pdf",
        ".pptx",
        ".xlsx",
        ".csv",
        ".tsv",
        ".rtf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
    ]
    if any(h in text for h in doc_hints):
        return False
    code_hints = [
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".cs",
        ".cpp",
        ".c",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".sql",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".md",
        ".txt",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "cargo.toml",
        "pom.xml",
        "build.gradle",
    ]
    if any(h in text for h in code_hints):
        return True
    path_hints = [
        "src/",
        "lib/",
        "tests/",
        "test/",
        "app/",
        "server/",
        "client/",
        "backend/",
        "frontend/",
        "agent/",
    ]
    return any(h in text for h in path_hints)
