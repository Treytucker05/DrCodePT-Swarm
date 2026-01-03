import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class WorktreeIsolation:
    def __init__(self, repo_root: Path, run_id: str):
        self.repo_root = repo_root.resolve()
        self.run_id = run_id
        self.worktrees_dir = repo_root / ".worktrees"
        self.worktrees_dir.mkdir(exist_ok=True)
        self.created_worktrees = []
    
    def create_worktree(self, task_id: str) -> Path:
        worktree_name = f"{self.run_id}_{task_id}"
        worktree_path = self.worktrees_dir / worktree_name
        branch_name = f"task/{self.run_id}/{task_id}"
        try:
            subprocess.run(["git", "branch", branch_name], cwd=self.repo_root, check=True, capture_output=True)
            subprocess.run(["git", "worktree", "add", str(worktree_path), branch_name], cwd=self.repo_root, check=True, capture_output=True)
            self.created_worktrees.append((task_id, worktree_path, branch_name))
            return worktree_path
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Worktree creation failed: {exc}")
    
    def cleanup_worktree(self, task_id: str) -> bool:
        worktree_name = f"{self.run_id}_{task_id}"
        worktree_path = self.worktrees_dir / worktree_name
        branch_name = f"task/{self.run_id}/{task_id}"
        if not worktree_path.exists():
            return False
        try:
            subprocess.run(["git", "worktree", "remove", str(worktree_path)], cwd=self.repo_root, check=True, capture_output=True)
            subprocess.run(["git", "branch", "-D", branch_name], cwd=self.repo_root, check=True, capture_output=True)
            return True
        except:
            return False
    
    def cleanup_all(self) -> int:
        cleaned = 0
        for task_id, _, _ in self.created_worktrees:
            if self.cleanup_worktree(task_id):
                cleaned += 1
        self.created_worktrees.clear()
        return cleaned
