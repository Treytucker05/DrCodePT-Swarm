"""Tests for loop detection."""

import pytest
from agent.autonomous.loop_detection import LoopDetector


def test_loop_detection_ignores_changing_output():
    """Loop detection doesn't trigger if output changes."""
    detector = LoopDetector(max_repeats=3)

    # Same tool, different outputs
    is_loop, _ = detector.check("glob_paths", {"pattern": "*.py"}, "file1.py")
    assert not is_loop

    is_loop, _ = detector.check("glob_paths", {"pattern": "*.py"}, "file1.py\nfile2.py")
    assert not is_loop

    is_loop, _ = detector.check("glob_paths", {"pattern": "*.py"}, "file1.py\nfile2.py\nfile3.py")
    assert not is_loop


def test_loop_detection_triggers_on_identical_output():
    """Loop detection triggers if output is identical."""
    detector = LoopDetector(max_repeats=3)

    # Same tool, same output 3 times
    is_loop, msg = detector.check("glob_paths", {"pattern": "*.py"}, "file1.py")
    assert not is_loop

    is_loop, msg = detector.check("glob_paths", {"pattern": "*.py"}, "file1.py")
    assert not is_loop

    is_loop, msg = detector.check("glob_paths", {"pattern": "*.py"}, "file1.py")
    assert is_loop
    assert "Loop detected" in msg


def test_loop_detection_different_args_not_loop():
    """Different args don't trigger loop detection."""
    detector = LoopDetector(max_repeats=3)

    # Same tool, different args
    is_loop, _ = detector.check("glob_paths", {"pattern": "*.py"}, "file1.py")
    assert not is_loop

    is_loop, _ = detector.check("glob_paths", {"pattern": "*.txt"}, "file1.py")
    assert not is_loop

    is_loop, _ = detector.check("glob_paths", {"pattern": "*.md"}, "file1.py")
    assert not is_loop


def test_loop_detection_reset():
    """Test resetting loop detection."""
    detector = LoopDetector(max_repeats=2)

    # Create a loop
    detector.check("tool", {}, "output")
    detector.check("tool", {}, "output")
    is_loop, _ = detector.check("tool", {}, "output")
    assert is_loop

    # Reset
    detector.reset()

    # Should not be a loop anymore
    is_loop, _ = detector.check("tool", {}, "output")
    assert not is_loop
