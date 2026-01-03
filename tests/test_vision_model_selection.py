from pathlib import Path
from agent.autonomous.vision_executor import VisionExecutor, ScreenState


class StubLLM:
    provider_name = "openai"

    def __init__(self):
        self.last_kwargs = {}
        self.last_prompt = None

    def chat_with_image(self, prompt, image_input, **kwargs):
        self.last_prompt = prompt
        self.last_kwargs = kwargs
        return "{}"


def test_selects_preferred_openai_model(tmp_path):
    # Create dummy screenshot
    from PIL import Image
    img_path = tmp_path / "screen.png"
    Image.new("RGB", (200, 200), color=(255, 255, 255)).save(img_path)

    stub = StubLLM()
    executor = VisionExecutor(llm=stub)
    executor.current_state = ScreenState(img_path, "ts")

    # Call the internal method
    executor._call_vision_llm("prompt", executor.current_state)

    # Expect preferred model to be the first in MODEL_PREFERRED for openai
    assert stub.last_kwargs.get("model") is not None
    assert "gpt-4" in stub.last_kwargs.get("model") or "vision" in stub.last_kwargs.get("model")
    # Ensure hint added to prompt
    assert "Be concise" in stub.last_prompt


def test_temperature_low_for_coordinates_and_higher_for_reasoning(tmp_path):
    from PIL import Image
    img_path = tmp_path / "screen2.png"
    Image.new("RGB", (200, 200), color=(255, 255, 255)).save(img_path)

    stub = StubLLM()
    executor = VisionExecutor(llm=stub)
    executor.current_state = ScreenState(img_path, "ts2")

    # Default (not use_reasoning) should be low temp
    executor.use_reasoning = False
    executor._call_vision_llm("prompt", executor.current_state)
    temp1 = stub.last_kwargs.get("temperature")

    # When use_reasoning True, temperature should be slightly higher
    executor.use_reasoning = True
    executor._call_vision_llm("prompt", executor.current_state)
    temp2 = stub.last_kwargs.get("temperature")

    assert temp1 is not None and temp2 is not None
    assert float(temp1) < float(temp2)
