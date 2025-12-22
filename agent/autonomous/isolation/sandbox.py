"""Sandbox copy isolation for parallel task execution."""

import logging
import shutil
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SandboxIsolation:
    """Isolate tasks using sandbox copies.

    Each task gets a complete copy of the repository, allowing
    parallel execution without conflicts. Simpler than worktrees
    but uses more disk space.
    """

    def __init__(self, repo_root: Path, run_id: str):
        """Initialize sandbox isolation.

        Args:
            repo_root: Root directory of repository
            run_id: Unique run ID for this execution
        """
        self.repo_root = repo_root.resolve()
        self.run_id = run_id
        self.sandboxes_dir = Path(f"runs/swarm/{run_id}")
        self.sandboxes_dir.mkdir(parents=True, exist_ok=True)
        self.created_sandboxes = []
        logger.info(f"SandboxIsolation initialized: {self.sandboxes_dir}")

    def create_sandbox(self, task_id: str) -> Path:
        """Create isolated sandbox copy for task.

        Args:
            task_id: Unique task ID

        Returns:
            Path to sandbox workspace

        Raises:
            RuntimeError: If sandbox creation fails
        """
        sandbox_path = self.sandboxes_dir / task_id / "workspace"

        try:
            sandbox_path.mkdir(parents=True, exist_ok=True)

            # Copy repo to sandbox
            shutil.copytree(
                self.repo_root,
                sandbox_path,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".worktrees",
                    "runs",
                    "__pycache__",
                    "*.pyc",
                    ".pytest_cache",
                ),
                dirs_exist_ok=True,
            )

            logger.info(f"Created sandbox: {sandbox_path}")
            self.created_sandboxes.append((task_id, sandbox_path))
            return sandbox_path

        except Exception as exc:
            logger.error(f"Failed to create sandbox: {exc}")
            raise RuntimeError(f"Sandbox creation failed: {exc}")

    def get_changes(self, task_id: str) -> Dict[str, str]:
        """Get file changes from sandbox.

        Args:
            task_id: Task ID

        Returns:
            Dict mapping file_path -> change_type (added, modified)
        """
        sandbox_path = self.sandboxes_dir / task_id / "workspace"
        changes = {}

        if not sandbox_path.exists():
            logger.warning(f"Sandbox not found: {sandbox_path}")
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
                        except (UnicodeDecodeError, IsADirectoryError):
                            # Binary file or directory, skip
                            pass

        except Exception as exc:
            logger.error(f"Error detecting changes: {exc}")

        return changes

    def apply_changes(self, task_id: str, target_dir: Optional[Path] = None) -> bool:
        """Apply sandbox changes to target directory.

        Args:
            task_id: Task ID
            target_dir: Target directory (default: repo_root)

        Returns:
            True if successful, False if error
        """
        if target_dir is None:
            target_dir = self.repo_root

        sandbox_path = self.sandboxes_dir / task_id / "workspace"

        if not sandbox_path.exists():
            logger.warning(f"Sandbox not found: {sandbox_path}")
            return False

        try:
            for file_path in sandbox_path.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(sandbox_path)
                    target_path = target_dir / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, target_path)

            logger.info(f"Applied changes from sandbox {task_id}")
            return True

        except Exception as exc:
            logger.error(f"Error applying changes: {exc}")
            return False

    def cleanup_sandbox(self, task_id: str) -> bool:
        """Clean up sandbox after task.

        Args:
            task_id: Task ID

        Returns:
            True if cleaned up, False if not found
        """
        sandbox_dir = self.sandboxes_dir / task_id

        if not sandbox_dir.exists():
            logger.warning(f"Sandbox not found: {sandbox_dir}")
            return False

        try:
            shutil.rmtree(sandbox_dir)
            logger.info(f"Cleaned up sandbox: {sandbox_dir}")
            return True

        except Exception as exc:
            logger.error(f"Error cleaning up sandbox: {exc}")
            return False

    def cleanup_all(self) -> int:
        """Clean up all created sandboxes.

        Returns:
            Number of sandboxes cleaned up
        """
        cleaned = 0

        for task_id, _ in self.created_sandboxes:
            if self.cleanup_sandbox(task_id):
                cleaned += 1

        self.created_sandboxes.clear()
        logger.info(f"Cleaned up {cleaned} sandboxes")
        return cleaned

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.cleanup_all()
        except Exception as exc:
            logger.error(f"Error during cleanup: {exc}")
