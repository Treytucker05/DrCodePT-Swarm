import json
from pathlib import Path
from agent.autonomous.vision_executor import VisionExecutor, ScreenState


class StubPyAutoGuiFailThenSucceed:
    def __init__(self, succeed_at):
        # succeed_at is (x,y) tuple
        self.succeed_at = succeed_at
        self.calls = []

    def click(self, x, y):
        self.calls.append((int(x), int(y)))
        if (int(x), int(y)) == (int(self.succeed_at[0]), int(self.succeed_at[1])):
            return True
        raise RuntimeError("Click failed")


def test_try_nearby_coordinates_respects_budget_and_succeeds(tmp_path):
    # Create a dummy screenshot
    from PIL import Image
    img_path = tmp_path / "screen.png"
    Image.new("RGB", (200, 100), color=(255, 255, 255)).save(img_path)

    executor = VisionExecutor()
    executor.current_state = ScreenState(img_path, "ts")

    # Set small retry budget and custom offsets prioritizing one spot
    executor.retry_budget = 4
    executor.retry_offsets = [(1, 0), (0, 1), (2, 0), (0, 2)]

    # The stub will succeed only at offset (2,0) (so at x+2,y)
    stub = StubPyAutoGuiFailThenSucceed(succeed_at=(7, 5))
    executor.pyautogui = stub

    # Call nearby where original was (5,5)
    ok, msg = executor._try_nearby_coordinates(5, 5, expected_text=None, error="initial fail")
    assert ok
    assert "nearby coordinates" in msg
    # Confirm that final successful click was recorded
    assert (7, 5) in stub.calls


def test_persistence_of_successful_patterns(tmp_path):
    executor = VisionExecutor()
    executor.patterns_path = tmp_path / "patterns.json"

    executor.successful_patterns = [
        {"text": "SaveMe", "coords": (10, 20), "confidence": 0.9, "timestamp": "ts"}
    ]
    executor._save_successful_patterns()

    # New executor should load the persisted patterns
    new_exec = VisionExecutor()
    new_exec.patterns_path = executor.patterns_path
    new_exec._load_successful_patterns()

    assert any(p.get("text") == "SaveMe" for p in new_exec.successful_patterns)
