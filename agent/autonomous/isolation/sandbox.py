import logging
import shutil
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SandboxIsolation:
    def __init__(self, repo_root: Path, run_id: str):
        self.repo_root = repo_root.resolve()
        self.run_id = run_id
        self.sandboxes_dir = Path(f"runs/swarm/{run_id}")
        self.sandboxes_dir.mkdir(parents=True, exist_ok=True)
        self.created_sandboxes = []
    
    def create_sandbox(self, task_id: str) -> Path:
        sandbox_path = self.sandboxes_dir / task_id / "workspace"
        try:
            sandbox_path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(self.repo_root, sandbox_path, ignore=shutil.ignore_patterns(".git", ".worktrees", "runs", "__pycache__", "*.pyc"), dirs_exist_ok=True)
            self.created_sandboxes.append((task_id, sandbox_path))
            return sandbox_path
        except Exception as exc:
            raise RuntimeError(f"Sandbox creation failed: {exc}")
    
    def get_changes(self, task_id: str) -> Dict[str, str]:
        sandbox_path = self.sandboxes_dir / task_id / "workspace"
        changes = {}
        if not sandbox_path.exists():
            return changes
        try:
            for file_path in sandbox_path.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(sandbox_path)
                    orig_path = self.repo_root / rel_path
                    if not orig_path.exists():
                        changes[str(rel_path)] = "added"
                    else:
                        try:
                            if file_path.read_text() != orig_path.read_text():
                                changes[str(rel_path)] = "modified"
                        except:
                            pass
        except:
            pass
        return changes
    
    def apply_changes(self, task_id: str, target_dir: Optional[Path] = None) -> bool:
        if target_dir is None:
            target_dir = self.repo_root
        sandbox_path = self.sandboxes_dir / task_id / "workspace"
        if not sandbox_path.exists():
            return False
        try:
            for file_path in sandbox_path.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(sandbox_path)
                    target_path = target_dir / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, target_path)
            return True
        except:
            return False
    
    def cleanup_sandbox(self, task_id: str) -> bool:
        sandbox_dir = self.sandboxes_dir / task_id
        if not sandbox_dir.exists():
            return False
        try:
            shutil.rmtree(sandbox_dir)
            return True
        except:
            return False
    
    def cleanup_all(self) -> int:
        cleaned = 0
        for task_id, _ in self.created_sandboxes:
            if self.cleanup_sandbox(task_id):
                cleaned += 1
        self.created_sandboxes.clear()
        return cleaned
