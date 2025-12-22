from __future__ import annotations

from agent.autonomous.loop_detection import LoopDetector


def test_loop_detector_ignores_changing_output() -> None:
    detector = LoopDetector(window=5, repeat_threshold=3)
    assert detector.update("file_search", "args", "out1") is False
    assert detector.update("file_search", "args", "out2") is False
    assert detector.update("file_search", "args", "out1") is False
    assert detector.update("file_search", "args", "out2") is False


def test_loop_detector_triggers_on_identical_output() -> None:
    detector = LoopDetector(window=4, repeat_threshold=3)
    assert detector.update("file_search", "args", "out") is False
    assert detector.update("file_search", "args", "out") is False
    assert detector.update("file_search", "args", "out") is True


def test_loop_detector_separates_args() -> None:
    detector = LoopDetector(window=4, repeat_threshold=2)
    assert detector.update("file_search", "args1", "out") is False
    assert detector.update("file_search", "args2", "out") is False
    assert detector.update("file_search", "args2", "out") is True
