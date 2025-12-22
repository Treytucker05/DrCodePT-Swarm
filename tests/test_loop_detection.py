from __future__ import annotations

from agent.autonomous.loop_detection import LoopDetector


def test_loop_detector_allows_changed_output() -> None:
    detector = LoopDetector(window=3, repeat_threshold=3)
    sig1 = "file_search:{\"q\":\"x\"}:hash1"
    sig2 = "file_search:{\"q\":\"x\"}:hash2"
    assert detector.update(sig1, "state") is False
    assert detector.update(sig2, "state") is False
    assert detector.update(sig1, "state") is False
    assert detector.update(sig1, "state") is False
    assert detector.update(sig1, "state") is True
