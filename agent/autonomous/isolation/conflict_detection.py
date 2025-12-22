"""Conflict detection for parallel task execution."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Detect conflicts between parallel tasks.

    Tracks file locks and detects when multiple tasks try to
    modify the same files.
    """

    def __init__(self):
        """Initialize conflict detector."""
        self.file_locks: Dict[str, str] = {}  # file_path -> task_id
        logger.info("ConflictDetector initialized")

    def acquire_lock(self, file_path: str, task_id: str) -> bool:
        """Try to acquire lock on file.

        Args:
            file_path: Path to file
            task_id: Task ID requesting lock

        Returns:
            True if lock acquired, False if already locked
        """
        if file_path in self.file_locks:
            logger.warning(
                f"File {file_path} already locked by {self.file_locks[file_path]}, "
                f"cannot acquire for {task_id}"
            )
            return False

        self.file_locks[file_path] = task_id
        logger.debug(f"Acquired lock on {file_path} for {task_id}")
        return True

    def release_lock(self, file_path: str, task_id: str) -> bool:
        """Release lock on file.

        Args:
            file_path: Path to file
            task_id: Task ID releasing lock

        Returns:
            True if released, False if not locked by this task
        """
        if file_path not in self.file_locks:
            logger.warning(f"File {file_path} not locked")
            return False

        if self.file_locks[file_path] != task_id:
            logger.warning(
                f"File {file_path} locked by {self.file_locks[file_path]}, "
                f"not by {task_id}"
            )
            return False

        del self.file_locks[file_path]
        logger.debug(f"Released lock on {file_path} from {task_id}")
        return True

    def detect_conflicts(self, changes: Dict[str, Dict[str, str]]) -> List[str]:
        """Detect conflicts between task changes.

        Args:
            changes: Dict mapping task_id -> {file_path -> change_type}

        Returns:
            List of conflict messages
        """
        conflicts = []

        for task_id, task_changes in changes.items():
            for file_path in task_changes.keys():
                for other_task_id, other_changes in changes.items():
                    if task_id != other_task_id and file_path in other_changes:
                        conflict_msg = (
                            f"Conflict: {file_path} modified by both "
                            f"{task_id} and {other_task_id}"
                        )
                        conflicts.append(conflict_msg)
                        logger.error(conflict_msg)

        return conflicts

    def get_locked_files(self) -> Dict[str, str]:
        """Get all currently locked files.

        Returns:
            Dict mapping file_path -> task_id
        """
        return self.file_locks.copy()

    def clear_locks(self) -> int:
        """Clear all locks.

        Returns:
            Number of locks cleared
        """
        count = len(self.file_locks)
        self.file_locks.clear()
        logger.info(f"Cleared {count} locks")
        return count
