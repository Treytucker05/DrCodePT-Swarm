"""Tests for conflict detection."""

import pytest
from agent.autonomous.isolation.conflict_detection import ConflictDetector


def test_conflict_detector_initialization():
    """Test ConflictDetector initialization."""
    detector = ConflictDetector()
    assert len(detector.get_locked_files()) == 0


def test_acquire_lock():
    """Test acquiring a lock."""
    detector = ConflictDetector()

    result = detector.acquire_lock("file.py", "task_1")
    assert result is True

    locks = detector.get_locked_files()
    assert locks["file.py"] == "task_1"


def test_acquire_lock_already_locked():
    """Test acquiring a lock on already locked file."""
    detector = ConflictDetector()

    # First task locks file
    detector.acquire_lock("file.py", "task_1")

    # Second task tries to lock same file
    result = detector.acquire_lock("file.py", "task_2")
    assert result is False


def test_release_lock():
    """Test releasing a lock."""
    detector = ConflictDetector()

    # Acquire lock
    detector.acquire_lock("file.py", "task_1")

    # Release lock
    result = detector.release_lock("file.py", "task_1")
    assert result is True

    # Verify lock is gone
    locks = detector.get_locked_files()
    assert "file.py" not in locks


def test_release_lock_wrong_task():
    """Test releasing a lock held by different task."""
    detector = ConflictDetector()

    # Task 1 locks file
    detector.acquire_lock("file.py", "task_1")

    # Task 2 tries to release
    result = detector.release_lock("file.py", "task_2")
    assert result is False


def test_detect_conflicts():
    """Test detecting conflicts between tasks."""
    detector = ConflictDetector()

    changes = {
        "task_1": {"file1.py": "modified", "file2.py": "added"},
        "task_2": {"file1.py": "modified", "file3.py": "added"},
    }

    conflicts = detector.detect_conflicts(changes)

    assert len(conflicts) > 0
    assert any("file1.py" in c for c in conflicts)


def test_detect_no_conflicts():
    """Test when there are no conflicts."""
    detector = ConflictDetector()

    changes = {
        "task_1": {"file1.py": "modified"},
        "task_2": {"file2.py": "modified"},
    }

    conflicts = detector.detect_conflicts(changes)
    assert len(conflicts) == 0


def test_clear_locks():
    """Test clearing all locks."""
    detector = ConflictDetector()

    # Acquire multiple locks
    detector.acquire_lock("file1.py", "task_1")
    detector.acquire_lock("file2.py", "task_2")
    detector.acquire_lock("file3.py", "task_3")

    # Clear all
    cleared = detector.clear_locks()
    assert cleared == 3

    # Verify all cleared
    locks = detector.get_locked_files()
    assert len(locks) == 0
