"""Tests for loop detection."""

import pytest
from agent.autonomous.loop_detection import LoopDetector


def test_loop_detection_ignores_changing_output():
    """Loop detection doesn't trigger if output changes."""
    detector = LoopDetector(max_repeats=3)

    # Same tool, different outputs
    is_loop, _ = detector.check("file_write", {"path": "a.txt"}, "file1.py")
    assert not is_loop

    is_loop, _ = detector.check("file_write", {"path": "a.txt"}, "file1.py\nfile2.py")
    assert not is_loop

    is_loop, _ = detector.check("file_write", {"path": "a.txt"}, "file1.py\nfile2.py\nfile3.py")
    assert not is_loop


def test_loop_detection_triggers_on_identical_output():
    """Loop detection triggers if output is identical."""
    detector = LoopDetector(max_repeats=3)

    # Same tool, same output 3 times
    is_loop, msg = detector.check("file_write", {"path": "a.txt"}, "file1.py")
    assert not is_loop

    is_loop, msg = detector.check("file_write", {"path": "a.txt"}, "file1.py")
    assert not is_loop

    is_loop, msg = detector.check("file_write", {"path": "a.txt"}, "file1.py")
    assert is_loop
    assert "Loop detected" in msg


def test_loop_detection_different_args_not_loop():
    """Different args don't trigger loop detection."""
    detector = LoopDetector(max_repeats=3)

    # Same tool, different args
    is_loop, _ = detector.check("file_write", {"path": "a.txt"}, "file1.py")
    assert not is_loop

    is_loop, _ = detector.check("file_write", {"path": "b.txt"}, "file1.py")
    assert not is_loop

    is_loop, _ = detector.check("file_write", {"path": "c.txt"}, "file1.py")
    assert not is_loop


def test_loop_detection_reset():
    """Test resetting loop detection."""
    detector = LoopDetector(max_repeats=2)

    # Create a loop
    detector.check("file_write", {"path": "a.txt"}, "output")
    detector.check("file_write", {"path": "a.txt"}, "output")
    is_loop, _ = detector.check("file_write", {"path": "a.txt"}, "output")
    assert is_loop

    # Reset
    detector.reset()

    # Should not be a loop anymore
    is_loop, _ = detector.check("file_write", {"path": "a.txt"}, "output")
    assert not is_loop
