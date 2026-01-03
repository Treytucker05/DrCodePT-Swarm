import json
from pathlib import Path
from agent.autonomous.vision_executor import VisionExecutor, ScreenState


def test_analyze_click_verify_flow_with_ocr_fallback(tmp_path):
    # Create initial screenshot (LLM will be wrong about position)
    from PIL import Image, ImageDraw

    init_path = tmp_path / "init.png"
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw the actual button text at the right place (true location) with a larger font for OCR
    true_x, true_y = 200, 60
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = None
    draw.text((true_x - 40, true_y - 18), "Submit", fill=(0, 0, 0), font=font)
    img.save(init_path)

    # Create post-click screenshot (after clicking) - still contains the button (simulating that click didn't work yet)
    post_path = tmp_path / "post.png"
    img2 = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw2 = ImageDraw.Draw(img2)
    draw2.text((true_x - 40, true_y - 18), "Submit", fill=(0, 0, 0), font=font)
    img2.save(post_path)

    # Stub LLM: returns an incorrect bbox (off to the left)
    class StubLLM:
        provider_name = "stub"

        def chat_with_image(self, prompt, image_input, **kwargs):
            # Return bbox that is incorrect (to left of true button)
            # Include quoted button name so executor can extract expected_text for OCR verification
            return json.dumps({
                "observation": "I see a \"Submit\" button",
                "reasoning": "Should click \"Submit\"",
                "action": "click",
                "bbox": {"left": 100, "top": 50, "right": 140, "bottom": 90, "confidence": 0.6},
                "confidence": 0.5,
            })

    # PyAutoGUI stub: succeed only for the true coords; otherwise, raise
    class StubPyAutoGui:
        def __init__(self):
            self.calls = []

        def click(self, x, y):
            self.calls.append((int(x), int(y)))
            # succeed if click is approximately at true button center (tolerance 20px)
            if abs(int(x) - true_x) <= 20 and abs(int(y) - true_y) <= 20:
                return True
            raise RuntimeError("Click failed")

    stub_gui = StubPyAutoGui()

    # Prepare executor with stub LLM and stub GUI
    executor = VisionExecutor(llm=StubLLM())
    executor.pyautogui = stub_gui
    # Use test-specific patterns path to avoid repo writes
    executor.patterns_path = tmp_path / "patterns.json"

    # Monkeypatch take_screenshot to return init_path first, then post_path on subsequent calls
    shots = [init_path, post_path]

    def fake_take_screenshot(name: str = "screen"):
        if not shots:
            raise RuntimeError("No more screenshots")
        p = shots.pop(0)
        ts = p.stem
        executor.current_state = ScreenState(p, ts)
        return executor.current_state

    executor.take_screenshot = fake_take_screenshot

    # Sanity check: ensure OCR can find the text in the initial screenshot
    executor.current_state = ScreenState(init_path, "init")
    coords_before = executor._find_text_with_ocr("Submit")
    assert coords_before is not None, "OCR couldn't find 'Submit' in initial screenshot (pre-check)"

    # Run analysis
    action = executor.analyze_screen("Click the Submit button")

    # Execute action: should ultimately succeed via OCR-based fallback
    ok, msg = executor.execute_action(action)
    if not ok:
        # Gather debugging info
        calls = stub_gui.calls
        ocr_now = executor._find_text_with_ocr("Submit")
        pytest = __import__("pytest")
        pytest.fail(f"Click did not succeed. msg={msg}, calls={calls}, ocr_now={ocr_now}")

    # Ensure OCR fallback was used: one of the calls should be within tolerance of true coords
    assert any(abs(x - true_x) <= 20 and abs(y - true_y) <= 20 for x, y in stub_gui.calls), f"No click near ({true_x},{true_y}); calls={stub_gui.calls}"

    # Ensure persistence saved pattern
    assert executor.patterns_path.exists()
    data = json.loads(executor.patterns_path.read_text(encoding="utf-8"))
    assert any(p.get("text", "").lower().find("submit") != -1 for p in data)
