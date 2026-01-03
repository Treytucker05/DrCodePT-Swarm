import json
from pathlib import Path
from agent.autonomous.vision_executor import VisionExecutor, ScreenState


def test_refine_coordinates_uses_bounding_box(tmp_path):
    # Create a dummy screenshot (blank image)
    from PIL import Image
    img_path = tmp_path / "screen.png"
    Image.new("RGB", (200, 100), color=(255, 255, 255)).save(img_path)

    # Stub LLM that returns a bounding box JSON when asked
    class StubLLM:
        provider_name = "stub"

        def chat_with_image(self, prompt, image_input, **kwargs):
            # Return a JSON object as text
            return json.dumps({
                "left": 20,
                "top": 10,
                "right": 60,
                "bottom": 50,
                "confidence": 0.92,
            })

    executor = VisionExecutor(llm=StubLLM())
    # Set current state to our dummy screenshot
    executor.current_state = ScreenState(img_path, "ts")

    x, y = 5.0, 5.0
    refined_x, refined_y = executor._refine_coordinates(x, y, confidence=0.4)

    # Bounding box center should be (40, 30)
    assert (int(refined_x), int(refined_y)) == (40, 30)


def test_ocr_caching(tmp_path):
    pytest = __import__("pytest")
    pytesseract = pytest.importorskip("pytesseract")
    from PIL import Image, ImageDraw, ImageFont

    img_path = tmp_path / "text.png"
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 80), "ClickMe", fill=(0, 0, 0))
    img.save(img_path)

    executor = VisionExecutor()
    executor.current_state = ScreenState(img_path, "ts2")

    coords = executor._find_text_with_ocr("ClickMe")
    assert coords is not None
    # Ensure cache populated
    assert str(img_path) in (executor._ocr_cache or {})
    # Re-running should hit cache and still find coords
    coords2 = executor._find_text_with_ocr("ClickMe")
    assert coords2 == coords


def test_prompt_requests_bbox_schema(tmp_path):
    # Prompt should include guidance to return a JSON bbox when uncertain
    executor = VisionExecutor()
    executor.current_state = ScreenState(tmp_path / "dummy.png", "ts")
    prompt = executor._build_vision_prompt("Click submit", "")
    assert "bbox" in prompt or '"left"' in prompt or "bounding box" in prompt


def test_request_bounding_box_handles_nested_bbox(tmp_path):
    # Create dummy screenshot
    from PIL import Image
    img_path = tmp_path / "screen2.png"
    Image.new("RGB", (200, 200), color=(255, 255, 255)).save(img_path)

    class StubLLM2:
        provider_name = "stub"

        def chat_with_image(self, prompt, image_input, **kwargs):
            return json.dumps({
                "bbox": {"left": 10, "top": 20, "right": 30, "bottom": 60},
                "confidence": 0.9,
            })

    executor = VisionExecutor(llm=StubLLM2())
    executor.current_state = ScreenState(img_path, "ts3")

    bbox = executor._request_bounding_box(1, 1, 0.3)
    assert bbox is not None
    assert int(bbox["left"]) == 10
    assert int(bbox["top"]) == 20
    assert int(bbox["right"]) == 30
    assert int(bbox["bottom"]) == 60

    # Ensure _refine_coordinates will compute center from nested bbox
    rx, ry = executor._refine_coordinates(1, 1, confidence=0.4)
    assert (int(rx), int(ry)) == ((10 + 30) // 2, (20 + 60) // 2)


def test_parse_response_with_bbox(tmp_path):
    from PIL import Image
    img_path = tmp_path / "screen3.png"
    Image.new("RGB", (300, 200), color=(255, 255, 255)).save(img_path)

    executor = VisionExecutor()
    executor.current_state = ScreenState(img_path, "ts4")

    # Model returns bbox but not target
    response = json.dumps({
        "observation": "I see a Submit button",
        "reasoning": "Button appears on the right side",
        "action": "click",
        "bbox": {"left": 200, "top": 50, "right": 260, "bottom": 90, "confidence": 0.85},
        "value": None,
        "confidence": 0.4,
    })

    parsed = executor._parse_vision_response(response, executor.current_state)
    assert parsed.get("action") == "click"
    target = parsed.get("target")
    assert target is not None
    assert int(target["x"]) == (200 + 260) // 2
    assert int(target["y"]) == (50 + 90) // 2
    # Confidence should be promoted from bbox
    assert float(parsed.get("confidence")) >= 0.85
