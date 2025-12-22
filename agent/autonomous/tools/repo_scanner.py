"""Repository scanning utilities."""

import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file."""
    path: str
    size_bytes: int
    file_type: str  # "python", "markdown", "config", "other"
    is_key_file: bool = False
    reason: Optional[str] = None


@dataclass
class RepoIndex:
    """Index of all files in repository."""
    root: str
    total_files: int
    total_bytes: int
    files: List[FileInfo]


@dataclass
class RepoMap:
    """Map of key files in repository."""
    root: str
    key_files: List[FileInfo]
    structure_summary: str


class RepoScanner:
    """Scan repository and produce index and map."""

    FILE_TYPES = {
        "python": {".py"},
        "markdown": {".md", ".rst", ".txt"},
        "config": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"},
        "code": {".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".h"},
    }

    KEY_FILE_PATTERNS = {
        "README.md": "Project overview",
        "setup.py": "Python package setup",
        "pyproject.toml": "Python project config",
        "requirements.txt": "Python dependencies",
        "Makefile": "Build instructions",
        ".github/workflows": "CI/CD configuration",
        "src/main.py": "Main entry point",
        "agent/run.py": "Agent entry point",
    }

    def __init__(
        self,
        repo_root: Path,
        max_files: int = 500,
        max_bytes: int = 10_000_000,
    ):
        """Initialize repo scanner."""
        self.repo_root = repo_root.resolve()
        self.max_files = max_files
        self.max_bytes = max_bytes

    def _get_file_type(self, path: Path) -> str:
        """Determine file type from extension."""
        suffix = path.suffix.lower()

        for file_type, extensions in self.FILE_TYPES.items():
            if suffix in extensions:
                return file_type

        return "other"

    def _is_key_file(self, path: Path) -> Tuple[bool, Optional[str]]:
        """Check if file is a key file."""
        try:
            rel_path = path.relative_to(self.repo_root)
        except ValueError:
            rel_path = path

        # Check exact matches
        for pattern, reason in self.KEY_FILE_PATTERNS.items():
            if str(rel_path) == pattern or path.name == pattern:
                return True, reason

        # Check patterns
        if path.name in {"README.md", "setup.py", "requirements.txt", "Makefile"}:
            return True, f"Key file: {path.name}"

        if path.parent.name in {".github", "src", "agent"}:
            if path.suffix in {".py", ".md"}:
                return True, f"Key file in {path.parent.name}/"

        return False, None

    def scan(self) -> Tuple[RepoIndex, RepoMap]:
        """Scan repository and produce index and map."""
        logger.info(f"Scanning repository: {self.repo_root}")

        all_files: List[FileInfo] = []
        key_files: List[FileInfo] = []
        total_bytes = 0

        # Walk repository
        for path in self.repo_root.rglob("*"):
            if path.is_file():
                # Skip hidden files and common unimportant directories
                if any(part.startswith(".") for part in path.parts):
                    continue
                if any(part in {"__pycache__", "node_modules", ".git"} for part in path.parts):
                    continue

                # Check budget
                if len(all_files) >= self.max_files:
                    logger.warning(f"Reached max files limit: {self.max_files}")
                    break

                try:
                    size = path.stat().st_size
                    if total_bytes + size > self.max_bytes:
                        logger.warning(f"Reached max bytes limit: {self.max_bytes}")
                        break

                    total_bytes += size

                    # Create file info
                    file_type = self._get_file_type(path)
                    is_key, reason = self._is_key_file(path)

                    file_info = FileInfo(
                        path=str(path.relative_to(self.repo_root)),
                        size_bytes=size,
                        file_type=file_type,
                        is_key_file=is_key,
                        reason=reason,
                    )

                    all_files.append(file_info)

                    if is_key:
                        key_files.append(file_info)

                except Exception as exc:
                    logger.warning(f"Error scanning file {path}: {exc}")

        # Create index
        index = RepoIndex(
            root=str(self.repo_root),
            total_files=len(all_files),
            total_bytes=total_bytes,
            files=all_files,
        )

        # Create map
        structure_summary = self._create_structure_summary(all_files)
        map_obj = RepoMap(
            root=str(self.repo_root),
            key_files=key_files,
            structure_summary=structure_summary,
        )

        logger.info(
            f"Scan complete: {len(all_files)} files, {total_bytes / 1024 / 1024:.1f}MB, "
            f"{len(key_files)} key files"
        )

        return index, map_obj

    def _create_structure_summary(self, files: List[FileInfo]) -> str:
        """Create a summary of repository structure."""
        by_type: Dict[str, int] = {}
        for file_info in files:
            by_type[file_info.file_type] = by_type.get(file_info.file_type, 0) + 1

        summary_lines = [
            f"Repository: {self.repo_root.name}",
            f"Total files: {len(files)}",
            "File types:",
        ]

        for file_type, count in sorted(by_type.items()):
            summary_lines.append(f"  {file_type}: {count}")

        return "\n".join(summary_lines)

    def save_index(self, output_path: Path) -> None:
        """Save index to file."""
        index, _ = self.scan()
        output_path.write_text(json.dumps(asdict(index), indent=2))
        logger.info(f"Saved index to {output_path}")

    def save_map(self, output_path: Path) -> None:
        """Save map to file."""
        _, map_obj = self.scan()
        output_path.write_text(json.dumps(asdict(map_obj), indent=2))
        logger.info(f"Saved map to {output_path}")
