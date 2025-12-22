import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ConflictDetector:
    def __init__(self):
        self.file_locks: Dict[str, str] = {}
    
    def acquire_lock(self, file_path: str, task_id: str) -> bool:
        if file_path in self.file_locks:
            return False
        self.file_locks[file_path] = task_id
        return True
    
    def release_lock(self, file_path: str, task_id: str) -> bool:
        if file_path not in self.file_locks or self.file_locks[file_path] != task_id:
            return False
        del self.file_locks[file_path]
        return True
    
    def detect_conflicts(self, changes: Dict[str, Dict[str, str]]) -> List[str]:
        conflicts = []
        for task_id, task_changes in changes.items():
            for file_path in task_changes.keys():
                for other_task_id, other_changes in changes.items():
                    if task_id != other_task_id and file_path in other_changes:
                        conflicts.append(f"Conflict: {file_path} modified by both {task_id} and {other_task_id}")
        return conflicts
    
    def get_locked_files(self) -> Dict[str, str]:
        return self.file_locks.copy()
    
    def clear_locks(self) -> int:
        count = len(self.file_locks)
        self.file_locks.clear()
        return count
