"""Repository scanning utilities."""
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    path: str
    size_bytes: int
    file_type: str
    is_key_file: bool = False
    reason: Optional[str] = None

@dataclass
class RepoIndex:
    root: str
    total_files: int
    total_bytes: int
    files: List[FileInfo]

@dataclass
class RepoMap:
    root: str
    key_files: List[FileInfo]
    structure_summary: str

class RepoScanner:
    FILE_TYPES = {"python": {".py"}, "markdown": {".md", ".rst", ".txt"}, "config": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}, "code": {".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".h"}}
    KEY_FILE_PATTERNS = {"README.md": "Project overview", "setup.py": "Python package setup", "pyproject.toml": "Python project config", "requirements.txt": "Python dependencies", "Makefile": "Build instructions"}
    
    def __init__(self, repo_root: Path, max_files: int = 500, max_bytes: int = 10_000_000):
        self.repo_root = repo_root.resolve()
        self.max_files = max_files
        self.max_bytes = max_bytes
    
    def _get_file_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        for file_type, extensions in self.FILE_TYPES.items():
            if suffix in extensions:
                return file_type
        return "other"
    
    def _is_key_file(self, path: Path) -> Tuple[bool, Optional[str]]:
        if not path.is_absolute():
            path = self.repo_root / path
        rel_path = path.relative_to(self.repo_root)
        for pattern, reason in self.KEY_FILE_PATTERNS.items():
            if str(rel_path) == pattern or path.name == pattern:
                return True, reason
        return False, None
    
    def scan(self) -> Tuple[RepoIndex, RepoMap]:
        all_files = []
        key_files = []
        total_bytes = 0
        
        for path in self.repo_root.rglob("*"):
            if path.is_file() and len(all_files) < self.max_files:
                if any(part.startswith(".") for part in path.parts):
                    continue
                try:
                    size = path.stat().st_size
                    if total_bytes + size > self.max_bytes:
                        break
                    total_bytes += size
                    file_type = self._get_file_type(path)
                    is_key, reason = self._is_key_file(path)
                    file_info = FileInfo(str(path.relative_to(self.repo_root)), size, file_type, is_key, reason)
                    all_files.append(file_info)
                    if is_key:
                        key_files.append(file_info)
                except:
                    pass
        
        index = RepoIndex(str(self.repo_root), len(all_files), total_bytes, all_files)
        map_obj = RepoMap(str(self.repo_root), key_files, f"Repository: {self.repo_root.name}\nTotal files: {len(all_files)}")
        return index, map_obj
