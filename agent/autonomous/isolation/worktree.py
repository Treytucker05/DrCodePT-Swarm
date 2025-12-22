"""Git worktree isolation for parallel task execution."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WorktreeIsolation:
    """Isolate tasks using git worktrees.

    Each task gets its own worktree on a separate branch, allowing
    parallel execution without conflicts.
    """

    def __init__(self, repo_root: Path, run_id: str):
        """Initialize worktree isolation.

        Args:
            repo_root: Root directory of git repository
            run_id: Unique run ID for this execution
        """
        self.repo_root = repo_root.resolve()
        self.run_id = run_id
        self.worktrees_dir = repo_root / ".worktrees"
        self.worktrees_dir.mkdir(exist_ok=True)
        self.created_worktrees = []
        logger.info(f"WorktreeIsolation initialized: {self.worktrees_dir}")

    def create_worktree(self, task_id: str) -> Path:
        """Create isolated worktree for task.

        Args:
            task_id: Unique task ID

        Returns:
            Path to worktree

        Raises:
            RuntimeError: If worktree creation fails
        """
        worktree_name = f"{self.run_id}_{task_id}"
        worktree_path = self.worktrees_dir / worktree_name
        branch_name = f"task/{self.run_id}/{task_id}"

        try:
            # Create new branch from main without switching HEAD
            subprocess.run(
                ["git", "branch", branch_name],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            logger.info(f"Created branch: {branch_name}")

            # Create worktree
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), branch_name],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            logger.info(f"Created worktree: {worktree_path}")

            self.created_worktrees.append((task_id, worktree_path, branch_name))
            return worktree_path

        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to create worktree: {exc}")
            raise RuntimeError(f"Worktree creation failed: {exc}")

    def cleanup_worktree(self, task_id: str) -> bool:
        """Clean up worktree after task.

        Args:
            task_id: Task ID

        Returns:
            True if cleaned up, False if not found
        """
        worktree_name = f"{self.run_id}_{task_id}"
        worktree_path = self.worktrees_dir / worktree_name
        branch_name = f"task/{self.run_id}/{task_id}"

        if not worktree_path.exists():
            logger.warning(f"Worktree not found: {worktree_path}")
            return False

        try:
            # Remove worktree
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path)],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            logger.info(f"Removed worktree: {worktree_path}")

            # Delete branch
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            logger.info(f"Deleted branch: {branch_name}")

            return True

        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to cleanup worktree: {exc}")
            return False

    def merge_changes(self, task_id: str, target_branch: str = "main") -> bool:
        """Merge task changes back to target branch.

        Args:
            task_id: Task ID
            target_branch: Target branch to merge into (default: main)

        Returns:
            True if merge successful, False if conflict or error
        """
        branch_name = f"task/{self.run_id}/{task_id}"

        try:
            # Checkout target branch
            subprocess.run(
                ["git", "checkout", target_branch],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            logger.info(f"Checked out: {target_branch}")

            # Merge task branch
            subprocess.run(
                ["git", "merge", branch_name, "--no-ff", "-m", f"Merge task {task_id}"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
            )
            logger.info(f"Merged {branch_name} into {target_branch}")
            return True

        except subprocess.CalledProcessError as exc:
            logger.error(f"Merge conflict or error for task {task_id}: {exc}")
            return False

    def cleanup_all(self) -> int:
        """Clean up all created worktrees.

        Returns:
            Number of worktrees cleaned up
        """
        cleaned = 0

        for task_id, _, _ in self.created_worktrees:
            if self.cleanup_worktree(task_id):
                cleaned += 1

        self.created_worktrees.clear()
        logger.info(f"Cleaned up {cleaned} worktrees")
        return cleaned

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.cleanup_all()
        except Exception as exc:
            logger.error(f"Error during cleanup: {exc}")
